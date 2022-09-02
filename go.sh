#!/bin/bash

#docker run -i -t --entrypoint bash -e TAVERN_FILE_DIR=example_data/functional -e OPEN_API_FILE=example_data/swagger_v2.yaml -e API_TARGET_URLS="{hsm_base_url}" --mount src=$(pwd),target=/src/app,type=bind open-api-tavern-coverage:0.1.0
docker run -i -t -e TAVERN_FILE_DIR=example_data/functional -e OPEN_API_FILE=example_data/swagger_v2.yaml -e API_TARGET_URLS="{hsm_base_url}" --mount src=$(pwd),target=/src/app,type=bind open-api-tavern-coverage:0.1.0

