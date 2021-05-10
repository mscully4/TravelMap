import os
import boto3
from boto3.dynamodb.conditions import Key
import json
from decimal import Decimal

class DynamoDB:
    def __init__(self):
        self.dynamo = self.create_dynamo_resource()

    def create_dynamo_resource(self):
        return boto3.resource('dynamodb')

    def create_dynamo_table_client(self, table_name):
        return self.dynamo.Table(table_name)

#Metadata Table CRUD Operations
def metadata_get(table, context):
    resp = table.get_item(Key={'context': context})
    assert resp['ResponseMetadata']['HTTPStatusCode'] == 200

    try:
        return resp['Item']['entry']
    except:
        return []

def metadata_add(table, context, place_id):
    resp = table.update_item(
        Key={'context': context},
        UpdateExpression="ADD entry :i",
        ExpressionAttributeValues={
            ':i': set([place_id])
        },
        ReturnValues="UPDATED_NEW"
    )

    assert resp['ResponseMetadata']['HTTPStatusCode'] == 200
    return True

def metadata_remove(table, context, place_id):
    resp = table.update_item(
        Key={"context": context},
        UpdateExpression="DELETE value :p",
        ExpressionAttributeValues={
            ":p": set([place_id])
        },
        ReturnValues="UPDATED_NEW"
    )
    assert resp['ResponseMetadata']['HTTPStatusCode'] == 200
    return True


#City Crud Operations
def city_get(table, place_id=None):
    if place_id:
        resp = table.get_item(Key={"place_id": place_id})
        print(resp.keys())
        assert resp['ResponseMetadata']['HTTPStatusCode'] == 200

        try:
            city = resp['Item']['entry']
        except:
            city = None
        
        return city
    else:
        resp = table.scan()
        return resp['Items']

def city_add(table, data):
    resp = table.put_item(
        Item=data,
        # ConditionExpression="attribute_not_exists(place_id)"
    )

    assert resp['ResponseMetadata']['HTTPStatusCode'] == 200
    return True

#Place CRUD Operations
def place_get(table, city_id=None, place_id=None):
    if not city_id and not place_id:
        return table.scan()

    key = None
    value = None
    if city_id:
        key = 'city_id'
        value = city_id
    if place_id:
        key = 'place_id'
        value = place_id

    resp = _query_table(table, key=key, value=value)
    assert resp['ResponseMetadata']['HTTPStatusCode'] == 200
    return resp['Items']

def place_add(table, data):
    resp = table.put_item(
        Item=data
    )

    assert resp['ResponseMetadata']['HTTPStatusCode'] == 200
    return True

def _query_table(table, key=None, value=None):
    if key is not None and value is not None:
        filtering_exp = Key(key).eq(value)
        return table.query(KeyConditionExpression=filtering_exp)

    raise ValueError('Parameters missing or invalid')
