# Image Fetcher
This repository contains examples that may be usefull for Devops Engineers:
  * python falsk application that uses AWS Dynamodb, AWS S3 and REST api
  * nginx-unit configuration example for python application in docker container
  * docker-compose example for local tests
  * troposphere blueprints/stacker configs for AWS EKS cluster creation
  * Helm chart example


## Required tools
  * stacker
  * aws-iam-authenticator
  * kubectl
  * helm


## Starting test environments
### Starting local dev environment

*  Create virtual environment

        python -m venv flask
        source flask/bin/activate

*  Install dependencies

        pip install -r requirements.txt
        pip install docker-compose

*  Start S3 and Dynamodb local servers, create bucket for images

        docker-compose up -d dynamodb s3server aws-cli

*  Set environment variables

        export APP_SETTINGS="config.dev"
        export AWS_ACCESS_KEY="accessKey1"
        export AWS_SECRET_KEY="verySecretKey1"
        export AWS_REGION="eu-central-1"
        export S3_BUCKET="images"

*  Start application

        python ./app.py


### Starting local test environment

*  Install docker-compose

        pip install docker-compose

*  Start service

        docker-compose up -d


### Starting application container manually

*  Build docker image

        docker build --tag=imagefetcher .

*  Start container

        docker run -d -e APP_SETTINGS="config.dev" -p 5000:80 imagefetcher


## Starting production environment
### Creating AWS infrastructure

*  Install dependencies

        cd stacker
        pip install -r requirements.txt

*  Create **AWS infrastructure**

        stacker build envs/test.yaml stacks/imageFetcher.yaml --recreate-failed --tail
        stacker info envs/test.yaml stacks/imageFetcher.yaml

*  Configure **Kubernetes**

        aws eks update-kubeconfig --name cluster_name
        kubectl get svc
        kubectl apply -f aws-auth-cm.yaml
        kubectl get nodes --watch

*  Install **Helm**

        kubectl apply -f helm/helm-tiller
        helm init --service-account tiller

*  Install **Imagefetcher**

        helm install helm/imagefetcher --name imagefetcher --namespace imagefetcher -f values-test.yaml


### Destroy AWS infrastructure

    stacker destroy envs/test.yaml stacks/imageFetcher.yaml --force --tail


## Testing application
*  Got configuration

        curl -X GET "localhost:5000/api/v1/config"

*  Request image uploading

        curl -X POST "localhost:5000/api/v1/images" -H 'Content-Type: application/json' -d'
        {
            "name": "Docker logo",
            "url" : "https://www.docker.com/sites/default/files/Whale%20Logo332_5.png"
        }
        '

*  Request a single image

        curl -X GET "localhost:5000/api/v1/images/name/test1"

*  List all images

        curl -X GET "localhost:5000/api/v1/images"

*  Check S3 bucket

        aws s3api list-objects --endpoint-url=http://localhost:8008 --bucket images

## Documents
  * https://flask-restful.readthedocs.io/en/latest/
  * https://github.com/scality/cloudserver/blob/master/docs/GETTING_STARTED.rst
  * https://hub.docker.com/r/amazon/dynamodb-local/
  * https://boto3.amazonaws.com/v1/documentation/api/latest/guide/dynamodb.html
  * https://stacker.readthedocs.io/en/latest/
  * https://github.com/cloudtools/troposphere
  * https://docs.aws.amazon.com/en_us/eks/latest/userguide/getting-started.html#eks-launch-workers
