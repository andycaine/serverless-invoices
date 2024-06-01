import boto3
import json

# invoice request SQS queue
queue_name = 'serverless-invoices-InvoiceRequestQueue-ruYtw2WmUmjZ'

# get the sqs resource
sqs = boto3.resource('sqs')

# create the invoice request
invoice_request = {
    'invoice_number': '9999',
    'invoice_date': '2024-05-01',
    'customer': {
        'name': 'Test Customer',
        'address': 'Address'
    },
    'line_items': [
        ['Name', 'Quantity', 'Unit Price', 'Total'],
        ['Foo Clip', '2', '£120.00', '£240.00'],
        ['Flux Capacitor', '1', '£1,234.00', '£1,234.00']
    ],
    'invoice_totals': [
        ['Subtotal', '£1,474'],
        ['VAT (%)', '20%'],
        ['Total VAT', '£284.80'],
        ['Balance', '£1,768.80']
    ]
}

# send the invoice request to the queue
queue = sqs.get_queue_by_name(QueueName=queue_name)
queue.send_message(MessageBody=json.dumps(invoice_request))
