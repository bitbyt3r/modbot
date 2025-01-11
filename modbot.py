import json

def main(event, context):
    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from my lambda!')
    }
