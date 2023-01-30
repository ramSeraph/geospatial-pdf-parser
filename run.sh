#!/bin/bash

PLATFORM=${PLATFORM:-"linux/amd64"}

if [ "$BUILD" == "1" ]; then
	docker build --platform $PLATFORM -f Dockerfile -t geospatial-pdf .
fi

DOCKER_CMD="docker run --platform $PLATFORM --rm  -v $PWD:/code -w /code/ -it --name geospatial-pdf-run geospatial-pdf" 

if [ "$SETUP" == "1" ]; then
    $DOCKER_CMD python -m venv /code/.venv
    $DOCKER_CMD pip install --upgrade pip
    #$DOCKER_CMD pip install -r requirements.txt
fi

$DOCKER_CMD "${@}"
