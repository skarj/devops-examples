import os

class Config(object):
    DEBUG = False
    PORT = 5000
    HOST = '0.0.0.0'
    AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY')
    AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY')
    AWS_REGION = os.environ.get('AWS_REGION')
    S3_BUCKET = os.environ.get('S3_BUCKET')
    S3_ENDPOINT = 'http://{}.s3.amazonaws.com/'.format(S3_BUCKET)
    DYNAMODB_ENDPOINT = os.environ.get('DYNAMODB_ENDPOINT')

class dev(Config):
    S3_ENDPOINT = 'http://localhost:8008'
    DYNAMODB_ENDPOINT = 'http://localhost:8000'
    DEBUG = True

class test(Config):
    S3_ENDPOINT = os.environ.get('S3_ENDPOINT')
    DEBUG = True

class prod(Config):
    HOST = '127.0.0.1'
