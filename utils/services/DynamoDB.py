import boto3

def create_dynamo_resource():
    return boto3.resource('dynamodb')

def create_dynamo_table_client(resource, table_name):
    return resource.Table(table_name)
