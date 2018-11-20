from flask                          import Flask, jsonify, request
from flask_restful                  import Api, Resource
from dynamodb.connectionManager     import ConnectionManager
from dynamodb.DBController          import DBController
from uuid                           import uuid4
from tools                          import s3
import requests

app = Flask(__name__)
api = Api(app)

cm = ConnectionManager(mode='local')
controller = DBController(cm)
controller.checkIfTableExists()

s3_bucket = 'images'

class Image(Resource):
    def get(self):
        images = controller.listImages()
        return images

    def post(self):
        json_data = request.get_json(force=True)
        name = json_data['name']
        url = json_data['url']
        uuid = str(uuid4())

        # implement multiple uploading
        req = requests.get(url, stream=True)
        file_object = req.raw
        #req_data = file_object.read()
        # implement check if bucket exist
        s3.put_object(s3_bucket, uuid, file_object)

        # save metadata to the dynamodb
        controller.addImage(uuid, name, url, s3_bucket)

        return jsonify(
            message="Image successfully uploaded",
            url=url
        )

api.add_resource(Image, "/api/v1/images")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000 ,debug=True)
