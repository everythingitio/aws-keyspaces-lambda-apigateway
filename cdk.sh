#!/bin/bash

export AWS_REGION_NAME=us-east-1
export DEPLOYMENT_ENV=test2

if [[ $1 == "deploy" ]]; then

    rm -rf venv/
    python3 -m venv venv/
    source venv/bin/activate
    cwd=$(pwd)
    $cwd/venv/bin/pip install -r requirements.txt
    cd $cwd/keyspaces_lambda
    rm -rf .dist
    $cwd/venv/bin/pip install -r requirements.txt -t .dist
    cd $cwd/keyspaces_lambda/.dist
    rm keyspaces_lambda.zip || true
    zip -r9 keyspaces_lambda.zip * -x "bin/*" "pip*" "pylint*" "setuptools*"
    cd $cwd/keyspaces_lambda/
    curl https://www.amazontrust.com/repository/AmazonRootCA1.pem -O
    zip -r9 .dist/keyspaces_lambda.zip * -x ".dist"
    cd $cwd
    deactivate
    
    # source back to cdk venv environment
    source ~/environment/.venv/bin/activate
    echo "Action: cdk $1 Begin..."
    cdk $1 --require-approval never
    echo "Action: cdk $1 --require-approval never Done..."
    
    opts=""
    iam_user="$DEPLOYMENT_ENV"CassandraDemoUser
    secretmgmr="$DEPLOYMENT_ENV"cassandra_demo_creds
    user_exists=$(aws iam $opts list-service-specific-credentials --user-name $iam_user --output text --query "ServiceSpecificCredentials[*].[UserName]")
    if [ "${user_exists}" == "" ]; then
        echo "Credentials missing for $iam_user generating and adding to secrets manager."
        secret=$(aws iam $opts create-service-specific-credential --user-name $iam_user --service-name cassandra.amazonaws.com)
        aws secretsmanager $opts  put-secret-value --secret-id $secretmgmr --secret-string "$secret"
    else
        echo "Credentials already created for  $iam_user, not overwriting it."
    fi
        
    
elif [[ $1 == "destroy" ]]; then
    echo "Action: cdk $1 Begin..."
    cdk $1 --force
    echo "Action: cdk $1 --force Done..."
else
  echo "Invalid or no action"
fi

# rm -rf venv
# rm -rf keyspaces_lambda/.dist/
# rm -rf keyspaces_lambda/AmazonRootCA1.pem