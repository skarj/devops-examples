# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/dynamodb.html

import boto3

def getDynamoDBConnection(endpoint_url=None, secret_access_key=None, access_key_id=None, local=False):

    if local:
        db = boto3.resource('dynamodb',
            endpoint_url=endpoint_url
        )

    return db

def createImagesTable(db):
    # Create the DynamoDB table.
    table = db.create_table(
        TableName='images',
        KeySchema=[
            {
                'AttributeName': 'ImageID',
                'KeyType': 'HASH'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'ImageID',
                'AttributeType': 'S'
            }

        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )

    # Wait until the table exists.
    table.meta.client.get_waiter('table_exists').wait(TableName='images')

    return table
