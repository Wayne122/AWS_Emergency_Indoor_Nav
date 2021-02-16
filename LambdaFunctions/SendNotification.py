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
        msg = json.loads(event['body'])
        client = boto3.client('sns')
        response = client.publish(
            TargetArn='arn:aws:sns:us-east-1:756906170378:app/APNS_SANDBOX/iOS_Emergency_Indoor_Nav',
            Message=msg['Message'],
            MessageStructure=msg['MessageStructure'],
            MessageAttributes=msg['MessageAttributes']
        )

        if "MessageId" in response:
            return {
                "statusCode": 200,
                "body": json.dumps({
                    #"response": response,
                    "response": "Sent!"
                }),
            }
        else:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    #"response": response,
                    "response": "Error(s) occurred."
                })
            }
    except:
        return {
            "statusCode": 400,
            "body": json.dumps({
                #"response": event,
                "response": "Error(s) occurred.",
            }),
        }