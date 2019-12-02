from .setupDynamoDB import getDynamoDBConnection, createImagesTable

class ConnectionManager:

    def __init__(
        self,
        endpoint_url=None,
        secret_access_key=None,
        access_key_id=None,
        region=None):

        self.db = None
        self._images_table = None

        self.db = getDynamoDBConnection(
            endpoint_url=endpoint_url,
            secret_access_key=secret_access_key,
            access_key_id=access_key_id,
            region=region
        )

        self.setup_images_table()

    def setup_images_table(self):
        try:
            self._images_table = self.db.Table('images')
        except Exception as e:
            raise e("There was an issue trying to retrieve the images table")

    def get_images_table(self):
        if self._images_table == None:
            self.setup_images_table()

        return self._images_table

    def create_images_table(self):
        self._images_table = createImagesTable(self.db)
