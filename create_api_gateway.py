#!/usr/bin/env python

import json
import uuid

import boto3

API_NAME = "OAuthPassthrough"
LAMBDA_REGION_NAME = "us-east-1"
LAMBDA_FUNCTION_NAME = "OAuthPassthrough"
API_REGION_NAME = "us-east-1"
ACCOUNT_ID = "Account Id"

def create_api(client, name):
    return client.create_rest_api(name=name)["id"]

def root_id(client, api_id):
    result = client.get_resources(
        restApiId=api_id
    )
    root_item = result["items"][0]
    assert root_item["path"] == "/"
    return root_item["id"]

class ResourceBuilder(object):
    def __init__(self, boto_client, rest_api_id, resource_id, http_method):
        self.boto_client = boto_client
        self.rest_api_id = rest_api_id
        self.resource_id = resource_id
        self.http_method = http_method

    def put_integration(self, **kwargs):
        return self.boto_client.put_integration(
            restApiId=self.rest_api_id,
            resourceId=self.resource_id,
            httpMethod=self.http_method,
            **kwargs
        )

    def put_integration_response(self, **kwargs):
        return self.boto_client.put_integration_response(
            restApiId=self.rest_api_id,
            resourceId=self.resource_id,
            httpMethod=self.http_method,
            **kwargs
        )

    def put_method(self, **kwargs):
        return self.boto_client.put_method(
            restApiId=self.rest_api_id,
            resourceId=self.resource_id,
            httpMethod=self.http_method,
            **kwargs
        )

    def put_method_response(self, **kwargs):
        return self.boto_client.put_method_response(
            restApiId=self.rest_api_id,
            resourceId=self.resource_id,
            httpMethod=self.http_method,
            **kwargs
        )

def add_get_integration(boto_client, api_id):
    resource_builder = ResourceBuilder(
        boto_client,
        api_id,
        root_id(boto_client, api_id),
        "GET"
    )
    resource_builder.put_method(
        authorizationType="NONE",
        requestParameters={
            "method.request.querystring.client_id": False,
            "method.request.querystring.redirect_uri": False,
            "method.request.querystring.response_type": False,
            "method.request.querystring.scope": False,
            "method.request.querystring.state": False
        }
    )
    uri = (
        "arn:aws:apigateway:{api_region_name}:lambda:path/2015-03-31/functions/"
        "arn:aws:lambda:{lambda_region_name}:{account_id}:function:{lambda_function_name}/invocations"
    ).format(
        api_region_name=API_REGION_NAME,
        lambda_region_name=LAMBDA_REGION_NAME,
        account_id=ACCOUNT_ID,
        lambda_function_name=LAMBDA_FUNCTION_NAME
    )
    resource_builder.put_integration(
        type="AWS",
        uri=uri,
        integrationHttpMethod="POST",
        requestTemplates={
            "application/json": json.dumps({
                  "method": "GET",
                  "client_id": "$input.params('client_id')",
                  "redirect_uri": "$input.params('redirect_uri')",
                  "response_type": "$input.params('response_type')",
                  "scope": "$input.params('scope')",
                  "state": "$input.params('state')"
            })
        }
    )

    resource_builder.put_method_response(
        statusCode="200",
        responseModels={
            "text/html": "Empty"
        }
    )

    resource_builder.put_integration_response(
        statusCode="200",
        selectionPattern="",
        responseTemplates={
            # TODO: Just $input.path('$')?
            "application/json": "#set($inputRoot = $input.path('$'))\n$inputRoot"
        }
    )

def add_post_integration(boto_client, api_id):
    resource_builder = ResourceBuilder(
        boto_client,
        api_id,
        root_id(boto_client, api_id),
        "POST"
    )
    resource_builder.put_method(
        authorizationType="NONE"
    )
    uri = (
        "arn:aws:apigateway:{api_region_name}:lambda:path/2015-03-31/functions/"
        "arn:aws:lambda:{lambda_region_name}:{account_id}:function:{lambda_function_name}/invocations"
    ).format(
        api_region_name=API_REGION_NAME,
        lambda_region_name=LAMBDA_REGION_NAME,
        account_id=ACCOUNT_ID,
        lambda_function_name=LAMBDA_FUNCTION_NAME
    )
    resource_builder.put_integration(
        type="AWS",
        uri=uri,
        integrationHttpMethod="POST",
        requestTemplates={
            "application/x-www-form-urlencoded": json.dumps({
                  "method": "POST",
                  "client_id": "$input.params('client_id')",
                  "email": "$input.params('email')",
                  "password": "$input.params('password')",
                  "redirect_uri": "$input.params('redirect_uri')",
                  "response_type": "$input.params('response_type')",
                  "scope": "$input.params('scope')",
                  "state": "$input.params('state')"
            })
        }
    )

    resource_builder.put_method_response(
        statusCode="200",
        responseModels={
            "text/html": "Empty"
        }
    )
    resource_builder.put_method_response(
        statusCode="302",
        responseParameters={
            "method.response.header.Location": True
        },
        responseModels={
            "text/html": "Empty"
        }
    )

    resource_builder.put_integration_response(
        statusCode="200",
        selectionPattern="",
        responseTemplates={
            # TODO: Just $input.path('$')?
            "application/json": "#set($inputRoot = $input.path('$'))\n$inputRoot"
        }
    )
    resource_builder.put_integration_response(
        statusCode="302",
        selectionPattern="http.*",
        responseParameters={
            "method.response.header.Location": "integration.response.body.errorMessage"
        }
    )

def give_permission_to_call_lambda(boto_lambda_client, api_id):
    boto_lambda_client.add_permission(
        FunctionName="arn:aws:lambda:{}:{}:function:{}"
            .format(LAMBDA_REGION_NAME, ACCOUNT_ID, LAMBDA_FUNCTION_NAME),
        SourceArn="arn:aws:execute-api:{}:{}:{}/*"
            .format(API_REGION_NAME, ACCOUNT_ID, api_id),
        Principal="apigateway.amazonaws.com",
        StatementId=str(uuid.uuid1()),
        Action="lambda:InvokeFunction"
    )

if __name__ == "__main__":
    boto_api_client = boto3.client("apigateway", region_name=API_REGION_NAME)
    api_id = create_api(boto_api_client, API_NAME)
    add_get_integration(boto_api_client, api_id)
    add_post_integration(boto_api_client, api_id)

    boto_lambda_client = boto3.client("lambda", region_name=LAMBDA_REGION_NAME)
    give_permission_to_call_lambda(boto_lambda_client, api_id)
