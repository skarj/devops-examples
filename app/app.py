from flask                          import Flask, jsonify, request
from flask_restful                  import Api, Resource
from dynamodb.connectionManager     import ConnectionManager
from dynamodb.dbController          import DBController
from imageFetcher.fetcher           import Fetcher
from os                             import environ

application = Flask(__name__, instance_relative_config=True)
application.config.from_object(environ['APP_SETTINGS'])
api = Api(application)

class Images(Resource):
    def __init__(self):

        self.fetcher = Fetcher(
            access_key=application.config["AWS_ACCESS_KEY"],
            secret_key=application.config["AWS_SECRET_KEY"],
            region=application.config["AWS_REGION"],
            endpoint_url=application.config["S3_ENDPOINT"]
        )

        # TODO
        #self.fetcher.checkIfBucketExists()

        cm = ConnectionManager(
            secret_access_key = application.config['AWS_SECRET_KEY'],
            access_key_id = application.config['AWS_ACCESS_KEY'],
            region = application.config['AWS_REGION'],
            endpoint_url = application.config['DYNAMODB_ENDPOINT']
        )
        self.dynamodb = DBController(cm)
        self.dynamodb.check_if_table_exists()

    def get(self):
        images = self.dynamodb.list_images()
        return images

    def post(self):
        json_data = request.get_json(force=True)
        image_name = json_data['name']
        image_url = json_data['url']
        s3_bucket = application.config["S3_BUCKET"]
        s3_endpoint = application.config["S3_ENDPOINT"]

        stream = self.fetcher.get_url_stream(image_url)
        image_id = self.fetcher.upload_object(s3_bucket, stream)

        s3_image_url = '{}/{}/{}'.format(s3_endpoint, s3_bucket, image_id)
        self.dynamodb.add_image(image_id, image_name, image_url, s3_image_url)

        return jsonify(
            Result="Image successfully uploaded",
            URL=s3_image_url
        )

class Config(Resource):
    def get(self):
        return jsonify(
            app_port = application.config['PORT'],
            app_host = application.config['HOST'],
            aws_region = application.config['AWS_REGION'],
            dynamodb_endpoint = application.config['DYNAMODB_ENDPOINT'],
            s3_bucket_name = application.config['S3_BUCKET'],
            s3_bucket_endpoint = application.config['S3_ENDPOINT']
        )


api.add_resource(Images, "/api/v1/images")
api.add_resource(Config, "/api/v1/config")

if __name__ == '__main__':
    application.run(
        port=application.config["PORT"],
        debug=application.config["DEBUG"]
    )
