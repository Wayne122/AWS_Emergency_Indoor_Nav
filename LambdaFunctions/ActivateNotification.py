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
        info = json.loads(event['body'])
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('MobileUser')

        id = info['userId']

        response = table.get_item(
            Key={'userId': id}
        )

        if "Item" in response:
            userInfo = response["Item"]
            client = boto3.client('sns')

            response = client.create_platform_endpoint(
                PlatformApplicationArn='arn:aws:sns:us-east-1:756906170378:app/APNS_SANDBOX/iOS_Emergency_Indoor_Nav',
                Token=userInfo['deviceTokenId'],
                CustomUserData=id
            )

            if "EndpointArn" in response:
                userInfo['EndpointArn'] = response['EndpointArn']
                response = client.subscribe(
                    TopicArn=info['TopicArn'],
                    Protocol='application',
                    Endpoint=userInfo['EndpointArn'],
                    ReturnSubscriptionArn=True
                )

                if "SubscriptionArn" in response:
                    userInfo['SubscriptionArn'] = response['SubscriptionArn']

                    response = table.put_item(
                        Item=userInfo
                    )

                    return {
                        "statusCode": 200,
                        "body": json.dumps({
                            #"detail": token,
                            "response": "Activated!"
                        }),
                    }
                else:
                    return {
                        "statusCode": 400,
                        "body": json.dumps({
                            "response": "Subscription unsuccessful.",
                        }),
                    }
            else:
                return {
                    "statusCode": 400,
                    "body": json.dumps({
                        "response": "Endpoint creation unsuccessful.",
                    }),
                }
        else:
            return {
                "statusCode": 404,
                "body": json.dumps({
                    #"response": response,
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