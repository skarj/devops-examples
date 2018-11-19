from flask                          import Flask, jsonify, request
from flask_restful                  import Api, Resource
from dynamodb.connectionManager     import ConnectionManager
from dynamodb.DBController          import DBController
from tools                          import s3
import urllib2

app = Flask(__name__)
api = Api(app)

cm = ConnectionManager(mode='local', endpoint_url='http://localhost:8000')
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
        bucket = s3_bucket
        
        # TODO: check if image name is in use

        # download image
        req = urllib2.Request(url)
        resp = urllib2.urlopen(req)

        s3.upload_file(bucket, name, resp)

        # save metadata to the dynamodb
        controller.addImage(name, url, bucket)

        return jsonify(name=name, url=url, s3_url=bucket)


api.add_resource(Image, "/api/v1/images")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000 ,debug=True)
