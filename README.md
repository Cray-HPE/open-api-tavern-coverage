# Open API Tavern Coverage Tool

## Overview

This tool is a coverage tool that can be used to determine how well an Open API spec is covered by Tavern tests.
It works by inspecting an OpenAPI spec (yaml file), building a map of the paths, verbs, then interrogating tavern test
 files (also yaml) and comparing tests and stages with references that are contained in the OpenAPI Specification.

The philosophy of use is to be deployed as part of a github action. The github action would use the existing source code,
with provided pointers to the tavern test files (commonly named in the pattern of: `test_*.tavern.yaml`) and the OpenAPI
specification (commonly named: `swagger.yaml`). The output format supports json, yaml, and csv. (TODO)

TODO need to better describe how the workflow works!

Some resources:

[Open API Specification](https://spec.openapis.org/oas/v3.1.0)
[Tavern API Tests](https://tavern.readthedocs.io/en/latest/)