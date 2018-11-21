from flask                          import Flask, jsonify, request
from flask_restful                  import Api, Resource
from dynamodb.connectionManager     import ConnectionManager
from dynamodb.dbController          import DBController
from s3.imageFetcher                import ImageFetcher
from os                             import environ

app = Flask(__name__)
api = Api(app)

db_endpoint_url=environ.get('DYNAMODB_ENDPOINT')
s3_endpoint_url=environ.get('S3_ENDPOINT')
mode=environ.get('MODE')
bucket = 'images'

cm = ConnectionManager(endpoint_url=db_endpoint_url)
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

        uploader=ImageFetcher(mode=mode)
        stream = uploader.get_url_stream(url)
        image_id = uploader.upload_object(bucket, stream)

        dynamodb.addImage(image_id, name, url, bucket)

        return jsonify(
            Result="Image successfully uploaded",
            URL=url
        )

api.add_resource(Image, "/api/v1/images")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000 ,debug=True)
