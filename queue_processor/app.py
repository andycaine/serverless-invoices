import json
import logging
import os
import tempfile

import boto3
import invoicely
import yaml

from . import ses


logger = logging.getLogger()
logger.setLevel(logging.INFO)
config_dir = '/opt/python'
s3 = boto3.client('s3')
invoice_bucket = os.environ['INVOICE_BUCKET']


def load_config():
    with open(f'{config_dir}/config.yaml') as f:
        return yaml.safe_load(f)


def process_message(message, provider, logo, line_item_col_widths,
                    email_from_address, email_subject, email_body):
    try:
        data = json.loads(message)
        customer = invoicely.Customer(**data['customer'])
        invoice_number = data['invoice_number']
        line_items = data['line_items']
        invoice_date = data['invoice_date']
        invoice_totals = data['invoice_totals']
        notification_addresses = data['notification_addresses']
    except (json.JSONDecodeError, KeyError, TypeError):
        logger.info(f'Skipping message due to invalid JSON: {message}')
        return

    with tempfile.NamedTemporaryFile(dir='/tmp') as f:
        invoicely.invoice(
            filename=f.name,
            provider=provider,
            customer=customer,
            logo=logo,
            line_item_col_widths=line_item_col_widths,
            line_items=line_items,
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            invoice_totals=invoice_totals
        )
        f.flush()
        s3.upload_file(
            f.name,
            invoice_bucket,
            f'{invoice_number}.pdf',
            ExtraArgs={'ContentType': 'application/pdf'}
        )
        ses.send_email(
            sender=email_from_address,
            recipients=notification_addresses,
            subject=email_subject,
            body=email_body,
            attachments=[ses.Attachment(
                file=f.name,
                name=f'{invoice_number}.pdf',
                maintype='application',
                subtype='pdf'
            )]
        )


def handler(event, _):
    config = load_config()
    email_from_address = config['email_from_address']
    email_subject = config['email_subject']
    email_body = config['email_body']
    provider = invoicely.Provider(**config['provider'])
    line_item_col_widths = config['line_item_col_widths']
    logo_config = config['logo']
    logo = invoicely.Logo(
        path=f"{config_dir}/{logo_config['filename']}",
        width=logo_config['width'],
        height=logo_config['height']
    )

    for record in event['Records']:
        logger.info(f'Processing message {record["messageId"]}')
        message = record['body']
        process_message(message, provider, logo, line_item_col_widths,
                        email_from_address, email_subject, email_body)

    return {
        'statusCode': 200,
        'body': ''
    }
