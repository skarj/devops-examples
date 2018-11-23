# S3 Image Uploader
## Starting dev environment

    python -m virtualenv ~/Projects/skaarj/virtualenv
    source ~/Projects/skaarj/virtualenv/bin/activate
    pip install -r requirements.txt
    pip install docker-compose
    docker-compose up -d dynamodb s3server aws-cli

    export APP_SETTINGS="config.dev"
    export AWS_ACCESS_KEY="accessKey1"
    export AWS_SECRET_KEY="verySecretKey1"
    export AWS_REGION="eu-central-1"
    export S3_BUCKET="images"

    python ./app.py

or

    pip install docker-compose
    docker-compose up -d


## List all images

    curl -X GET "localhost:5000/api/v1/images"


## Request a single image

    curl -X GET "localhost:5000/api/v1/images/name/test1"


## Request image uploading

    curl -X POST "localhost:5000/api/v1/images" -H 'Content-Type: application/json' -d'
    {
        "name": "Docker logo",
        "url" : "https://www.docker.com/sites/default/files/Whale%20Logo332_5.png"
    }
    '


## S3 bucket check

See all buckets:

    aws s3 ls --endpoint-url=http://localhost:8008

Create bucket:

    aws s3 mb --endpoint-url=http://localhost:8008 s3://images

List bucket

    aws s3api list-objects --endpoint-url=http://localhost:8008 --bucket images


## Documents
  * https://technologyconversations.com/2014/08/12/rest-api-with-json/
  * https://codeburst.io/this-is-how-easy-it-is-to-create-a-rest-api-8a25122ab1f3
  * https://boto3.amazonaws.com/v1/documentation/api/latest/guide/dynamodb.html
  * https://docs.aws.amazon.com/en_us/amazondynamodb/latest/developerguide/GettingStarted.Python.03.
  * https://github.com/scality/cloudserver/blob/master/docs/GETTING_STARTED.rst
