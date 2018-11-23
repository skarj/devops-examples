from .setupDynamoDB import getDynamoDBConnection, createImagesTable

class ConnectionManager:

    def __init__(
        self,
        endpoint_url=None,
        secret_access_key=None,
        access_key_id=None,
        region=None):

        self.db = None
        self.imagesTable = None

        self.db = getDynamoDBConnection(
            endpoint_url=endpoint_url,
            secret_access_key=secret_access_key,
            access_key_id=access_key_id,
            region=region
        )

        self.setupImagesTable()

    def setupImagesTable(self):
        try:
            self.imagesTable = self.db.Table('images')
        except Exception as e:
            raise e("There was an issue trying to retrieve the images table")

    def getImagesTable(self):
        if self.imagesTable == None:
            self.setupImagesTable()

        return self.imagesTable

    def createImagesTable(self):
        self.imagesTable = createImagesTable(self.db)
