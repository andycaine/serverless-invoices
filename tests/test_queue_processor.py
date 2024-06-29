from unittest.mock import patch
import json
import sys

import pytest


@pytest.fixture
def envvars(monkeypatch):
    monkeypatch.setenv('INVOICE_BUCKET', 'test-bucket')


@pytest.fixture
def mock_s3(lambda_path):
    with patch('app.s3') as mock_s3:
        yield mock_s3


@pytest.fixture
def mock_ses(lambda_path):
    with patch('ses.ses') as mock_ses:
        yield mock_ses


@pytest.fixture
def lambda_path():
    path = 'queue_processor'
    if path not in sys.path:
        sys.path.insert(0, path)
    yield path


@pytest.fixture
def app(envvars, mock_s3, mock_ses):
    path = 'queue_processor'
    if path not in sys.path:
        sys.path.insert(0, path)
    import app
    app.config_dir = 'tests/config'
    yield app


def test_queue_processor(app, mock_s3, mock_ses):
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
        ],
        'notification_addresses': [
            'test@example.com'
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

    mock_ses.send_raw_email.assert_called_once()
    _, kwargs = mock_ses.send_raw_email.call_args
    assert kwargs['Source'] == 'invoices@example.com'
    assert kwargs['Destinations'] == ['test@example.com']


def test_invalid_json(app):
    event = {
        "Records": [
            {
                "messageId": "1",
                "body": "not a json",
            }
        ]
    }
    result = app.handler(event, {})
    assert result["statusCode"] == 200


def test_missing_fields(app):
    event = {
        "Records": [
            {
                "messageId": "1",
                "body": json.dumps({}),
            }
        ]
    }
    result = app.handler(event, {})
    assert result["statusCode"] == 200
