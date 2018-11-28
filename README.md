# Image Fetcher
This repository contains some usefull examples:
  * simple falsk application that works with AWS Dynamodb and S3 services
  * troposphere blueprint/stacker configs for AWS infrastructure as code

## Starting test environments
### Starting local dev environment

Create virtual environment

    python -m venv flask
    source flask/bin/activate

Install dependencies

    pip install -r requirements.txt
    pip install docker-compose

Start S3 and Dynamodb local servers, create bucket for images

    docker-compose up -d dynamodb s3server aws-cli

Set environment variables

    export APP_SETTINGS="config.dev"
    export AWS_ACCESS_KEY="accessKey1"
    export AWS_SECRET_KEY="verySecretKey1"
    export AWS_REGION="eu-central-1"
    export S3_BUCKET="images"

Start application

    python ./app.py

### Starting local test environment

Install docker-compose

    pip install docker-compose

Start service

    docker-compose up -d

## Starting production environment
### Creating AWS infrastructure

Create virtual environment

    python -m venv stacker
    source stacker/bin/activate

Install dependencies

    cd stacker
    pip install -r requirements.txt
    stacker build envs/production.yaml stacks/imageFetcher.yaml --recreate-failed


## Testing application
### Request image uploading

    curl -X POST "localhost:5000/api/v1/images" -H 'Content-Type: application/json' -d'
    {
        "name": "Docker logo",
        "url" : "https://www.docker.com/sites/default/files/Whale%20Logo332_5.png"
    }
    '

### Request a single image

    curl -X GET "localhost:5000/api/v1/images/name/test1"

### List all images

    curl -X GET "localhost:5000/api/v1/images"

### Check S3 bucket

    aws s3api list-objects --endpoint-url=http://localhost:8008 --bucket images


## Documents
  * https://flask-restful.readthedocs.io/en/latest/
  * https://github.com/scality/cloudserver/blob/master/docs/GETTING_STARTED.rst
  * https://hub.docker.com/r/amazon/dynamodb-local/
  * https://boto3.amazonaws.com/v1/documentation/api/latest/guide/dynamodb.html
  * https://stacker.readthedocs.io/en/latest/
  * https://github.com/cloudtools/troposphere
