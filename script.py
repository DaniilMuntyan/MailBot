import imaplib
import threading
import email as email_lib
import classes
import telebot
import os
from classes import EmailHandler
import sched
import time
from langdetect import detect
import requests

s = sched.scheduler(time.time, time.sleep)
token = "962832986:AAEaFrbPHcUpje0V1pYBqMGKkjPtPliMQUw"
path = '/home/ubuntu/Daniil/Gmail/Files/'
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
    def prepare_text(text: str):
        if len(text) > 4096:
            return 'Сообщение слишком длинное ' + u"\U0001F614" + '\nПожалуйста, посмотрите текст на почтовом ящике'
        return text

    @staticmethod
    def prepare_subject(subject: str, with_parse_mode: bool):
        if with_parse_mode:
            return "Тема: *{}*".format(subject)
        return "Тема: {}".format(subject)

    @staticmethod
    def prepare_from(from0: str, from1: str, with_parse_mode: bool):
        string = u"\u2709 "
        if with_parse_mode:
            if from0.strip() == "" and from1.strip() == "":
                return string + "<Отправитель неизвестен>"
            if from0.strip() == "":
                return string + ' *{}*'.format(from1)
            if from1.strip() == "":
                return string + ' *{}*'.format(from0)
            return string + ' *"{}" {}*'.format(from0, from1)
        else:
            if from0.strip() == "" and from1.strip() == "":
                return string + "<Отправитель неизвестен>"
            if from0.strip() == "":
                return string + ' {}'.format(from1)
            if from1.strip() == "":
                return string + ' {}'.format(from0)
            return string + ' "{}" {}'.format(from0, from1)

    @staticmethod
    def prepare_msg(from0: str, from1: str, subject: str, text: str, with_parse_mode=True):
        return MailThread.prepare_from(from0, from1, with_parse_mode) + "\n" + \
               MailThread.prepare_subject(subject, with_parse_mode) + "\n\n" + MailThread.prepare_text(text)

    def send_admin(self, string: str):
        message_data = {'chat_id': 442618563, 'text': string}
        requests.post(URL + token + '/sendMessage', data=message_data)

    def send_message(self, string, with_parse_mode=True):
        if with_parse_mode:
            message_data = {'chat_id': self.chat_id, 'text': string, 'parse_mode': 'Markdown'}
        else:
            message_data = {'chat_id': self.chat_id, 'text': string}
        if "</div>" in string or "<p style" in string or "</a>" in string or "<div style" in string \
                or "</html>" in string or "</body>" in string:
            with open('/home/ubuntu/Daniil/Gmail/ScriptBot/Unreadable message.html', 'w') as f:
                f.write(string)
            doc = open('/home/ubuntu/Daniil/Gmail/ScriptBot/Unreadable message.html', 'rb')
            self.send_document(doc)
            os.remove('/home/ubuntu/Daniil/Gmail/ScriptBot/Unreadable message.html')
            return -1
        try:
            request = requests.post(URL + token + '/sendMessage', data=message_data)
            if not request.status_code == 200:
                message_data = {'chat_id': self.chat_id, 'text': string}
                request = requests.post(URL + token + '/sendMessage', data=message_data)
            return request.status_code
        except Exception as e: 
            self.send_admin("Ошибка отправления в канал\n" + str(self.chat_id) + '\n' + str(e))

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
            to = str(self.email.my_mail['To'])
            subject = str(self.email.get_subject())
            '''if 'iasa-ka87@ukr.net' not in to:
                continue'''
            if "Delivery Status Notification (Failure)" in subject or "ka87.iasa+caf_=iasa-" in to:
                continue
            string = subject + ", " + str(self.email.my_mail['Date'])
            now.append((string, temp))
        new_mails = MailThread.intersection(now, current)
        for temp, item in new_mails:
            self.email.my_mail = item
            to = str(self.email.my_mail['To'])
            get_from = self.email.get_from()
            from0 = str(get_from[0])
            p = get_from[1]
            from1 = str(p.decode('utf-8')) if not isinstance(p, str) else p
            if "mailer-daemon@googlemail.com" in from1:
                continue
            subject = str(self.email.get_subject())
            if subject.strip() == "":
                subject = "<нет>"
            text = str(self.email.get_text())
            if len(text) > 4096:
                k = text[:4096].rfind(" ")
                text1 = text[:k]
                text2 = text[k:]
                self.send_message(MailThread.prepare_msg(from0, from1, subject, text1, True), with_parse_mode=True)
                self.send_message(text2, with_parse_mode=True)
            else:
                self.send_message(MailThread.prepare_msg(from0, from1, subject, text, True),
                                  with_parse_mode=True)
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
                    self.send_message(file_name + " " + u'\U0001f447')
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
    with open('/home/ubuntu/Daniil/Gmail/ScriptBot/ChatIds.txt', 'r', encoding='utf-8-sig') as f:
        for temp in list(f):
            list_channels.append(get_split(temp))
    for temp in list_channels:
        list_threads.append(MailThread(temp[0], temp[1], temp[2]))





