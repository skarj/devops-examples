# devops-callenge
## Starting dev environment

    python -m virtualenv ~/Projects/skaarj/virtualenv
    source ~/Projects/skaarj/virtualenv/bin/activate
    pip install -r requirements.txt
    pip install docker-compose
    docker-compose up -d


## List all images

    Protocol: GET
    URI: /api/v1/images
    Request body: EMPTY


## Request a single image

    Protocol: GET
    URI: /api/v1/images/name/test1
    Request body: EMPTY


## Request book creation

    Protocol: POST
    URI: /api/v1/images
    Request body:

    {
        name: 'Docker logo',
        url: 'https://www.docker.com/sites/default/files/Whale%20Logo332_5.png'
    }

## S3

    [default]
    aws_access_key_id = accessKey1
    aws_secret_access_key = verySecretKey1

    See all buckets:

    aws s3 ls --endpoint-url=http://localhost:8080

    Create bucket:

    aws s3 mb --endpoint-url=http://localhost:8080 s3://images

    List bucket

    aws s3api list-objects --endpoint-url=http://localhost:8080 --bucket images

    wget http://localhost:8080/images/image1

## Documents
  * https://technologyconversations.com/2014/08/12/rest-api-with-json/
  * https://codeburst.io/this-is-how-easy-it-is-to-create-a-rest-api-8a25122ab1f3
  * https://boto3.amazonaws.com/v1/documentation/api/latest/guide/dynamodb.html
  * https://docs.aws.amazon.com/en_us/amazondynamodb/latest/developerguide/GettingStarted.Python.03.
  * https://github.com/scality/cloudserver/blob/master/docs/GETTING_STARTED.rst
