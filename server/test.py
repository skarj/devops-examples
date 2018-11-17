from dynamodb.connectionManager     import ConnectionManager
from dynamodb.DBController          import DBController

cm = ConnectionManager(mode='local', endpoint_url='http://localhost:8000')
controller = DBController(cm)

#cm.createImagesTable()

# try:
#     is_table_existing = table.table_status in ("CREATING", "UPDATING",
#                                              "DELETING", "ACTIVE")
# except ClientError:
#     is_table_existing = False
#     print "Table %s doesn't exist. Creating table" % table.name
#     createImagesTable(db)


controller.addImage('name', 'ffefef', 'fefefef')