import pandas as pd
import os
import sys

class MailSender :
    def __init__(self, sender, password) :
        self.sender = sender
        self.password = password

    def send(self, mail) :
        t = mail.send(self)