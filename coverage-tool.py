#!/usr/bin/env python3

# MIT License
#
# (C) Copyright [2022] Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

import logging
import os
import yaml
import regex
import json
import re
import sys

from urllib.parse import urlparse
import copy

OPEN_API_FILE = "example_data/swagger_v2.yaml"
TAVERN_FILE_DIR = "example_data/functional"
TAVERN_FILES = []
TAVERN_REGEX = "test_.*.tavern.yaml"
API_TARGET_URLS = []  # ["{hsm_base_url}"]  # use this to specify variables you care about! This is the literal variable IN the tavern file


def CreateJobSummaryTemplateValues(report):
    template_values = {}
    template_values["endpoints"] = []

    for row in report:
        template_values["endpoints"].append({"url": row[0], "method": row[1], "count": row[2]})
    template_values["endpoints"].sort(key=lambda e: (e["url"], e["method"]))

    return template_values


class SafeLoaderIgnoreUnknown(yaml.SafeLoader):
    def ignore_unknown(self, node):
        return None


if __name__ == '__main__':

    ####################
    # Load Configuration
    ####################
    log_level = logging.INFO
    logging.basicConfig(level=log_level)

    if "OPEN_API_FILE" not in os.environ:
        logging.fatal("OPEN_API_FILE  is not set")
        sys.exit(1)
    else:
        OPEN_API_FILE = os.getenv("OPEN_API_FILE", None)
        logging.info("OPEN_API_FILE: " + str(OPEN_API_FILE))

    if "TAVERN_FILE_DIR" not in os.environ:
        logging.fatal("TAVERN_FILE_DIR  is not set")
        sys.exit(1)
    else:
        TAVERN_FILE_DIR = os.getenv("TAVERN_FILE_DIR", None)
        logging.info("TAVERN_FILE_DIR: " + str(TAVERN_FILE_DIR))

    if "API_TARGET_URLS" not in os.environ:
        logging.fatal("API_TARGET_URLS  is not set")
        sys.exit(1)
    else:
        RAW_API_TARGET_URLS = os.getenv("API_TARGET_URLS", None)
        API_TARGET_URLS = copy.deepcopy(RAW_API_TARGET_URLS.split(","))
        logging.info("API_TARGET_URLS: " + str(API_TARGET_URLS))

    SafeLoaderIgnoreUnknown.add_constructor(None, SafeLoaderIgnoreUnknown.ignore_unknown)

    # parse all the tavern test files

    test_cases = []
    if os.path.exists(TAVERN_FILE_DIR) == False:
        logging.error(TAVERN_FILE_DIR, " not found")
        sys.exit(1)

    for file in os.listdir(TAVERN_FILE_DIR):
        file_path = os.path.join(TAVERN_FILE_DIR, file)
        if os.path.isfile(file_path):
            if regex.search(TAVERN_REGEX, file) is not None:

                with open(file_path) as stream:
                    # Im not using safe load, because I have a custom constructor to turn all unknown tags into Nones
                    tavern_docs = yaml.load_all(stream, Loader=SafeLoaderIgnoreUnknown)
                    for doc in tavern_docs:
                        test = doc["test_name"]

                        for stage in doc["stages"]:
                            test_data = {}
                            test_data["file"] = file
                            test_data["test_name"] = test
                            test_stage = test + " - " + stage["name"]
                            test_data["stage"] = stage["name"]
                            test_data["request_url"] = stage["request"]["url"]
                            test_data["request_method"] = stage["request"]["method"].upper()
                            test_cases.append(test_data)

    # parse the swagger doc
    api_methods = []
    if os.path.exists(OPEN_API_FILE) == False:
        logging.error(OPEN_API_FILE, " not found")
        sys.exit(1)

    with open(OPEN_API_FILE) as stream:
        try:
            swagger = yaml.safe_load(stream)
            for path in swagger["paths"]:
                for method in swagger["paths"][path]:
                    endpoint = {}
                    endpoint["method"] = method.upper()
                    endpoint["url"] = path
                    api_methods.append(endpoint)
        except yaml.YAMLError as exc:
            logging.error(exc)
            sys.exit(1)

    # filter out any urls that dont have the expected URL string in them.
    filtered_test_cases = []
    for test_case in test_cases:
        for urls in API_TARGET_URLS:
            if urls in test_case["request_url"]:
                filtered_test_cases.append(test_case)

    # request_url = "{hsm_base_url}/hsm/v2/State/Components/{xname}" VS  url "/State/Components/{xname}"
    # -> There is no guarantee that the variable is the same.  I think I want to convert all {.*} into a magic string like: {VARIABLE}
    # But need to do this AFTER the base url filtering...

    for test_case in filtered_test_cases:
        test_case["request_url"] = regex.sub(r'\{(.*?)\}', "{VARIABLE}", test_case["request_url"])

    for endpoint in api_methods:
        endpoint["url"] = regex.sub(r'\{(.*?)\}', "{VARIABLE}", endpoint["url"])

    endpoints = {}

    for ep in api_methods:
        if ep["url"] in endpoints:
            if ep["method"] not in endpoints[ep["url"]]:
                endpoints[ep["url"]].setdefault(ep["method"], [])

        else:
            method = {}
            method[ep["method"]] = []
            endpoints.setdefault(ep["url"], method)

    new_endpoints = copy.deepcopy(endpoints)
    for test_case in filtered_test_cases:
        parsed_url = urlparse(test_case["request_url"])
        method = test_case["request_method"]
        for endpoint, verb in endpoints.items():
            sub_endpoint = re.sub("{VARIABLE}", "[{}a-zA-Z0-9_]*", endpoint)
            sub_endpoint = sub_endpoint + "$"
            if re.search(sub_endpoint, parsed_url.path) is not None and method in verb:
                nd = endpoints[endpoint]
                nd[method].append(test_case)
                new_endpoints[endpoint] = nd

    final_endpoints = {}
    for endpoint, verb in new_endpoints.items():
        data = {}
        data["methods"] = verb
        data["counts"] = {}

        for method, test_case_list in verb.items():
            data["counts"][method] = len(test_case_list)
        final_endpoints[endpoint] = data

    # create a final report
    # flatten this into a list of tuples

    report = []
    for url, data in final_endpoints.items():
        for method, count in data["counts"].items():
            report.append((url, method, count))


    if not os.path.exists("data/output"):
        os.makedirs("data/output")

    logging.info("Generating job summary template values")
    template_values = CreateJobSummaryTemplateValues(report)
    with open("data/output/job_summary_template_values.yaml", "w") as f:
        yaml.dump(template_values, f)

    logging.info(json.dumps(final_endpoints, indent=2))
