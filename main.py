import time
from config import *
from Code.GmailHandler import GmailHandler
from Code.MessengerHandler import *


gmail_handler = GmailHandler(user_account=user_account, receiver_account=receiver_account)
messenger_handler = MessengerHandler(messenger_email, messenger_password, messenger_chat_id, ThreadType.GROUP)

while True:
    mails = gmail_handler.get_messages()
    for mail in mails:
        print('Sending message')
        messenger_handler.parse_message(mail)
        print('Finished sending message\n')

    time.sleep(30)
