from unittest.mock import patch
import json
import os

os.environ['INVOICE_BUCKET'] = 'test-bucket'
from queue_processor import app  # noqa: E402

app.config_dir = 'tests/config'


@patch('queue_processor.app.s3')
def test_queue_processor(mock_s3):
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

    event = {
        "Records": [
            {
                "messageId": "1",
                "body": json.dumps(invoice_request),
            }
        ]
    }
    result = app.handler(event, {})
    assert result["statusCode"] == 200
    mock_s3.upload_file.assert_called_once()
    args, kwargs = mock_s3.upload_file.call_args
    file_name, bucket, invoice_name = args
    assert file_name.startswith('/tmp/')
    assert bucket == 'test-bucket'
    assert invoice_name == '9999.pdf'
    assert kwargs == {
        'ExtraArgs': {'ContentType': 'application/pdf'}
    }
