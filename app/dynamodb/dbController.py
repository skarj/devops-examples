from datetime                       import datetime
from botocore.exceptions            import ClientError

class DBController:
    """
    DynamoDB API calls
    """
    def __init__(self, connectionManager):
        self.cm = connectionManager

    def check_if_table_exists(self):
        try:
            tablestatus = self.cm.get_images_table().table_status in (
                "CREATING", "UPDATING", "DELETING", "ACTIVE")
        except ClientError:
            tablestatus = False
            self.cm.create_table.images()

    def add_image(self, image_id, image_name, upload_url, s3_url):
        date = str(datetime.now())
        table = self.cm.get_images_table()
        table.put_item(
            Item={
                'ImageID': image_id,
                'ImageName': image_name,
                'UploadURL': upload_url,
                'S3URL': s3_url,
                'Timestamp': date
            }
        )

    def list_images(self):
        table = self.cm.get_images_table()
        response = table.scan()
        return response['Items']
