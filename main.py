import time
from config import *
from GmailHandler import GmailHandler
from MessengerHandler import *


gmail_handler = GmailHandler(user_account=user_account, receiver_account=receiver_account)
messenger_handler = MessengerHandler(messenger_email, messenger_password, messenger_chat_id, ThreadType.GROUP)

while True:
    messages = gmail_handler.get_messages()
    for message in messages:
        messenger_handler.parse_message(message)

    time.sleep(60)
