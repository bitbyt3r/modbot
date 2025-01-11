import json
import requests
import boto3

from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler

app = App()

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
    
@app.action("approve")
def approve(ack, client, body):
    ack()
    key = body['message']['blocks'][1]['elements'][0]['value']
    url = body['message']['blocks'][0]['image_url']
    print(f"Approving {key}")
    print(body)
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
                "text": "Approved"
            }
        }
    ]
    client.chat_update(channel=body['channel']['id'], ts=body['message']['ts'], blocks=blocks, text=f"Approved by {body['user']['name']}")

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
                "text": "Rejected"
            }
        }
    ]
    client.chat_update(channel=body['channel']['id'], ts=body['message']['ts'], blocks=blocks, text=f"Rejected by {body['user']['name']}")

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