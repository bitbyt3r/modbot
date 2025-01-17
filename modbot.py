import json
import requests
import traceback
import boto3

from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler

app = App(process_before_response=True)

def post_image(bucket, key):
    url = f"https://{bucket}.s3.us-east-1.amazonaws.com/{key}"
    blocks = [
        {
            "type": "image",
            "image_url": url,
            "alt_text": "Unmoderated image"
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Approve",
                        "emoji": True
                    },
                    "value": key,
                    "action_id": "approve"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Reject",
                        "emoji": True
                    },
                    "value": key,
                    "action_id": "reject"
                }
            ]
        }
    ]
    app.client.chat_postMessage(
        channel="#super-jumbobot",
        text="Image to moderate",
        blocks=blocks
    )
    
    
def approve(ack, client, body):
    ack()
    key = body['message']['blocks'][1]['elements'][0]['value']
    url = body['message']['blocks'][0]['image_url']
    print(f"Approving {key}")
    blocks = [
        {
            "type": "image",
            "image_url": url,
            "alt_text": f"Approved by {body['user']['name']}"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Approved by {body['user']['name']}"
            }
        }
    ]
    client.chat_update(channel=body['channel']['id'], ts=body['message']['ts'], blocks=blocks, text=f"Approved by {body['user']['name']}")
    print(f"Replied for {key}")

def copy_image(body):
    key = body['message']['blocks'][1]['elements'][0]['value']
    copy_source = {
        'Bucket': 'giffinator-uncensored',
        'Key': key
    }
    print(f"About to copy {key}", copy_source)
    s3 = boto3.resource('s3')
    s3.meta.client.copy(copy_source, 'giffinator-approved', key)
    print(f"Finished copying {key}")

app.action("approve")(ack=approve, lazy=[copy_image])

@app.action("reject")
def reject(ack, client, body):
    ack()
    key = body['message']['blocks'][1]['elements'][0]['value']
    url = body['message']['blocks'][0]['image_url']
    print(f"Rejecting {key}")
    blocks = [
        {
            "type": "image",
            "image_url": url,
            "alt_text": f"Rejected by {body['user']['name']}"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Rejected by {body['user']['name']}"
            }
        }
    ]
    client.chat_update(channel=body['channel']['id'], ts=body['message']['ts'], blocks=blocks, text=f"Rejected by {body['user']['name']}")
    print(f"Replied for {key}")

def main(event, context):
    if "Records" in event:
        for record in event['Records']:
            bucket = record.get("s3", {}).get("bucket", {}).get("name", "giffinator-uncensored")
            key = record.get("s3", {}).get("object", {}).get("key", None)
            if key and bucket:
                post_image(bucket, key)
    else:
        slack_handler = SlackRequestHandler(app=app)
        return slack_handler.handle(event, context)