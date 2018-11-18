from dynamodb.connectionManager     import ConnectionManager
from dynamodb.DBController          import DBController
from botocore.exceptions            import ClientError

cm = ConnectionManager(mode='local', endpoint_url='http://localhost:8000')
controller = DBController(cm)

controller.checkIfTableExists()
controller.addImage('name2', 'ffefef', 'fefefef')