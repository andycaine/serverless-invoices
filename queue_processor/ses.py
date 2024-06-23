import dataclasses
import email.message
import logging

import boto3

ses = boto3.client('ses')
logger = logging.getLogger()


@dataclasses.dataclass
class Attachment:
    file: str
    name: str
    maintype: str
    subtype: str


def send_email(sender, recipients, subject, body, attachments=[]):
    msg = email.message.EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    msg.set_content(body)
    for attachment in attachments:
        with open(attachment.file, 'rb') as f:
            msg.add_attachment(
                f.read(),
                maintype=attachment.maintype,
                subtype=attachment.subtype,
                filename=attachment.name
            )
    response = ses.send_raw_email(
        Source=sender,
        Destinations=recipients,
        RawMessage={'Data': msg.as_string()}
    )
    logger.info(f"Email sent with message id {response['MessageId']}")
