#!/bin/bash

# build and run Dockerfile with a local data directory.
TAG=dockmann/web-tool:latest

# build and run the container
docker run -it --rm -p 8532:8532 --name web-tool ${TAG} $@
