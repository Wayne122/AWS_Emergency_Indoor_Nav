import json
import boto3
import datetime
import uuid

client = boto3.client('sns')

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
        if "body" in event:
            msg = json.loads(event['body'])
        else:
            msg = event

        # Get all topics
        topics = client.list_topics()
        tlist = []
        for topic in topics['Topics']:
            if topic['TopicArn'].split(':')[-1].split('_')[0] == "SmartNavigationPushNotification":
                tlist.append(topic['TopicArn'])
        
        for t in tlist:
            r = client.publish(
                TargetArn=t,
                Message=json.dumps(msg['Message']),
                MessageStructure=msg['MessageStructure'],
                MessageAttributes=msg['MessageAttributes']
            )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "response": "Sent!"
            }),
        }
    except:
        with open('/tmp/error.log', 'w') as el:
            json.dump(event, el, indent=2)
        filename = "error_logs/" + datetime.datetime.today().strftime("%Y-%m-%dT%H%M%S-") + "SendNotification-" + str(uuid.uuid4()) + ".log"
        boto3.client('s3').upload_file('/tmp/error.log', 'smartnavigationcloudformationdeployment', filename)
        return {
            "statusCode": 400,
            "body": json.dumps({
                "response": "Error(s) occurred.",
                "detail": event
            })
        }