import json
import boto3
import urllib3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('MobileUser-zspi2ti25naz3ksfjxkregagtm-dev')
pathTable = dynamodb.Table('Directions')
lc = boto3.client('lambda')

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
        id = event['pathParameters']

        response = table.get_item(
            Key=id
        )

        if "Item" in response:
            # Send information to path finding instance
            userInfo = response['Item']

            # Get shortest path
            response = lc.invoke(FunctionName = 'GetShortestPathFunction', Payload=json.dumps(userInfo['location']))
            sp = json.load(response['Payload'])['body']

            pathTable.put_item(
                Item={"directionsId": id['id'], "path": sp}
            )

            # Send push notification
            http = urllib3.PoolManager()
            data = {
                "Message": {
                    "default": sp
                },
                "MessageStructure": "json",
                "MessageAttributes": {
                    "msgattr": {
                        "DataType": "String",
                        "StringValue": "attribute here"
                    }
                }
            }

            r = http.request(
                'POST',
                'https://hza50oxgik.execute-api.us-east-1.amazonaws.com/Prod/SendNotification',
                body=json.dumps(data).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )

            return {
                "statusCode": 200,
                "body": json.dumps({
                    #"detail": json.loads(r.data.decode('utf-8')),
                    "response": "Sent!"
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
                #"detail": event
            }),
        }