import base64
import pathlib
import pickle
from os import path, listdir
from bs4 import BeautifulSoup
from fbchat import Client
from fbchat.models import *
import shutil

from config import sender_aliases

fonts = {'mathematical': 120224,
         'mathematical_bold': 119808,
         'mathematical_italic': 119860}
default_font = fonts['mathematical']


def convert_font(text, font=default_font):

    def find_chars(start, end, ascii_start):
        chars = {}
        for c, i in enumerate(range(start, end)):
            chars[chr(ascii_start + c)] = chr(i)
        return chars

    math_start = font
    capitals = find_chars(math_start, math_start + 26, 65)
    lowers = find_chars(math_start + 26, math_start + 52, 97)

    new_text = ''
    for letter in text:
        letter = capitals.get(letter, letter)
        letter = lowers.get(letter, letter)
        new_text += letter

    return new_text


class MessengerHandler(Client):

    def __init__(self, email, password, thread, thread_type):
        self.email = email
        self.password = password
        self.cookies_path = path.join(pathlib.Path(__file__).parent.absolute(), '../__local__/cookies.pickle')

        session_cookies = self.load_cookies()
        super().__init__(email, password, session_cookies=session_cookies)
        self.save_cookies()

        self.setDefaultThread(thread, thread_type)

    def check_login(self):
        if not self.isLoggedIn():
            self.login(self.email, self.password)
            self.save_cookies()

    def load_cookies(self):
        cookies = None
        if path.exists(self.cookies_path):
            cookies = pickle.load(open(self.cookies_path, 'rb'))
        return cookies

    def save_cookies(self):
        cookies = self.getSession()
        pickle.dump(cookies, open(self.cookies_path, 'wb'))

    def parse_message(self, mail):
        self.check_login()
        message = mail['message']
        parts = mail['parts']

        def get_header(name):
            for header in message['payload']['headers']:
                if header['name'] == name:
                    return header['value']

        sender = get_header('From')
        if sender in sender_aliases:
            sender = sender_aliases[get_header('From')]

        sender = convert_font(sender, fonts['mathematical_italic'])
        subject = convert_font(get_header('Subject'), fonts['mathematical_bold'])

        contents = None
        if parts:
            html = base64.urlsafe_b64decode(parts['text/html']['body']['data']).decode('utf-8')
            soup = BeautifulSoup(html, "html.parser")
            contents = soup.find('div', attrs={'dir': 'ltr'})

        if contents:  # BeautifulSoup feels like a bit of a hack so we're cautious when using it
            snippet = contents.get_text()
        elif 'body' in message['payload'] and 'data' in message['payload']['body']:
            snippet = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')
        else:
            snippet = message['snippet']
        snippet = snippet[0:400] + ' ...' if len(snippet) > 400 else snippet


        snippet = convert_font(snippet, fonts['mathematical'])

        self.send(Message(text=f"Novo sporočilo od {sender} – {subject}\n{snippet}"))

        if parts and 'other' in parts:
            print('\tUploading files')

            local_path = parts['local_path']
            paths = [path.abspath(path.join(local_path, f)) for f in listdir(local_path) if path.isfile(path.join(local_path, f))]
            for file in paths:
                self.sendLocalFiles(file_paths=[file])

            shutil.rmtree(local_path)
