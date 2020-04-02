from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from config import service_account_address
import base64
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

            parts = self.get_parts(mail['payload']['parts']) if 'parts' in mail['payload'] else None
            if parts and 'other' in parts:
                path = os.path.join(pathlib.Path(__file__).parent.absolute(), f'../__local__/tmp/{msg["id"]}')
                path = os.path.abspath(path)
                if not os.path.exists(path):
                    os.makedirs(path)
                parts.update({'local_path': path})

                for other in parts['other']:
                    if 'data' not in other['body']:
                        attachment = self.service.users().messages().attachments().get(
                            id=other['body']['attachmentId'], messageId=msg['id'], userId=self.user_account).execute()
                        other['body'] = attachment

                    file_data = base64.urlsafe_b64decode(other['body']['data'])

                    file_mode = 'wb'
                    if type(file_data) is not bytes:
                        file_data.encode('utf-8')
                        file_mode = 'w'

                    file_path = os.path.join(path, other['filename'])

                    f = open(file_path, file_mode)
                    f.write(file_data)
                    f.close()

            self.service.users().messages().modify(userId=self.user_account, id=msg['id'],
                                                   body={'removeLabelIds': ['UNREAD']}).execute()
            print('\tMarked as read')

            emails.append({'message': mail, 'parts': parts})

        print("Finished\n")
        return emails

    def get_parts(self, sub_parts):
        results = {}
        for part in sub_parts:
            if part['mimeType'].startswith('multipart/'):
                results.update(self.get_parts(part['parts']))
            elif part['mimeType'] == 'text/plain':
                results.update({'text/plain': part})
            elif part['mimeType'] == 'text/html':
                results.update({'text/html': part})
            else:
                if 'other' in results:
                    results['other'].append(part)
                else:
                    results.update({'other': [part]})

        return results
