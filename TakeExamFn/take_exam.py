import json
import boto3
import os
# Initialize S3 client outside of handler
s3_client = boto3.client('s3')

def get_object(bucket_name, object_key):
    """
    Retrieve an object from S3.

    :param bucket_name: Name of the S3 bucket.
    :param object_key: Key of the object to retrieve.
    :return: The object's content if the object is found. Otherwise, an error message.
    """
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        content = response['Body'].read().decode('utf-8')  # Decoding from bytes to string
        return content  # Return the raw string content
    except Exception as e:
        return {
                    'statusCode': 500,
                    'body': json.dumps({'error': str(e)})
                }

def list_bucket_objects(bucket_name, prefix):
    """
    List objects in an S3 bucket with the specified prefix.

    :param bucket_name: Name of the S3 bucket.
    :param prefix: Prefix of the object keys to list.
    :return: List of object keys, excluding the prefix itself.
    """
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        objects = []
        if 'Contents' in response:
            for obj in response['Contents']:
                if obj['Key'] != prefix:  # Exclude the directory name itself
                    objects.append(obj['Key'].replace(prefix, ''))  # Remove the prefix
        return objects
    except Exception as e:
        return {
                    'statusCode': 500,
                    'body': json.dumps({'error': str(e)})
                }

def lambda_handler(event, context):
    """
    Main Lambda function handler.

    :param event: AWS Lambda uses this parameter to pass in event data to the handler.
    :param context: AWS Lambda uses this parameter to provide runtime information to your handler.
    :return: Appropriate HTTP response.
    """
    #bucket = 'exam-gen'  # specify your bucket name
    bucket = os.environ['BUCKET_NAME']
    prefix = 'questions_bank/'  # specify your folder if any

    params = event.get('queryStringParameters')
    if params:
        object_name = params.get('object_name')

        if object_name:
            full_object_key = prefix + object_name
            get_response = get_object(bucket, full_object_key)
            
            # Return the raw string content, setting the appropriate content type
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'  # for CORS
                },
                'body': get_response  # This is the raw string, not re-encoded as JSON
            }

    # If there's no object_name in the parameters, list the objects
    list_response = list_bucket_objects(bucket, prefix)

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'  # for CORS
        },
        'body': json.dumps(list_response)  # List of files, excluding the prefix
    }