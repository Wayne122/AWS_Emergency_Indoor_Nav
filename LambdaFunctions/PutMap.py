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

        table = dynamodb.Table('Map')

        body = event['body']

        entity = json.loads(body)

        id = entity['mapId']

        response = table.get_item(
            Key={'mapId': id}
        )

        if "Item" in response:
            response = table.put_item(
                Item=entity
            )

            return {
                "statusCode": 200,
                "body": json.dumps({
                    #"response": response,
                    "response": "Replaced!"
                }),
            }
        else:
            return {
                "statusCode": 404,
                "body": json.dumps({
                    "response": "Record not found!"
                })
            }
    except:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "response": "Error(s) occurred.",
            }),
        }