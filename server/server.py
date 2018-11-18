from flask                          import Flask
from flask_restful                  import Api, Resource, reqparse
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
        return images, 200

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("name")
        parser.add_argument("url")
        args = parser.parse_args()

        # if(name == images["name"]):
        #     return "Image with name {} already exists".format(name), 400

        controller.addImage(args['name'], args['url'], 'http://bucket.s3-aws-region.amazonaws.com/aaaaaa')

        return "Added {}".format(args['name']), 200


api.add_resource(Image, "/api/v1/images")

app.run(debug=True)