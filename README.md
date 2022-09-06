# Open API Tavern Coverage Tool

## Overview

This tool is a coverage tool that can be used to determine how well an Open API spec is covered by Tavern tests.
It works by inspecting an OpenAPI spec (yaml file), building a map of the paths, verbs, then interrogating tavern test
 files (also yaml) and comparing tests and stages with references that are contained in the OpenAPI Specification.

The philosophy of use is to be deployed as part of a github action. The github action would use the existing source code,
with provided pointers to the tavern test files (commonly named in the pattern of: `test_*.tavern.yaml`) and the OpenAPI
specification (commonly named: `swagger.yaml`). The output of the job will be parsed via a template `open-api-tavern-coverage.md.tpl` (which must be in every caller repo).

The job logs will also contain a full JSON mapping of api endpoint, verb, and test cases.


Some resources:

[Open API Specification](https://spec.openapis.org/oas/v3.1.0)
[Tavern API Tests](https://tavern.readthedocs.io/en/latest/)

## Getting started:

You will need:

* the location of you swagger.yaml or openapi.yaml file
* the location of your tavern files, MUST be named `test_*.tavern.yaml`
* the `run_open-api-tavern-coverage.yaml` file into your `.github/workflows` directory
* the `open-api-tavern-coverage.yaml` into your `.github` directory

## Example consumer workflow file

`run_open-api-tavern-coverage.yaml`

```yaml
name: Run Open-API Tavern Coverage
on:
  - push # Perform a build of the contents from the branch
  - pull_request # Perform a build after merging with the target branch
  - workflow_dispatch
jobs:
  build_and_release:
    uses: Cray-HPE/open-api-tavern-coverage/.github/workflows/run_open-api-tavern-coverage.yaml@v1
    with:
      open-api-file: "api/docs/swagger.yaml"
      tavern-file-dir: "test/ct/functional"
      api-target-urls: "{fas_base_url}"

```

### General flow:

1. Checkout
2. Run the tool
3. Render the template
4. Generate the summary
