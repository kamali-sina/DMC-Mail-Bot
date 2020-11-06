import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import time

class Mail :
    def __init__(self, title) :
        self.title = title
        self.have_receiver = False
        self.have_body = False
        self.have_file = False
        self.log = False

    def set_body(self, body) :
        self.body = body
        self.have_body = True

    def set_file(self, file_addr, file_name=None) :
        if file_name == None :
            file_name = file_addr.split('/')[-1]
        self.file = file_addr
        self.file_name = file_name
        self.have_file = True

    def receiver(self, to) :
        self.receiver = to
        self.have_receiver = True

    def have_content(self) :
        return self.have_body or self.have_file

    def is_ready(self) :
        return self.have_content() and self.have_receiver

    def logger(self, folder) :
        self.log_folder = folder
        if folder[-1] == '/' :
            self.log_folder += '/'
        self.log = True

    def record(self, text) :
        with open(self.log_folder+self.send_time, 'w') as f :
            f.write(text)

    def send(self, sender, just_record=False, received=False) :
        if not self.is_ready() :
            return "mail is not ready!"
        message = MIMEMultipart()
        if received :
            message['From'] = self.receiver
            message['To'] = sender.receiver
        else :
            message['From'] = sender.sender
            message['To'] = self.receiver
        message['Subject'] = self.title
        message.attach(MIMEText(self.body, 'plain'))
        record_text = message.as_string()
        if self.have_file :
            attach_file = open(self.file, 'rb')
            payload = MIMEBase('application', 'octate-stream')
            payload.set_payload((attach_file).read())
            encoders.encode_base64(payload)
            payload.add_header('Content-Disposition', 'attachment', filename=self.file_name)
            message.attach(payload)
            record_text += "\n attach_file="+self.file_name
        if just_record :
            self.send_time = time.ctime()
            if self.log : self.record(record_text)
            return self.send_time
        text = message.as_string()
        session = smtplib.SMTP('smtp.gmail.com', 587)
        session.starttls()
        session.login(sender.sender, sender.password)
        session.sendmail(sender.sender, self.receiver, text)
        session.quit()
        self.send_time = time.ctime()
        if self.log : self.record(record_text)
        return self.send_time