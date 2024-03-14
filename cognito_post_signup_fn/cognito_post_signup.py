import boto3
import os


def lambda_handler(event, context):
    # Extract the email address from the event data
    email = event['request']['userAttributes']['email']
    
    sns_topic_arn = os.environ['SNS_TOPIC_ARN']
    

    sns_client = boto3.client('sns')
    

    try:
        response = sns_client.subscribe(
            TopicArn=sns_topic_arn,
            Protocol='email',
            Endpoint=email,
            ReturnSubscriptionArn=True
        )
        subscription_arn = response['SubscriptionArn']
        print(f"Subscription successful. Subscription ARN: {subscription_arn}")
    except Exception as e:
        print(f"Failed to subscribe {email} to the SNS topic: {str(e)}")
        raise e
    return event
