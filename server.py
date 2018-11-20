from flask                          import Flask, jsonify, request
from flask_restful                  import Api, Resource
from dynamodb.connectionManager     import ConnectionManager
from dynamodb.dbController          import DBController
from s3.imageUploader               import ImageUploader

app = Flask(__name__)
api = Api(app)

cm = ConnectionManager(mode='local')
controller = DBController(cm)
controller.checkIfTableExists()

bucket = 'images'

class Image(Resource):
    def get(self):
        images = controller.listImages()
        return images

    def post(self):
        json_data = request.get_json(force=True)
        name = json_data['name']
        url = json_data['url']

        uploader=ImageUploader(mode='local')
        stream = uploader.get_url_stream(url)
        image_id = uploader.upload_object(bucket, stream)

        controller.addImage(image_id, name, url, bucket)

        return jsonify(
            Result="Image successfully uploaded",
            URL=url
        )

api.add_resource(Image, "/api/v1/images")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000 ,debug=True)
