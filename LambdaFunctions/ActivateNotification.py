import json
import boto3
import datetime
import uuid

dynamodb = boto3.resource('dynamodb')
client = boto3.client('sns')
table = dynamodb.Table('MobileUser-zspi2ti25naz3ksfjxkregagtm-dev')
subtable = dynamodb.Table('Subscription')

# for logging
s3 = boto3.client('s3')


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

    el = open('/tmp/error.log', 'w')
    try:
        if "pathParameters" in event:
            el.write("Triggered by API...\n")
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
                        Token=userInfo['deviceTokenId'],
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
            el.write("Triggered by table trigger...\n")
            records = event['Records']
            for r in records:
                el.write("  Looping records...\n")
                if r['eventName'] == "INSERT":
                    el.write("    Inserting new record...\n")
                    userInfo = r['dynamodb']['NewImage']

                    # Delete endpoint if already exist
                    el.write("    Looking for old endpoints...\n")
                    response = subtable.get_item(
                        Key={'id': userInfo['id']['S']}
                    )
                    if "Item" in response:
                        el.write("      Endpoint exists, deleting...\n")
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
                    el.write("    Looking for token...\n")
                    if 'deviceTokenId' in userInfo:
                        el.write("      Token exists, creating endpoint...\n")
                        subInfo = {'id': userInfo['id']['S']}

                        # Create endpoint
                        response = client.create_platform_endpoint(
                            PlatformApplicationArn='arn:aws:sns:us-east-1:756906170378:app/APNS_SANDBOX/iOS_Emergency_Indoor_Nav',
                            Token=userInfo['deviceTokenId']['S'],
                            CustomUserData=userInfo['id']['S']
                        )

                        # If endpoint creation succeeded
                        if "EndpointArn" in response:
                            el.write("        Endpoint created successfully...\n")
                            subInfo['EndpointArn'] = response['EndpointArn']

                            # Get all topics
                            el.write("        Getting topics...\n")
                            topics = client.list_topics()
                            tlist = []
                            for topic in topics['Topics']:
                                if topic['TopicArn'].split(':')[-1].split('_')[0] == "SmartNavigationPushNotification":
                                    tlist.append(topic['TopicArn'])
                            
                            # Find an usable topic
                            el.write("        Looking for usable topic...\n")
                            tArn = ""
                            for t in tlist:
                                r = client.get_topic_attributes(TopicArn=t)
                                if int(r['Attributes']['SubscriptionsConfirmed']) < 10000000:
                                    tArn = t
                                    break

                            # Create topic if no topic is found
                            if not tArn:
                                el.write("          Usable topic not found, creating...\n")
                                newTopic = client.create_topic(
                                    Name='SmartNavigationPushNotification_' + str(len(tlist)+1)
                                )
                                tArn = newTopic['TopicArn']

                            # Subscribe to a topic
                            el.write("        Subscribing to the topic...\n")
                            response = client.subscribe(
                                TopicArn=tArn,
                                Protocol='application',
                                Endpoint=subInfo['EndpointArn'],
                                ReturnSubscriptionArn=True
                            )

                            # If topic subscription succeeded
                            if "SubscriptionArn" in response:
                                el.write("          Subscription succesful...\n")
                                subInfo['SubscriptionArn'] = response['SubscriptionArn']

                                subtable.put_item(
                                    Item=subInfo
                                )
                            
                    el.write("    Done inserting new record...\n")
                elif r['eventName'] == "MODIFY":
                    el.write("    Modifying old record...\n")
                    newUserInfo = r['dynamodb']['NewImage']
                    oldUserInfo = r['dynamodb']['OldImage']

                    # Check if token is updated
                    el.write("    Checking if token got changed...\n")
                    if 'deviceTokenId' not in oldUserInfo and 'deviceTokenId' in newUserInfo or newUserInfo['deviceTokenId']['S'] != oldUserInfo['deviceTokenId']['S']:
                        # Delete old subscription
                        el.write("      Token changed, looking for old endpoints...\n")
                        response = subtable.get_item(
                            Key={'id': newUserInfo['id']['S']}
                        )
                        if "Item" in response:
                            el.write("        Endpoint exists, deleting...\n")
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
                        el.write("      Creating new endpoint...\n")
                        subInfo = {'id': newUserInfo['id']['S']}

                        response = client.create_platform_endpoint(
                            PlatformApplicationArn='arn:aws:sns:us-east-1:756906170378:app/APNS_SANDBOX/iOS_Emergency_Indoor_Nav',
                            Token=newUserInfo['deviceTokenId']['S'],
                            CustomUserData=newUserInfo['id']['S']
                        )

                        if "EndpointArn" in response:
                            el.write("        Endpoint created successfully...\n")
                            subInfo['EndpointArn'] = response['EndpointArn']

                            # Get all topics
                            el.write("        Getting topics...\n")
                            topics = client.list_topics()
                            tlist = []
                            for topic in topics['Topics']:
                                if topic['TopicArn'].split(':')[-1].split('_')[0] == "SmartNavigationPushNotification":
                                    tlist.append(topic['TopicArn'])
                            
                            # Find an usable topic
                            el.write("        Looking for usable topic...\n")
                            tArn = ""
                            for t in tlist:
                                r = client.get_topic_attributes(TopicArn=t)
                                # If the topic has not reached subscription limit
                                if int(r['Attributes']['SubscriptionsConfirmed']) < 10000000:
                                    tArn = t
                                    break

                            # Create topic if no topic is found
                            if not tArn:
                                el.write("          Usable topic not found, creating...\n")
                                newTopic = client.create_topic(
                                    Name='SmartNavigationPushNotification_' + str(len(tlist)+1)
                                )
                                tArn = newTopic['TopicArn']

                            # Subscribe to a topic
                            el.write("        Subscribing to the topic...\n")
                            response = client.subscribe(
                                TopicArn=tArn,
                                Protocol='application',
                                Endpoint=subInfo['EndpointArn'],
                                ReturnSubscriptionArn=True
                            )

                            # If topic subscription succeeded
                            if "SubscriptionArn" in response:
                                el.write("          Subscription succesful...\n")
                                subInfo['SubscriptionArn'] = response['SubscriptionArn']

                                subtable.put_item(
                                    Item=subInfo
                                )
                    el.write("    Done modifying old record...\n")
                else:
                    el.write("    Ignoring deletion...\n")
            el.write("Ending function...\n")
    except:
        el.write("ERROR OCCURED!\n\n")
        json.dump(event, el, indent=2)
        el.close()
        filename = "error_logs/" + datetime.datetime.today().strftime("%Y-%m-%dT%H%M%S-") + "ActivateNotification-" + str(uuid.uuid4()) + ".log"
        s3.upload_file('/tmp/error.log', 'smartnavigationcloudformationdeployment', filename)
        return {
            "statusCode": 400,
            "body": json.dumps({
                "response": "Error(s) occurred.",
            }),
        }