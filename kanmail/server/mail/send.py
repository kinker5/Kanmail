from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from kanmail.log import logger

from .contacts import get_contacts
from .util import markdownify


def _make_address(obj):
    if isinstance(obj, (tuple, list)):
        return '{0} <{1}>'.format(*obj)
    else:
        contacts = get_contacts()
        if obj in contacts:
            return _make_address((contacts[obj], obj))
    return obj


def _ensure_multiple(item):
    if item is None:
        return ()

    if not isinstance(item, (tuple, list)):
        return (item,)

    return item


def send_email(
    smtp_connection,
    from_,
    to=None, cc=None, bcc=None,
    subject=None, text=None, html=None,
    # If replying to another message
    reply_to_message_id=None,
    reply_to_message_references=None,
    reply_to_html=None,
):
    text = text or ''

    to = _ensure_multiple(to)
    cc = _ensure_multiple(cc)
    bcc = _ensure_multiple(bcc)

    to_addresses = to + cc + bcc

    message = MIMEMultipart('alternative')

    message['From'] = _make_address(from_)
    message['To'] = ', '.join(_make_address(a) for a in to)

    if cc:
        message['Cc'] = ', '.join(_make_address(a) for a in cc)

    if subject:
        message['Subject'] = subject

    if reply_to_message_id:
        message['In-Reply-To'] = reply_to_message_id

        references = reply_to_message_references or []
        references.append(reply_to_message_id)
        message['References'] = ' '.join(references)

    # Attach the text part (simples!)
    text_part = MIMEText(text, 'plain')
    message.attach(text_part)

    # Make/attach the HTML part, including any quote
    if not html:
        html = markdownify(text)

    if reply_to_html:
        html = f'{html}<blockquote>{reply_to_html}</blockquote>'

    html_part = MIMEText(html, 'html')
    message.attach(html_part)

    # Send the email!
    with smtp_connection.get_connection() as smtp:
        logger.debug(f'Send email via SMTP/{smtp_connection}: {subject} => {to_addresses}')
        smtp.sendmail(from_, to_addresses, message.as_string())
