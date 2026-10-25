import base64
from email.message import EmailMessage
from enum import Enum
import os

from pydantic import BaseModel, Field

from utils import find_plain_text, get_gmail_service_client


class Label(Enum):
    INBOX = "INBOX"
    SPAM = "SPAM"
    TRASH = "TRASH"
    UNREAD = "UNREAD"
    STARRED = "STARRED"
    IMPORTANT = "IMPORTANT"
    SENT = "SENT"
    DRAFT = "DRAFT"
    CATEGORY_PERSONAL = "CATEGORY_PERSONAL"
    CATEGORY_SOCIAL = "CATEGORY_SOCIAL"
    CATEGORY_PROMOTIONS = "CATEGORY_PROMOTIONS"
    CATEGORY_UPDATES = "CATEGORY_UPDATES"
    CATEGORY_FORUMS = "CATEGORY_FORUMS"


class GetMessagesListRequest(BaseModel):
    maxResults: int = Field(default=10, description=(
        "Number of recent mails to be fetched. By default recent 10 mails are fetched. "
        "Maximum 500 recent mails can be fetched per request. Minimum 1 recent mails can be fetched per request"
    ), max=500, min=1)
    q: str = Field(default="", description=(
        'Only return messages matching the specified query. Supports the same query format as the Gmail search box. '
        'For example, "from:someuser@example.com rfc822msgid:<somemsgid@example.com> is:unread"'
    ))
    labelIds: list[Label] = Field(default=[Label.INBOX], description=(
        "Only return messages with labels that match all of the specified label IDs"
    ))


def get_messages_list(q="", labelIds: list[Label] = [Label.INBOX], maxResults: int = 10) -> list[dict[str, str]]:
    service = get_gmail_service_client()
    results = service.users().messages().list(
        userId="me", labelIds=labelIds, maxResults=maxResults, q=q
    ).execute()
    result = []
    for message in results.get("messages", []):
        msg = service.users().messages().get(userId="me", id=message["id"]).execute()
        result.append({"id": message["id"], "snippet": msg["snippet"]})
    return result


class GetMessageRequest(BaseModel):
    id: str = Field(description="Id of mail to be retrieved")


def get_message(id):
    service = get_gmail_service_client()
    result = service.user().messages().get(userId="me", id=id, format="full").execute()
    return find_plain_text(result.get("payload", {})) or result.get("snippet", "")


class GmailCreateDraftRequest(BaseModel):
    content: str = Field(description="Complete draft body.")
    to: str = Field(description="Recipient's email address.", pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    subject: str = Field(description="subject of the draft")


def _create_email_message(content, to, subject):
    message = EmailMessage()
    message.set_content(content)
    message["To"] = to
    message["From"] = os.getenv("GMAIL")
    message["Subject"] = subject
    return base64.urlsafe_b64encode(message.as_bytes()).decode()


def gmail_create_draft(content, to, subject):
    service = get_gmail_service_client()
    encoded_message = _create_email_message(content, to, subject)
    create_message = {"message": {"raw": encoded_message}}
    return service.users().drafts().create(userId="me", body=create_message).execute()


class GmailSendDraftRequest(BaseModel):
    draft_id: str = Field(description="id of the draft to be send")


def gmail_send_draft(draft_id):
    service = get_gmail_service_client()
    sent_message = service.user().draft().send(userId="me", body={"id": draft_id}).execute()
    return f"sent message id: {sent_message['id']}"


class GmailSendMessageRequest(BaseModel):
    content: str = Field(description="Complete email body.")
    to: str = Field(description="Recipient's email address.", pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    subject: str = Field(description="Subject of the email.")


def gmail_send_message(content, to, subject):
    service = get_gmail_service_client()
    encoded_message = _create_email_message(content, to, subject)
    send_message = service.users().messages().send(
        userId="me", body={"raw": encoded_message}
    ).execute()
    return f"sent message id: {send_message['id']}"


def _tool(name, description, request_model):
    return {"type": "function", "function": {
        "name": name, "description": description,
        "parameters": request_model.model_json_schema(),
    }}


TOOLS = [
    _tool("get_messages_list", "Get list of recent mails of user of given size. Output list contains id (email id) and snippet for every email.", GetMessagesListRequest),
    _tool("get_message", "Gets the specified mail using its mail id.", GetMessageRequest),
    _tool("gmail_create_draft", "Create and save an email draft in the user's Gmail account without sending it. Use this tool when the user asks to draft or compose an email. Return the draft ID and message metadata.", GmailCreateDraftRequest),
    _tool("gmail_send_draft", "Send a saved draft in the user's Gmail account. Returns the id of sent mail.", GmailSendDraftRequest),
    _tool("gmail_send_message", "Compose and send an email in the user's Gmail account. Use this tool when the user asks to send an email. Returns the id of sent mail.", GmailSendMessageRequest),
]

TOOLS_MAPPING = {
    "get_messages_list": {"function": get_messages_list, "validator": GetMessagesListRequest},
    "get_message": {"function": get_message, "validator": GetMessageRequest},
    "gmail_create_draft": {"function": gmail_create_draft, "validator": GmailCreateDraftRequest},
    "gmail_send_draft": {"function": gmail_send_draft, "validator": GmailSendDraftRequest},
    "gmail_send_message": {"function": gmail_send_message, "validator": GmailSendMessageRequest},
}
