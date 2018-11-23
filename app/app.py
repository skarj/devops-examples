from flask                          import Flask, jsonify, request
from flask_restful                  import Api, Resource
from dynamodb.connectionManager     import ConnectionManager
from dynamodb.dbController          import DBController
from imageFetcher.fetcher           import Fetcher
from os                             import environ

app = Flask(__name__, instance_relative_config=True)
app.config.from_object(environ['APP_SETTINGS'])
api = Api(app)

cm = ConnectionManager(
    secret_access_key=app.config['AWS_SECRET_KEY'],
    access_key_id=app.config['AWS_ACCESS_KEY'],
    region=app.config['AWS_REGION'],
    endpoint_url=app.config['DYNAMODB_ENDPOINT']
)
dynamodb = DBController(cm)
dynamodb.checkIfTableExists()

class Image(Resource):
    def get(self):
        images = dynamodb.listImages()
        return images

    def post(self):
        json_data = request.get_json(force=True)
        name = json_data['name']
        url = json_data['url']

        fetcher=Fetcher(
            access_key=app.config["AWS_SECRET_KEY"],
            secret_key=app.config["AWS_ACCESS_KEY"],
            endpoint_url=app.config["S3_ENDPOINT"]
        )
        stream = fetcher.get_url_stream(url)
        image_id = fetcher.upload_object(app.config["S3_BUCKET"], stream)

        dynamodb.addImage(image_id, name, url, app.config["S3_BUCKET"])

        return jsonify(
            Result="Image successfully uploaded",
            URL=url
        )

api.add_resource(Image, "/api/v1/images")

if __name__ == '__main__':
    app.run(
        host=app.config["HOST"],
        port=app.config["PORT"],
        debug=app.config["DEBUG"]
    )
