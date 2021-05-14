import pprint
from boto3.dynamodb.conditions import Key

class Table(object):
    def __init__(self, table, partition_key, sort_key=None):
        self.table = table
        self.partition_key = partition_key
        self.sort_key = sort_key

    def _query_table(self, partition_key_value=None, sort_key_value=None):
        assert partition_key_value != None
        filtering_exp = Key(self.partition_key).eq(partition_key_value)
        if sort_key_value:
            assert self.sort_key
            filtering_exp = filtering_exp & Key(self.sort_key).eq(sort_key_value)
        resp = self.table.query(KeyConditionExpression=filtering_exp)
        return resp['Items']

    def _put_item(self, data):
        resp = self.table.put_item(
            Item=data
        )

        assert resp['ResponseMetadata']['HTTPStatusCode'] == 200
        return True

    def _delete_item(self, data):
        key = {
            self.partition_key: data.__dict__[self.partition_key]
        }
        if self.sort_key:
            key[self.sort_key] = data.__dict__[self.sort_key]

        resp = self.table.delete_item(
            Key=key
        )

        assert resp['ResponseMetadata']['HTTPStatusCode'] == 200

    def get_keys(self):
        id_key = self.sort_key if self.sort_key else self.partition_key
        scan_kwargs = {
            'ProjectionExpression': f"{id_key}"
        }

        keys = []

        done = False
        start_key = None
        while not done:
            if start_key:
                scan_kwargs['ExclusiveStartKey'] = start_key
            response = self.table.scan(**scan_kwargs)
            keys += [k[id_key] for k in response['Items']]
            start_key = response.get('LastEvaluatedKey', None)
            done = start_key is None

        return keys

    def get(self, partition_key_value=None, sort_key_value=None):
        if sort_key_value:
            assert partition_key_value
            return self._query_table(partition_key_value=partition_key_value, sort_key_value=sort_key_value)
        elif partition_key_value:
            resp = self._query_table(partition_key_value=partition_key_value)
            return resp
        else:
            return self.table.scan()['Items']

    def insert(self, obj):
        if hasattr(obj, "serialize"):
            self._put_item(obj.serialize())

    def update(self, obj):
        if hasattr(obj, "serialize"):
            self._put_item(obj.serialize())
    
    def delete(self, obj):
        if hasattr(obj, "serialize"):
            self._delete_item(obj.serializa())