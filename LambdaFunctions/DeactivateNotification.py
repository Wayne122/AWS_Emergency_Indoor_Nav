import json
import boto3
# import requests


def lambda_handler(event, context):
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """

    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('MobileUser')

        id = event['pathParameters']

        response = table.get_item(
            Key=id
        )

        if "Item" in response:
            userInfo = response["Item"]
            client = boto3.client('sns')

            client.unsubscribe(
                SubscriptionArn=userInfo['SubscriptionArn']
            )

            client.delete_endpoint(
                EndpointArn=userInfo['EndpointArn']
            )

            return {
                "statusCode": 200,
                "body": json.dumps({
                    "response": "Deactivated!",
                })
            }
        else:
            return {
                "statusCode": 404,
                "body": json.dumps({
                    "response": "User not found!"
                })
            }
    except:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "response": "Error(s) occurred.",
            }),
        }