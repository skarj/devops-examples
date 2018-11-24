from flask                          import Flask, jsonify, request
from flask_restful                  import Api, Resource
from dynamodb.connectionManager     import ConnectionManager
from dynamodb.dbController          import DBController
from imageFetcher.fetcher           import Fetcher
from os                             import environ

app = Flask(__name__, instance_relative_config=True)
app.config.from_object(environ['APP_SETTINGS'])
api = Api(app)

class Image(Resource):
    def __init__(self):

        self.fetcher = Fetcher(
            access_key=app.config["AWS_ACCESS_KEY"],
            secret_key=app.config["AWS_SECRET_KEY"],
            region=app.config["AWS_REGION"],
            endpoint_url=app.config["S3_ENDPOINT"]
        )

        # TODO
        #self.fetcher.checkIfBucketExists()

        cm = ConnectionManager(
            secret_access_key = app.config['AWS_SECRET_KEY'],
            access_key_id = app.config['AWS_ACCESS_KEY'],
            region = app.config['AWS_REGION'],
            endpoint_url = app.config['DYNAMODB_ENDPOINT']
        )
        self.dynamodb = DBController(cm)
        self.dynamodb.checkIfTableExists()

    def get(self):
        images = self.dynamodb.listImages()
        return images

    def post(self):
        json_data = request.get_json(force=True)
        image_name = json_data['name']
        image_url = json_data['url']
        s3_bucket = app.config["S3_BUCKET"]
        s3_endpoint = app.config["S3_ENDPOINT"]

        stream = self.fetcher.get_url_stream(image_url)
        image_id = self.fetcher.upload_object(s3_bucket, stream)

        s3_image_url = '{}/{}/{}'.format(s3_endpoint, s3_bucket, image_id)
        self.dynamodb.addImage(image_id, image_name, image_url, s3_image_url)

        return jsonify(
            Result="Image successfully uploaded",
            URL=s3_image_url
        )

api.add_resource(Image, "/api/v1/images")

if __name__ == '__main__':
    app.run(
        host=app.config["HOST"],
        port=app.config["PORT"],
        debug=app.config["DEBUG"]
    )
