import boto3
import os
import uuid
import json
from ssl import SSLContext, PROTOCOL_TLSv1_2, CERT_REQUIRED
from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster, ExecutionProfile, EXEC_PROFILE_DEFAULT, ConsistencyLevel

CASSANDRA_CREDS = os.environ['CASSANDRA_CREDS']
AWS_DEFAULT_REGION = os.environ['AWS_DEFAULT_REGION']

CASSANDRA_KEYSPACE1 = os.environ['CASSANDRA_KEYSPACE1']
CASSANDRA_TABLE1 = os.environ['CASSANDRA_TABLE1']

print(f'CASSANDRA_KEYSPACE1 {CASSANDRA_KEYSPACE1} CASSANDRA_TABLE1 {CASSANDRA_TABLE1} CASSANDRA_CREDS {CASSANDRA_CREDS} AWS_DEFAULT_REGION {AWS_DEFAULT_REGION}')

secret_client = boto3.client('secretsmanager')
secret_response = secret_client.get_secret_value(SecretId=CASSANDRA_CREDS)
secret = json.loads(secret_response.get('SecretString'))

cassandra_user = secret['ServiceSpecificCredential']['ServiceUserName']
cassandra_password = secret['ServiceSpecificCredential']['ServicePassword']
auth_provider = PlainTextAuthProvider(username=cassandra_user, password=cassandra_password)

ssl_context = SSLContext(PROTOCOL_TLSv1_2)
ssl_context.load_verify_locations('AmazonRootCA1.pem')
ssl_context.verify_mode = CERT_REQUIRED
cluster = Cluster(['cassandra.{}.amazonaws.com'.format(AWS_DEFAULT_REGION)], port=9142, ssl_context=ssl_context, auth_provider=auth_provider)
session = cluster.connect()

def handler(event, context):
    response = {'statusCode': 405}
    if event['httpMethod'] in ['PUT', 'POST']:
        do_upsert(json.loads(event['body']))
        response['statusCode'] = 201
    elif event['httpMethod'] == 'GET':
        response['body'] = do_get(event['queryStringParameters']['country'])
        response['statusCode'] = 200
    return response

def do_get(country_name): 
    demo_query = "SELECT country, city_name, population FROM {}.{} WHERE country = '{}'".format(CASSANDRA_KEYSPACE1, CASSANDRA_TABLE1, country_name)
    cities = session.execute(demo_query)
    response = []
    for city in cities:
        response.append({'country':city.country, 'city_name':city.city_name, 'population': city.population})
    return json.dumps(response)

def do_upsert(body):
    stmt = session.prepare("INSERT INTO {}.{} (country, city_name, population) VALUES (?, ?, ?)".format(CASSANDRA_KEYSPACE1, CASSANDRA_TABLE1))
    execution_profile = session.execution_profile_clone_update(session.get_execution_profile(EXEC_PROFILE_DEFAULT))
    execution_profile.consistency_level = ConsistencyLevel.LOCAL_QUORUM
    session.execute(stmt, body.values(), execution_profile=execution_profile)
