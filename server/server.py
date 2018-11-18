from flask                          import Flask
from flask_restful                  import Api, Resource, reqparse
from dynamodb.connectionManager     import ConnectionManager
from dynamodb.DBController          import DBController

app = Flask(__name__)
api = Api(app)

IMAGES_JSON = [
    {
        'name': 'Falsk-restful',
        'upload_url': 'https://flask-restful.readthedocs.io/en/0.3.5/_static/flask-restful-small.png',
        's3_url': 'http://bucket.s3-aws-region.amazonaws.com/cccccc',
        'timestamp': '1542143608'
    },
    {
        'name': 'Docker logo',
        'upload_url': 'https://www.docker.com/sites/default/files/Whale%20Logo332_5.png',
        's3_url': 'http://bucket.s3-aws-region.amazonaws.com/bbbbbb',
        'timestamp': '1542143608'
    },
    {
        'name': 'AWS logo',
        'upload_url': 'https://upload.wikimedia.org/wikipedia/commons/1/1d/AmazonWebservices_Logo.svg',
        's3_url': 'http://bucket.s3-aws-region.amazonaws.com/aaaaaa',
        'timestamp': '1542143608'
    }
]

cm = ConnectionManager(mode='local', endpoint_url='http://localhost:8000')
controller = DBController(cm)

controller.checkIfTableExists()
#controller.addImage('name2', 'ffefef', 'fefefef')

class Files(Resource):
    def get(self):
        return IMAGES_JSON, 200
      
api.add_resource(Files, "/images")

app.run(debug=True)