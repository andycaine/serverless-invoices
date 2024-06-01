from unittest.mock import patch
import base64
import os
import io

import botocore.exceptions

os.environ['INVOICE_BUCKET'] = 'test-bucket'
from get_invoice import app  # noqa: E402


def event(invoice_id):
    return {
        'pathParameters': {
            'invoice_id': invoice_id
        },
        'requestContext': {
            'http': {
                'method': 'GET'
            }
        }
    }


@patch('get_invoice.app.s3')
def test_get_invoice(mock_s3):
    mock_s3.get_object.return_value = {
        'Body': io.BytesIO(b'Hello World')
    }

    response = app.handler(event('9999.pdf'), {})
    assert response == {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/pdf',
            'Content-Disposition': 'inline',
            'Cache-Control': ('max-age=0, no-cache, no-store, '
                              'must-revalidate, private')
        },
        'body': base64.b64encode(b'Hello World').decode('utf-8'),
        'isBase64Encoded': True
    }


def test_get_invoice_invalid_invoice_number():
    response = app.handler(event('..as'), {})
    assert response == {
        'statusCode': 400,
        'headers': {
            'Content-Type': 'text/plain',
        },
        'body': 'Invalid invoice name'
    }


def test_get_invoice_no_invoice_number():
    response = app.handler(event(''), {})
    assert response == {
        'statusCode': 404,
        'headers': {
            'Content-Type': 'text/plain',
        },
        'body': ''
    }


@patch('get_invoice.app.s3')
def test_get_invoice_not_found(mock_s3):
    error_response = {
        'Error': {
            'Code': 'NoSuchKey'
        }
    }
    error = botocore.exceptions.ClientError(error_response=error_response,
                                            operation_name='')
    mock_s3.get_object.side_effect = error
    response = app.handler(event('9999.pdf'), {})
    assert response == {
        'statusCode': 404,
        'headers': {
            'Content-Type': 'text/plain',
        },
        'body': 'Not found'
    }
