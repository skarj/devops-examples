
import boto3

s3 = boto3.client(
    's3',
    aws_access_key_id='accessKey1',
    aws_secret_access_key='verySecretKey1',
    endpoint_url='http://localhost:8080'
)

def upload_file(bucket, body, key):

    try:
        s3.upload_fileobj(
            body,
            bucket,
            key
        )

    except Exception as e:
        print("Error: ", e)
        return e
