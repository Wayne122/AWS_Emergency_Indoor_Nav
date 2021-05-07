import json
import boto3
import datetime
import uuid

dynamodb = boto3.resource('dynamodb')
client = boto3.client('sns')
table = dynamodb.Table('MobileUser-zspi2ti25naz3ksfjxkregagtm-dev')
subtable = dynamodb.Table('Subscription')


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
                userInfo = response["Item"]

                # Delete endpoint if already exist
                response = subtable.get_item(
                    Key=id
                )
                if "Item" in response:
                    unsubInfo = response["Item"]

                    client.unsubscribe(
                        SubscriptionArn=unsubInfo['SubscriptionArn']
                    )

                    client.delete_endpoint(
                        EndpointArn=unsubInfo['EndpointArn']
                    )

                    table.delete_item(
                        Key=id
                    )

                # Creation process
                # If token exists
                if 'deviceTokenId' in userInfo:
                    subInfo = id

                    # Create endpoint
                    response = client.create_platform_endpoint(
                        PlatformApplicationArn='arn:aws:sns:us-east-1:756906170378:app/APNS_SANDBOX/iOS_Emergency_Indoor_Nav',
                        Token=userInfo['deviceTokenId'].replace('-', ''), # Remove dash from fake token
                        CustomUserData=userInfo['id']
                    )

                    # If endpoint creation succeeded
                    if "EndpointArn" in response:
                        subInfo['EndpointArn'] = response['EndpointArn']

                        # Get all topics
                        topics = client.list_topics()
                        tlist = []
                        for topic in topics['Topics']:
                            if topic['TopicArn'].split(':')[-1].split('_')[0] == "SmartNavigationPushNotification":
                                tlist.append(topic['TopicArn'])
                        
                        # Find an usable topic
                        tArn = ""
                        for t in tlist:
                            r = client.get_topic_attributes(TopicArn=t)
                            if int(r['Attributes']['SubscriptionsConfirmed']) < 10000000:
                                tArn = t
                                break

                        # Create topic if no topic is found
                        if not tArn:
                            newTopic = client.create_topic(
                                Name='SmartNavigationPushNotification_' + str(len(tlist))
                            )
                            tArn = newTopic['TopicArn']

                        # Subscribe to a topic
                        response = client.subscribe(
                            TopicArn=tArn,
                            Protocol='application',
                            Endpoint=subInfo['EndpointArn'],
                            ReturnSubscriptionArn=True
                        )

                        # If topic subscription succeeded
                        if "SubscriptionArn" in response:
                            subInfo['SubscriptionArn'] = response['SubscriptionArn']

                            response = subtable.put_item(
                                Item=subInfo
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
                        "statusCode": 400,
                        "body": json.dumps({
                            "response": "No token found.",
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
        elif "Records" in event:
            records = event['Records']
            for r in records:
                if r['eventName'] == "INSERT":
                    userInfo = r['dynamodb']['NewImage']

                    # Delete endpoint if already exist
                    response = subtable.get_item(
                        Key={'id': userInfo['id']['S']}
                    )
                    if "Item" in response:
                        unsubInfo = response["Item"]

                        client.unsubscribe(
                            SubscriptionArn=unsubInfo['SubscriptionArn']
                        )

                        client.delete_endpoint(
                            EndpointArn=unsubInfo['EndpointArn']
                        )

                        subtable.delete_item(
                            Key={'id': userInfo['id']['S']}
                        )

                    # Creation process
                    # If token exists
                    if 'deviceTokenId' in userInfo:
                        subInfo = {'id': userInfo['id']['S']}

                        # Create endpoint
                        response = client.create_platform_endpoint(
                            PlatformApplicationArn='arn:aws:sns:us-east-1:756906170378:app/APNS_SANDBOX/iOS_Emergency_Indoor_Nav',
                            Token=userInfo['deviceTokenId']['S'].replace('-', ''), # Remove dash from fake token
                            CustomUserData=userInfo['id']['S']
                        )

                        # If endpoint creation succeeded
                        if "EndpointArn" in response:
                            subInfo['EndpointArn'] = response['EndpointArn']

                            # Get all topics
                            topics = client.list_topics()
                            tlist = []
                            for topic in topics['Topics']:
                                if topic['TopicArn'].split(':')[-1].split('_')[0] == "SmartNavigationPushNotification":
                                    tlist.append(topic['TopicArn'])
                            
                            # Find an usable topic
                            tArn = ""
                            for t in tlist:
                                r = client.get_topic_attributes(TopicArn=t)
                                if int(r['Attributes']['SubscriptionsConfirmed']) < 10000000:
                                    tArn = t
                                    break

                            # Create topic if no topic is found
                            if not tArn:
                                newTopic = client.create_topic(
                                    Name='SmartNavigationPushNotification_' + str(len(tlist)+1)
                                )
                                tArn = newTopic['TopicArn']

                            # Subscribe to a topic
                            response = client.subscribe(
                                TopicArn=tArn,
                                Protocol='application',
                                Endpoint=subInfo['EndpointArn'],
                                ReturnSubscriptionArn=True
                            )

                            # If topic subscription succeeded
                            if "SubscriptionArn" in response:
                                subInfo['SubscriptionArn'] = response['SubscriptionArn']

                                subtable.put_item(
                                    Item=subInfo
                                )

                elif r['eventName'] == "MODIFY":
                    newUserInfo = r['dynamodb']['NewImage']
                    oldUserInfo = r['dynamodb']['OldImage']

                    # Check if token is updated
                    if 'deviceTokenId' not in oldUserInfo and 'deviceTokenId' in newUserInfo or newUserInfo['deviceTokenId']['S'] != oldUserInfo['deviceTokenId']['S']:
                        # Delete old subscription
                        response = subtable.get_item(
                            Key={'id': newUserInfo['id']['S']}
                        )
                        if "Item" in response:
                            unsubInfo = response["Item"]

                            client.unsubscribe(
                                SubscriptionArn=unsubInfo['SubscriptionArn']
                            )

                            client.delete_endpoint(
                                EndpointArn=unsubInfo['EndpointArn']
                            )

                            subtable.delete_item(
                                Key={'id': newUserInfo['id']['S']}
                            )
                        
                        # Re-subscribe
                        subInfo = {'id': newUserInfo['id']['S']}

                        response = client.create_platform_endpoint(
                            PlatformApplicationArn='arn:aws:sns:us-east-1:756906170378:app/APNS_SANDBOX/iOS_Emergency_Indoor_Nav',
                            Token=newUserInfo['deviceTokenId']['S'].replace('-', ''), # Remove dash from fake token
                            CustomUserData=newUserInfo['id']['S']
                        )

                        if "EndpointArn" in response:
                            subInfo['EndpointArn'] = response['EndpointArn']

                            # Get all topics
                            topics = client.list_topics()
                            tlist = []
                            for topic in topics['Topics']:
                                if topic['TopicArn'].split(':')[-1].split('_')[0] == "SmartNavigationPushNotification":
                                    tlist.append(topic['TopicArn'])
                            
                            # Find an usable topic
                            tArn = ""
                            for t in tlist:
                                r = client.get_topic_attributes(TopicArn=t)
                                # If the topic has not reached subscription limit
                                if int(r['Attributes']['SubscriptionsConfirmed']) < 10000000:
                                    tArn = t
                                    break

                            # Create topic if no topic is found
                            if not tArn:
                                newTopic = client.create_topic(
                                    Name='SmartNavigationPushNotification_' + str(len(tlist)+1)
                                )
                                tArn = newTopic['TopicArn']

                            # Subscribe to a topic
                            response = client.subscribe(
                                TopicArn=tArn,
                                Protocol='application',
                                Endpoint=subInfo['EndpointArn'],
                                ReturnSubscriptionArn=True
                            )

                            # If topic subscription succeeded
                            if "SubscriptionArn" in response:
                                subInfo['SubscriptionArn'] = response['SubscriptionArn']

                                subtable.put_item(
                                    Item=subInfo
                                )
    except:
        with open('/tmp/error.log', 'w') as el:
            json.dump(event, el, indent=2)
        filename = "error_logs/" + datetime.datetime.today().strftime("%Y-%m-%dT%H%M%S-") + "ActivateNotification-" + str(uuid.uuid4()) + ".log"
        boto3.client('s3').upload_file('/tmp/error.log', 'smartnavigationcloudformationdeployment', filename)
        return {
            "statusCode": 400,
            "body": json.dumps({
                "response": "Error(s) occurred.",
            }),
        }