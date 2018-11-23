# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/dynamodb.html

import boto3

def getDynamoDBConnection(
    endpoint_url=None,
    secret_access_key=None,
    access_key_id=None,
    region=None):

    db = boto3.resource('dynamodb',
        endpoint_url=endpoint_url,
        aws_secret_access_key=secret_access_key,
        aws_access_key_id=access_key_id,
        region_name=region
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
