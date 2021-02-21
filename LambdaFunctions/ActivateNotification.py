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
        table = dynamodb.Table('MobileUser-zspi2ti25naz3ksfjxkregagtm-dev')
        subtable = dynamodb.Table('Subscription')

        if "pathParameters" in event:
            id = event['pathParameters']

            response = table.get_item(
                Key=id
            )

            if "Item" in response:
                userInfo = response["Item"]
                client = boto3.client('sns')
                subInfo = {'id': userInfo['id']}

                response = client.create_platform_endpoint(
                    PlatformApplicationArn='arn:aws:sns:us-east-1:756906170378:app/APNS_SANDBOX/iOS_Emergency_Indoor_Nav',
                    Token=userInfo['deviceTokenId'],
                    CustomUserData=userInfo['id']
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
                        if int(r['Attributes']['SubscriptionsConfirmed']) < 10000000:
                            tArn = t
                            break

                    # Create topic if no topic is found
                    if not tArn:
                        newTopic = client.create_topic(
                            Name='SmartNavigationPushNotification_' + str(len(tlist))
                        )
                        tArn = newTopic['TopicArn']
                    
                    response = client.subscribe(
                        TopicArn=tArn,
                        Protocol='application',
                        Endpoint=subInfo['EndpointArn'],
                        ReturnSubscriptionArn=True
                    )

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
                    client = boto3.client('sns')
                    subInfo = {'id': userInfo['id']['S']}

                    response = client.create_platform_endpoint(
                        PlatformApplicationArn='arn:aws:sns:us-east-1:756906170378:app/APNS_SANDBOX/iOS_Emergency_Indoor_Nav',
                        Token=userInfo['deviceTokenId']['S'],
                        CustomUserData=userInfo['id']['S']
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
                            if int(r['Attributes']['SubscriptionsConfirmed']) < 10000000:
                                tArn = t
                                break

                        # Create topic if no topic is found
                        if not tArn:
                            newTopic = client.create_topic(
                                Name='SmartNavigationPushNotification_' + str(len(tlist)+1)
                            )
                            tArn = newTopic['TopicArn']

                        response = client.subscribe(
                            TopicArn=tArn,
                            Protocol='application',
                            Endpoint=subInfo['EndpointArn'],
                            ReturnSubscriptionArn=True
                        )

                        if "SubscriptionArn" in response:
                            subInfo['SubscriptionArn'] = response['SubscriptionArn']

                            subtable.put_item(
                                Item=subInfo
                            )
    except:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "response": "Error(s) occurred.",
            }),
        }