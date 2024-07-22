# Amazon Keyspaces (for Apache Cassandra) Lambda Python Demo.

This demo is to show how to deploy and use Amazon Keyspaces (for Apache Cassandra) from a python Lambda.

This demo uses the documentation provided here https://docs.aws.amazon.com/mcs/latest/devguide/programmatic.html, sets it up and automates it.

The Service Credentials are stored in Secrets Manager and post deploying the CF stack (generated with CDK) the deployspec uses the `infrastructure\set_secrets.sh` script to generated the Service Credentials for the IAM User CassandraDemoUser and stores them in secrets manager. These credentials are then used by the lambda when connecting to Cassandra.

Once the application is deployed (se below) to test it first load up some data then query it.

````

Add KeyspacesFullAccess to iam user manually if permission issue shows.

export YOUR_API_ID=1234

curl --header "Content-Type: application/json" \
  --request POST \
  --data '{"country": "Sweden", "city_name": "Göteborg", "population": 600000}' \
  https://$YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/countries
  
curl https://$YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/countries?country=Sweden

When destroying, remove the iam user manually.

````

### Deploying 

To deploy this application into a AWS account you can use the `./cdk.sh deploy` script provided. 

````bash 


deactivate existing python env 
$ deactivate

removed the profile to use the environment variables

$ export AWS_ACCESS_KEY_ID=xxxx
$ export AWS_SECRET_ACCESS_KEY=yyyy
$ export AWS_DEFAULT_REGION=us-east-1

$ ./cdk.sh deploy

````
The profile `your_aws_profile` or aws credential needs to have enough privilages to deploy the application.

````yml
      Policies:
        - PolicyName: root
          PolicyDocument:
            Version: 2012-10-17
            Statement:
              - Effect: Allow
                Action:
                - apigateway:*
                - cassandra:*
                - cloudformation:*
                - lambda:*
                - iam:*
                - s3:*
                - secretsmanager:*
                - ssm:GetParameters
                Resource:
                - "*"
````

Cleanup

```

$ ./cdk.sh destroy


```

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

