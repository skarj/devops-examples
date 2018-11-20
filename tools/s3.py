import boto3

session = boto3.Session()
s3 = session.resource('s3',
    endpoint_url='http://127.0.0.1:8080/',
    use_ssl=False
)

def put_object(bucket, key, body):
    bucket = s3.Bucket(bucket)
    try:
        print(bucket)
        bucket.upload_fileobj(body, key)
    except Exception as e:
        print("Error: ", e)
        return e
