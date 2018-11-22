import boto3
import requests
from uuid import uuid4

class ImageFetcher:
    """
    Image uploading from extrernal URL to s3 bucket
    """
    def __init__(self, mode='local', endpoint_url=None, secret_key=None, access_key=None, region=None, use_ssl=True):

        self.session = None
        self.s3 = None

        if mode == "local":
            use_ssl=False
            if endpoint_url is None:
                endpoint_url = 'http://localhost:8008'

        self.session = boto3.Session()
        self.s3 = self.session.resource('s3', 
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            use_ssl=use_ssl,
            region_name=region
        )

    def upload_object(self, bucket, fileobj):
        bucket = self.s3.Bucket(bucket)
        uuid = str(uuid4())

        try:
            bucket.upload_fileobj(fileobj, uuid)
        except Exception as e:
            print("Error: ", e)
            return e
        return uuid

    def get_url_stream(self, url):
        req = requests.get(url, stream=True)
        return req.raw
        