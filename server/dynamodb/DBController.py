import boto3
from datetime import datetime

class DBController:
    """
    DBController class provides the necessary DynamoDB API calls.
    """
    def __init__(self, connectionManager):
        self.cm = connectionManager

    def addImage(self, image_name, upload_url, s3_url):
 
        date = str(datetime.now())
        table = self.cm.getImagesTable()

        table.put_item(
            Item={
                'ImageName': image_name,
                'UploadURL': upload_url,
                'S3URL': s3_url,
                'Timestamp': date
            }
        )
