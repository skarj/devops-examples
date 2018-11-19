
import boto3

s3 = boto3.client(
    's3',
    aws_access_key_id='accessKey1',
    aws_secret_access_key='verySecretKey1',
    endpoint_url='http://localhost:8080'
)

def upload_file(bucket, key, body):

    try:
        s3.put_object(
            Bucket = bucket,
            Key = key,
            Body = body
        )

    except Exception as e:
        print("Error: ", e)
        return e
