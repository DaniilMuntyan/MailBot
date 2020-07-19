import imaplib
import oauth2 as oauth
import base64
import email
import chardet
from email.mime.text import MIMEText
from email.header import decode_header
import codecs 
import base64
from langdetect import detect
import quopri
from imbox import Imbox
import imbox
import io
import os
from io import StringIO
from email.generator import Generator


class EmailHandler:

    decoder = codecs.getincrementaldecoder('utf-8')()

    def __init__(self, login, password):
        self.mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
        self.mail.login(login, password)
        self.mail.list()
        self.mail.select("inbox")
        self.c = 0
        typ, data = self.mail.search(None, 'All')
        all_id = data[0].split()
        result, data = self.mail.fetch(all_id[-10], "(RFC822)")
        raw_email = data[0][1]
        self.my_mail = email.message_from_bytes(raw_email)

    def get_last_mails(self, last_mails: int):
        self.mail.list()
        self.mail.select("inbox")
        self.c = 0
        typ, data = self.mail.search(None, 'All')
        all_id = data[0].split()
        return_value = []
        for id in all_id[-1 * last_mails:]:
            result, data = self.mail.fetch(id, "(RFC822)")
            raw_email = data[0][1]
            self.my_mail = email.message_from_bytes(raw_email)
            return_value.append(self.my_mail)
        return_value.reverse()
        return return_value

    def get_text(self):
        my_mail = self.my_mail
        while my_mail.is_multipart():
            my_mail = my_mail.get_payload(0)
        content = my_mail.get_payload(decode=True)
        return EmailHandler.decoder.decode(content)
  
    def get_from(self):
        my_mail = self.my_mail
        decode1 = decode_header(my_mail['From'])[0]
        res1 = decode1[0]
        if decode1[1] is not None:
            temp = codecs.getincrementaldecoder(decode1[1])()
            res1 = temp.decode(decode1[0])
        if len(decode_header(my_mail['From'])) == 2:
            decode2 = decode_header(my_mail['From'])[1]
            res2 = decode2[0]
            if decode2[1] is not None:
                temp = codecs.getincrementaldecoder(decode2[1])()
                res2 = temp.decode(decode2[0])
            return [res1, res2]
        return ["", res1]

    def get_subject(self):
        my_mail = self.my_mail
        subject = my_mail['Subject'].split()
        result = ""
        for temp in subject:
            decode1 = decode_header(temp)[0]
            res = decode1[0]
            if decode1[1] is not None:
                temp = codecs.getincrementaldecoder(decode1[1])()
                res = temp.decode(decode1[0])
                result += res
            else:
                result += res + " "
        return result

    def download_attachment(self):
        email_message = self.my_mail
        c = 0
        k = 1
        for part in email_message.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
            file_name = part.get_filename()
            if file_name is not None:
                names = file_name.split()
                file_name: str = ""
                for name in names:
                    decode1 = decode_header(name)[0]
                    part_name = decode1[0]
                    if decode1[1] is not None:
                        temp = codecs.getincrementaldecoder(decode1[1])()
                        part_name = temp.decode(decode1[0])
                        file_name += part_name
                    else:
                        file_name += part_name + " "
            if bool(file_name):
                file_path = os.path.join('/home/ubuntu/Daniil/Gmail/Files', file_name)
                if not os.path.isfile(file_path):
                    fp = open(file_path, 'wb')
                    fp.write(part.get_payload(decode=True))
                    fp.close()
                    c += 1
