
from .setupDynamoDB import getDynamoDBConnection, createImagesTable

class ConnectionManager:

    def __init__(self, mode=None, endpoint_url=None):
        self.db = None
        self.imageTable = None

        if mode == "local":
            if endpoint_url is None:
                endpoint_url = 'http://localhost:8000'
            self.db = getDynamoDBConnection(endpoint_url=endpoint_url, local=True)
        elif mode == "service":
            print('todo')
        else:
            raise Exception("Invalid arguments, please refer to usage.")

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
