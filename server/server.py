from flask                          import Flask, jsonify, request
from flask_restful                  import Api, Resource
from dynamodb.connectionManager     import ConnectionManager
from dynamodb.DBController          import DBController

app = Flask(__name__)
api = Api(app)

cm = ConnectionManager(mode='local', endpoint_url='http://localhost:8000')
controller = DBController(cm)

controller.checkIfTableExists()

class Image(Resource):
    def get(self):
        images = controller.listImages()
        return images

    def post(self):
        json_data = request.get_json(force=True)
        name = json_data['name']
        url = json_data['url']
        s3_url = 'http://bucket.s3-aws-region.amazonaws.com/aaaaaa'

        # if(name == images["name"]):
        #     return "Image with name {} already exists".format(name), 400

        controller.addImage(name, url, s3_url)

        return jsonify(name=name, url=url, s3_url=s3_url)


api.add_resource(Image, "/api/v1/images")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000 ,debug=True)
