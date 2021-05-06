import json
import boto3
import datetime
import uuid

dynamodb = boto3.resource('dynamodb')
client = boto3.client('sns')
table = dynamodb.Table('Subscription')


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
        if "pathParameters" in event:
            id = event['pathParameters']

            response = table.get_item(
                Key=id
            )

            if "Item" in response:
                subInfo = response["Item"]

                client.unsubscribe(
                    SubscriptionArn=subInfo['SubscriptionArn']
                )

                client.delete_endpoint(
                    EndpointArn=subInfo['EndpointArn']
                )

                table.delete_item(
                    Key=id
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
        elif "Records" in event:
            records = event['Records']
            for r in records:
                if r['eventName'] == "REMOVE":
                    response = table.get_item(Key={'id': r['dynamodb']['OldImage']['id']['S']})
                    if "Item" in response:
                        subInfo = response["Item"]

                        client.unsubscribe(
                            SubscriptionArn=subInfo['SubscriptionArn']
                        )

                        client.delete_endpoint(
                            EndpointArn=subInfo['EndpointArn']
                        )

                        table.delete_item(
                            Key={'id': r['dynamodb']['OldImage']['id']['S']}
                        )
    except:
        with open('/tmp/error.log', 'w') as el:
            json.dump(event, el, indent=2)
        filename = "error_logs/" + datetime.datetime.today().strftime("%Y-%m-%dT%H%M%S-") + "DeactivateNotification-" + str(uuid.uuid4()) + ".log"
        boto3.client('s3').upload_file('/tmp/error.log', 'smartnavigationcloudformationdeployment', filename)
        return {
            "statusCode": 400,
            "body": json.dumps({
                "response": "Error(s) occurred.",
            }),
        }