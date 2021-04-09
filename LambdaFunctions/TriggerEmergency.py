import json
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('MobileUser-zspi2ti25naz3ksfjxkregagtm-dev')
subtable = dynamodb.Table('Subscription')
# pathTable = dynamodb.Table('Directions')
# testTable = dynamodb.Table('Subscription')
lc = boto3.client('lambda')
snsc = boto3.client('sns')

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

            test_counter = 0

            # Get all relevant users
            response = table.query(
                IndexName='byBuilding',
                KeyConditionExpression=Key('buildingId').eq(id['id'])
            )

            # if there's any user
            if response['Items']:
                userList = response["Items"]

                # list[locationId]
                locations = []

                # Get all locations
                for userInfo in userList:
                    locations.append(userInfo['location'])

                # Remove duplicates
                locations = list(set(locations))

                # dict{locationId: Path}
                paths = {}

                # Get shortest path for all relevant locations
                for l in locations:
                    response = lc.invoke(FunctionName = 'GetShortestPathFromMap', Payload=json.dumps({'start_node':l}))
                    paths[l] = json.load(response['Payload'])
                    # pathTable.put_item(
                    #     Item={"directionsId": l, "path": paths[l]}
                    # )

                # Send push notifications to all relevant users
                for userInfo in userList:
                    # Get endpoint
                    response = subtable.get_item(
                        Key={'id': userInfo['id']}
                    )

                    # If endpoint exist
                    if "Item" in response:
                        msg = {
                            "Message": {
                                "default": "default message",
                                "APNS_SANDBOX": json.dumps({
                                    "aps": {
                                        "alert": {
                                            "title": "Emergency Alert",
                                            "body": "Follow the instructions to exit the building"
                                        }
                                    },
                                    "shortestPath": json.dumps(paths[userInfo['location']])
                                })
                            },
                            "MessageStructure": "json"
                        }
                        try:
                            snsc.publish(
                                TargetArn=response['Item']['EndpointArn'],
                                Message=json.dumps(msg['Message']),
                                MessageStructure=msg['MessageStructure']
                            )
                            test_counter += 1
                        except:
                            pass

                return {
                    "statusCode": 200,
                    "body": json.dumps({
                        #"detail": json.load(response['Payload'])['body'],
                        "msg count": test_counter,
                        "response": "Sent!"
                    }),
                }
            else:
                return {
                    "statusCode": 404,
                    "body": json.dumps({
                        #"response": response,
                        "response": "No user is found!"
                    })
                }
        elif "Records" in event:
            records = event['Records']
            for r in records:
                # testTable.put_item(
                #     Item={"id": "test", "detail": json.dumps(r)}
                # )

                # return

                if r['eventName'] == "INSERT" or r['eventName'] == "MODIFY":
                    buildingInfo = r['dynamodb']['NewImage']

                    if buildingInfo['isInEmergency']['BOOL']:
                        buildingId = buildingInfo['id']['S']

                        # test_counter = 0

                        # Get all relevant users
                        response = table.query(
                            IndexName='byBuilding',
                            KeyConditionExpression=Key('buildingId').eq(buildingId)
                        )

                        # if there's any user
                        if response['Items']:
                            userList = response["Items"]

                            # list[locationId]
                            locations = []

                            # Get all locations
                            for userInfo in userList:
                                locations.append(userInfo['location'])

                            # Remove duplicates
                            locations = list(set(locations))

                            # dict{locationId: Path}
                            paths = {}

                            # Get shortest path for all relevant locations
                            for l in locations:
                                response = lc.invoke(FunctionName = 'GetShortestPathFromMap', Payload=json.dumps({'start_node':l}))
                                paths[l] = json.load(response['Payload'])
                                # pathTable.put_item(
                                #     Item={"directionsId": l, "path": paths[l]}
                                # )

                            # Send push notifications to all relevant users
                            for userInfo in userList:
                                # Get endpoint
                                response = subtable.get_item(
                                    Key={'id': userInfo['id']}
                                )

                                # If endpoint exist
                                if "Item" in response:
                                    msg = {
                                        "Message": {
                                            "default": "default message",
                                            "APNS_SANDBOX": json.dumps({
                                                "aps": {
                                                    "alert": {
                                                        "title": "Emergency Alert: " + buildingInfo['emergencyDescription']['S'],
                                                        "body": "Follow the instructions to exit the building"
                                                    }
                                                },
                                                "shortestPath": json.dumps(paths[userInfo['location']])
                                            })
                                        },
                                        "MessageStructure": "json"
                                    }
                                    try:
                                        snsc.publish(
                                            TargetArn=response['Item']['EndpointArn'],
                                            Message=json.dumps(msg['Message']),
                                            MessageStructure=msg['MessageStructure']
                                        )
                                        # test_counter += 1
                                    except:
                                        pass
    except:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "response": "Error(s) occurred.",
                #"detail": event
            }),
        }