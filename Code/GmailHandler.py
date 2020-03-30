from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from config import service_account_address
import os
import pathlib


class GmailHandler:

    def __init__(self, user_account, receiver_account):

        self.user_account = user_account
        self.receiver_account = receiver_account
        self.service = self.get_authorization()

    def get_authorization(self):

        credentials = ServiceAccountCredentials.from_p12_keyfile(
            service_account_address,
            os.path.join(pathlib.Path(__file__).parent.absolute(), '../__local__/credentials.p12'),
            'notasecret',
            scopes=['https://mail.google.com/'])
        credentials = credentials.create_delegated(self.user_account)

        return build('gmail', 'v1', credentials=credentials)

    def get_messages(self):

        print("Pulling messages")
        self.service = self.get_authorization()

        query = f"to:{self.receiver_account} is:unread"
        unread = self.service.users().messages().list(userId=self.user_account, q=query).execute()
        print(f"\tUnread: {unread['resultSizeEstimate']}")

        messages = unread['messages'] if unread['resultSizeEstimate'] != 0 else []

        emails = []
        for msg in messages:
            mail = self.service.users().messages().get(userId=self.user_account, id=msg['id']).execute()

            self.service.users().messages().modify(userId=self.user_account, id=msg['id'],
                                                   body={'removeLabelIds': ['UNREAD']}).execute()
            print('\tMarking as read ...')

            emails.append(mail)

        print("Messages read\n")
        return emails
