import json
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('MobileUser-zspi2ti25naz3ksfjxkregagtm-dev')
subtable = dynamodb.Table('Subscription')
buildingtable = dynamodb.Table('Building-zspi2ti25naz3ksfjxkregagtm-dev')
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

                # Send push notifications to all relevant users
                for userInfo in userList:
                    # Get endpoint
                    response = subtable.get_item(
                        Key={'id': userInfo['id']}
                    )

                    # If endpoint exist
                    if "Item" in response:
                        if isinstance(paths[userInfo['location']]['shortestPath'], list):
                            msg = {
                                "Message": {
                                    "default": "default message",
                                    "APNS_SANDBOX": json.dumps({
                                        "aps": {
                                            "alert": {
                                                "title": "Emergency Alert: ",
                                                "body": "New instructions updated: Follow the instructions to exit the building"
                                            }
                                        },
                                        "shortestPath": json.dumps(paths[userInfo['location']])
                                    })
                                },
                                "MessageStructure": "json"
                            }
                        else:
                            msg = {
                                "Message": {
                                    "default": "default message",
                                    "APNS_SANDBOX": json.dumps({
                                        "aps": {
                                            "alert": {
                                                "title": "Emergency Alert: ",
                                                "body": "New instructions updated: No safe path found, click for more detail."
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
                if r['eventName'] == "INSERT" or r['eventName'] == "MODIFY":
                    edgeInfo = r['dynamodb']['NewImage']
                else:
                    edgeInfo = r['dynamodb']['OldImage']

                buildingInfo = buildingtable.get_item(
                    Key={"id": edgeInfo['buildingId']['S']}
                )

                # If building is found and in emergency
                if "Item" in buildingInfo and buildingInfo["Item"]['isInEmergency']:
                    buildingId = buildingInfo["Item"]['id']

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

                        # Send push notifications to all relevant users
                        for userInfo in userList:
                            # Get endpoint
                            response = subtable.get_item(
                                Key={'id': userInfo['id']}
                            )

                            # If endpoint exist
                            if "Item" in response:
                                if isinstance(paths[userInfo['location']]['shortestPath'], list):
                                    msg = {
                                        "Message": {
                                            "default": "default message",
                                            "APNS_SANDBOX": json.dumps({
                                                "aps": {
                                                    "alert": {
                                                        "title": "Emergency Alert: " + buildingInfo["Item"]['emergencyDescription'],
                                                        "body": "New instructions updated: Follow the instructions to exit the building"
                                                    }
                                                },
                                                "shortestPath": json.dumps(paths[userInfo['location']])
                                            })
                                        },
                                        "MessageStructure": "json"
                                    }
                                else:
                                    msg = {
                                        "Message": {
                                            "default": "default message",
                                            "APNS_SANDBOX": json.dumps({
                                                "aps": {
                                                    "alert": {
                                                        "title": "Emergency Alert: " + buildingInfo["Item"]['emergencyDescription'],
                                                        "body": "New instructions updated: No safe path found, click for more detail."
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