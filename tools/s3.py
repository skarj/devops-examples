
import boto3

s3 = boto3.client(
    's3',
    aws_access_key_id='accessKey1',
    aws_secret_access_key='verySecretKey1',
    endpoint_url='http://localhost:8080'
)

def upload_file(file, bucket_name, filename, acl="public-read"):

    try:
        s3.upload_file(
            file,
            bucket_name,
            filename,
            ExtraArgs={
                "ACL": acl
            }
        )

    except Exception as e:
        print("Error: ", e)
        return e
