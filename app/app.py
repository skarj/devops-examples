from flask                          import Flask, jsonify, request
from flask_restful                  import Api, Resource
from dynamodb.connectionManager     import ConnectionManager
from dynamodb.dbController          import DBController
from s3.imageFetcher                import ImageFetcher
from os                             import environ

app = Flask(__name__)
api = Api(app)

mode=environ.get('MODE')
aws_region=environ.get('AWS_DEFAULT_REGION')

s3_bucket = environ.get('S3_BUCKET')
s3_endpoint_url = environ.get('S3_ENDPOINT')
s3_access_key = environ.get('S3_ACCESS_KEY')
s3_secret_key = environ.get('S3_SECRET_KEY')

db_secret_access_key = environ.get('DYNAMODB_ACCESS_KEY')
db_access_key_id = environ.get('DYNAMODB_SECRET_KEY')
db_endpoint_url = environ.get('DYNAMODB_ENDPOINT')

cm = ConnectionManager(
    endpoint_url=db_endpoint_url,
    secret_access_key=db_secret_access_key,
    access_key_id=db_access_key_id
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

        uploader=ImageFetcher(
            mode=mode,
            endpoint_url=s3_endpoint_url,
            access_key=s3_access_key,
            secret_key=s3_secret_key,
            region=aws_region
        )
                              
        stream = uploader.get_url_stream(url)
        image_id = uploader.upload_object(s3_bucket, stream)

        dynamodb.addImage(image_id, name, url, s3_bucket)

        return jsonify(
            Result="Image successfully uploaded",
            URL=url
        )

api.add_resource(Image, "/api/v1/images")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000 ,debug=True)
