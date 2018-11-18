from datetime                       import datetime
from botocore.exceptions            import ClientError

class DBController:
    """
    DBController class provides the necessary DynamoDB API calls.
    """
    def __init__(self, connectionManager):
        self.cm = connectionManager

    def checkIfTableExists(self):
        try:
            is_table_existing = self.cm.getImagesTable().table_status in (
                "CREATING", "UPDATING", "DELETING", "ACTIVE")
        except ClientError:
            is_table_existing = False
            self.cm.createImagesTable()

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

    def listImages(self):

        table = self.cm.getImagesTable()

        response = table.scan()

        return response['Items']
