import imaplib
import threading
import email as email_lib
import classes
import telebot
import os
from email.header import decode_header
from classes import EmailHandler
import sched
import time
from langdetect import detect
import requests

s = sched.scheduler(time.time, time.sleep)
token = "YOUR_TOKEN"
path = '/home/ubuntu/Dev/Mail bot/File/'
splitter = " !!splitter!! "
URL = 'https://api.telegram.org/bot'


class MailThread:
    s = sched.scheduler(time.time, time.sleep)

    def __init__(self, chat_id, login, pswd):
        self.killed = False
        self.flag = True
        self.email = EmailHandler(login, pswd)
        self.chat_id = chat_id
        s.enter(2, 1, self.check, ())
        s.run()

    @staticmethod
    def intersection(lst1, lst2):
        return [(value, item) for value, item in lst1 if (value not in lst2 and (value + "\n") not in lst2)]

    @staticmethod
    def prepare_text(text: str, with_parse_mode=True):
        text = text.replace("*", "")
        if len(text) > 4096:
            return 'Сообщение слишком длинное ' + u"\U0001F614" + '\nПожалуйста, посмотрите текст на почтовом ящике'
        if with_parse_mode:
            return MailThread.edit_html(text)
        return text

    @staticmethod
    def prepare_to(to: str, with_parse_mode: bool):
        if with_parse_mode:
            return 'To: ' + '<b>' + MailThread.edit_html(to) + '</b>'
        return 'To: ' + to

    @staticmethod
    def prepare_subject(subject: str, with_parse_mode: bool):
        if with_parse_mode:
            return "Subject: " + '<b>{}</b>'.format(MailThread.edit_html(subject))
        return "Subject: {}".format(subject)

    @staticmethod
    def prepare_from(from0: str, from1: str, with_parse_mode: bool):
        string = u"\u2709 "
        if with_parse_mode:
            if from0.strip() == "" and from1.strip() == "":
                return string + "<Отправитель неизвестен>"
            if from0.strip() == "":
                return string + ' <b>{}</b>'.format(MailThread.edit_html(from1))
                #return string + ' *{}*'.format(from1)
            if from1.strip() == "":
                return string + ' <b>{}</b>'.format(MailThread.edit_html(from0))
                #return string + ' *{}*'.format(from0)
            return string + " <b>&#34{}&#34 {}</b>".format(MailThread.edit_html(from0), MailThread.edit_html(from1))
            #return string + ' *"{}" {}*'.format(from0, from1)
        else:
            if from0.strip() == "" and from1.strip() == "":
                return string + "<Отправитель неизвестен>"
            if from0.strip() == "":
                return string + ' {}'.format(from1)
            if from1.strip() == "":
                return string + ' {}'.format(from0)
            return string + ' "{}" {}'.format(from0, from1)

    @staticmethod
    def prepare_msg(from0: str, from1: str, subject: str, to: str, text: str, with_parse_mode=True):
        return MailThread.prepare_from(from0, from1, with_parse_mode) + "\n" + \
               MailThread.prepare_subject(subject, with_parse_mode) + "\n" + \
               MailThread.prepare_to(to, with_parse_mode) + "\n\n" + MailThread.prepare_text(text, with_parse_mode)

    @staticmethod
    def edit_html(string: str):
        char_map = {"&": '&#38;', "<": "&#60", ">": "&#62", "−": "&#8722", '"': "&#34", "§": "&#167",
                    "©": "&#169", "®": "&#174", "'": "&#8242", "«": "&#171;", "»": "&#187;",
                    '″': "&#8243;", "“": "&#8220;", "”": "&#8221;", "„": '&#8222;', "‘": "&#8216;",
                    "’": "&#8217;", "‚": "&#8218;", "≈": "&#8776;", "№": "&#8470;"}

        for char, repl in char_map.items():
            string = string.replace(char, repl)

        return string

    def send_admin(self, string: str):
        message_data = {'chat_id': 442618563, 'text': string}
        requests.post(URL + token + '/sendMessage', data=message_data)

    def send_message(self, string, with_parse_mode):
        if with_parse_mode:
            message_data = {'chat_id': self.chat_id, 'text': string, 'parse_mode': 'HTML'}
        else:
            message_data = {'chat_id': self.chat_id, 'text': string}
        if "</div>" in string or "<p style" in string or "</a>" in string or "<div style" in string \
                or "</html>" in string or "</body>" in string:

            with open('Unreadable message.html', 'w') as f:
                f.write(string)
            doc = open('Unreadable message.html', 'rb')
            self.send_document(doc)
            os.remove('Unreadable message.html')
            return -1
        request = requests.post(URL + token + '/sendMessage', data=message_data)
        return request.status_code

    def send_document(self, file):
        post_data = {'chat_id': self.chat_id}
        post_file = {'document': file}
        try:
            r = requests.post(f'https://api.telegram.org/bot{token}/sendDocument', data=post_data, files=post_file)
            if not r.status_code == 200:
                self.send_admin("Ошибка отправления в канал (приложения)\n" + str(self.chat_id) + '\nStatus code: ' +
                                str(r.status_code) + " " + file.name)
        except Exception as e:
            self.send_admin("Ошибка отправления в канал\n" + str(self.chat_id) + '\n' + str(e))
        time.sleep(2)

    def check(self): 
        current = []
        now = []
        with open(path + 'current.txt', 'r', encoding='UTF-8') as f:
            current = f.read().split(splitter)
        mails_list = self.email.get_last_mails(5)
        mails_list.reverse()
        for temp in mails_list:
            self.email.my_mail = temp
            to = self.email.get_to()
            subject = str(self.email.get_subject())
            if "Delivery Status Notification (Failure)" in subject or "ka87.iasa+caf_=iasa-" in to:
                continue
            string = subject + ", " + str(self.email.my_mail['Date'])
            now.append((string, temp))
        new_mails = MailThread.intersection(now, current)
        for temp, item in new_mails:
            self.email.my_mail = item
            to = self.email.get_to()
            get_from = self.email.get_from()
            from0 = str(get_from[0])
            p = get_from[1]
            from1 = str(p.decode('utf-8')) if not isinstance(p, str) else p
            if "mailer-daemon@googlemail.com" in from1:
                continue
            subject = str(self.email.get_subject())
            if subject.strip() == "":
                subject = "<no>"
            text = str(self.email.get_text())
            if len(text) > 4096:
                k = text[:4096].rfind(" ")
                text1 = text[:k]
                text2 = text[k:]
                str_first_prepare = MailThread.prepare_msg(from0, from1, subject, to, text1, True)
                try:
                    code = self.send_message(str_first_prepare, with_parse_mode=True)
                    if not code == 200:
                        message_data = {'chat_id': self.chat_id, 'text': MailThread.prepare_msg(from0, from1, subject,
                                                                                                to, text1, False)}
                        requests.post(URL + token + '/sendMessage', data=message_data)
                    code = self.send_message(text2, with_parse_mode=True)
                    if not code == 200:
                        message_data = {'chat_id': self.chat_id, 'text': text2}
                        requests.post(URL + token + '/sendMessage', data=message_data)
                except Exception as e:
                    self.send_admin("Ошибка отправления в канал\n" + str(self.chat_id) + '\n' + str(e))
            else:
                try:
                    code = self.send_message(MailThread.prepare_msg(from0, from1, subject, to, text,
                                                                    True), with_parse_mode=True)
                    if not code == 200:
                        message_data = {'chat_id': self.chat_id, 'text': MailThread.prepare_msg(from0, from1, subject,
                                                                                                to, text, False)}
                        requests.post(URL + token + '/sendMessage', data=message_data)
                except Exception as e:
                    self.send_admin("Ошибка отправления в канал\n" + str(self.chat_id) + '\n' + str(e))
            self.email.download_attachment()
            arr = os.listdir(path)
            k = 1
            for temp_path in arr:
                if temp_path == 'current.txt':
                    continue
                if detect(temp_path) == 'uk' or detect(temp_path) == 'ru':
                    file_name = temp_path
                    temp_path = "Unknown attachment({}){}".format(k, file_name[temp_path.rfind('.'):])
                    os.rename(path + '/' + file_name, path + '/' + temp_path)
                    self.send_message(file_name + " " + u'\U0001f447', with_parse_mode=False)
                    time.sleep(1)
                    k += 1
                doc = open(path + '/' + temp_path, 'rb')
                self.send_document(doc)
                os.remove(path + '/' + temp_path)
            time.sleep(1)
        with open(path + 'current.txt', 'w', encoding='UTF-8') as f:
            for temp, temp2 in now:
                f.write(temp + splitter)
        if self.flag:
            s.enter(2, 1, self.check, ())
        else:
            return


def get_split(string: str):
    s = string.split(' ')
    return int(s[0]), s[1], s[2]


if __name__ == '__main__':
    chat_id = -1
    login = ""
    pswd = ""
    my_list = []
    list_channels = []
    list_threads = []
    with open('ChatIds.txt', 'r', encoding='utf-8-sig') as f:
        for temp in list(f):
            list_channels.append(get_split(temp))

    for temp in list_channels:
        list_threads.append(threading.Thread(target=MailThread, args= (temp[0], temp[1], temp[2],)))
        list_threads[-1].start()
