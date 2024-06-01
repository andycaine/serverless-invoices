import base64
import logging
import os
import re

import boto3
import botocore

s3 = boto3.client('s3')
logger = logging.getLogger()
logger.setLevel('INFO')
invoice_bucket = os.environ['INVOICE_BUCKET']


def handler(event, _):
    logger.info(event)
    try:
        method = event['requestContext']['http']['method']
        if method != 'GET':
            return {
                "statusCode": 405,
                "headers": {
                    "Content-Type": "text/plain"
                },
                "body": "Method not allowed"
            }

        invoice_name = event['pathParameters']['invoice_id']
        if not invoice_name:
            return {
                "statusCode": 404,
                "headers": {
                    "Content-Type": "text/plain"
                },
                "body": ""
            }
        if not re.match(r'^[a-zA-Z0-9-]+[.]pdf$', invoice_name):
            logger.info(f'Invalid invoice name: {invoice_name}')
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "text/plain"
                },
                "body": "Invalid invoice name"
            }

        response = s3.get_object(Bucket=invoice_bucket, Key=invoice_name)
        logger.info(response)
        obj = response['Body'].read()

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/pdf",
                "Content-Disposition": "inline",
                "Cache-Control": ("max-age=0, no-cache, no-store, "
                                  "must-revalidate, private")
            },
            "body": base64.b64encode(obj).decode('utf-8'),
            "isBase64Encoded": True
        }

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            logger.info('Invoice not found')
            return {
                "statusCode": 404,
                "headers": {
                    "Content-Type": "text/plain"
                },
                "body": "Not found"
            }
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "text/plain"
            },
            "body": ""
        }
