#CSV > S3 > Lambda > SQS > Lambda > DynamoDb

from aws_cdk import (
    CfnOutput,
    CfnTag,
    Duration,
    Stack,
    aws_sqs as sqs,
    aws_s3 as s3,
    aws_s3_notifications as s3_notifications,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_apigateway as _apigateway,
    aws_sns as sns,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cloudwatch_actions,
    aws_dynamodb as dynamodb,
    Tags,
    RemovalPolicy,
    aws_events_targets,
    custom_resources as cr,
    aws_cassandra as cassandra,
    aws_secretsmanager as secretsmanager,
    Fn,
    Arn
)
from aws_cdk.aws_events import Rule, Schedule
import os


from constructs import Construct
from aws_cdk.aws_lambda import Function, Tracing

class KeyspacesLambdaStack(Stack):

    def create_keyspaces1(self):
        
        keyspaces1 = cassandra.CfnKeyspace(self, self.env + "cassandra_demo",
            keyspace_name=self.env + "cassandra_demo",
            replication_specification=cassandra.CfnKeyspace.ReplicationSpecificationProperty(
                replication_strategy="SINGLE_REGION"
            ),
            tags=[CfnTag(
                key="app",
                value="CassandraDemoApp"
            )]
        )
        
        self.keyspaces1 = keyspaces1
        
    def create_keyspaces_table1(self):
        
        cassandra_table1 = cassandra.CfnTable(self, self.env + "country_cities",
            keyspace_name=self.keyspaces1.keyspace_name,
            partition_key_columns=[cassandra.CfnTable.ColumnProperty(
                column_name="country",
                column_type="TEXT"
            )],
            client_side_timestamps_enabled=False,
            clustering_key_columns=[cassandra.CfnTable.ClusteringKeyColumnProperty(
                column=cassandra.CfnTable.ColumnProperty(
                    column_name="city_name",
                    column_type="TEXT"
                ),
                # the properties below are optional
                order_by="ASC"
            )],
            point_in_time_recovery_enabled=False,
            regular_columns=[cassandra.CfnTable.ColumnProperty(
                column_name="population",
                column_type="INT"
            )],
            table_name=self.env + "country_cities",
            tags=[CfnTag(
                key="app",
                value="CassandraDemoApp"
            )]
        )
        cassandra_table1.add_dependency(self.keyspaces1)

        self.cassandra_table1 = cassandra_table1

    def create_keyspaces_iam_user(self):
        
        user = iam.User(self, self.env + 'CassandraDemoUser',user_name=self.env + 'CassandraDemoUser')

        table_arn = Stack.format_arn(self,
            service='cassandra',
            resource='keyspace/{}/table'.format(self.keyspaces1.keyspace_name),
            resource_name=self.env + "country_cities")

        policy = iam.Policy(self, 'CassandraFullDataAccess')
        policy.add_statements(iam.PolicyStatement(
            resources=[ table_arn],
            actions=['cassandra:Select', 'cassandra:Modify']
        ))
        policy.attach_to_user(user)
    
    def create_secrets_manager(self):
        secrets = secretsmanager.Secret(self,
             self.env + 'cassandra_demo_creds',
             secret_name=self.env + 'cassandra_demo_creds')
        self.secrets1 = secrets
             
    def create_lambda_function(self):
        code = _lambda.Code.from_asset('keyspaces_lambda/.dist/keyspaces_lambda.zip')
        cassandra_function = _lambda.Function(self,
            self.env + 'cassandra-demo',
            function_name=self.env + 'cassandra-demo',
            runtime=_lambda.Runtime.PYTHON_3_8,
            memory_size=1024,
            code=code,
            handler='demo_handler.handler',
            #tracing=_lambda.Tracing.ACTIVE, # deactivate if not needed
            environment={'CASSANDRA_CREDS': self.secrets1.secret_arn},
            )
            
        cassandra_function.add_environment('CASSANDRA_CREDS', self.secrets1.secret_arn)
        cassandra_function.add_environment('CASSANDRA_KEYSPACE1', self.keyspaces1.keyspace_name)
        cassandra_function.add_environment('CASSANDRA_TABLE1', self.cassandra_table1.table_name)

        self.secrets1.grant_read(cassandra_function)
        
        api = _apigateway.LambdaRestApi(self, self.env + 'cassandra-demo-api', handler=cassandra_function)
             
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.env = os.environ.get('DEPLOYMENT_ENV', 'dev5')
        self.create_keyspaces1()
        self.create_keyspaces_table1()
        self.create_keyspaces_iam_user()
        self.create_secrets_manager()
        self.create_lambda_function()


