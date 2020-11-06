"""
Programmed by Sina Kamali and Behzad Shayeq at Univercity of Tehran. You can contact us at kamali.sina@ut.ac.ir or behzad.shayegh@ut.ac.ir .
This program is to be used only for the DM Contests of Univercity of Tehran. If you want to use it for different matters please contact us.
"""

from MailSender import MailSender
from MailReceiver import MailReceiver
from Mail import Mail
import pandas as pd
import numpy as np
import random
import sys
from math import floor

class server :
    def __init__(self, Email, password, attachments_path='./received_attachments/', log_path='./mails_log/',testmode = False) :
        #configurations
        self.number_of_questions = [13,18,12,1]                           #please state how many questions we have.
        self.admins_commands = ['/start','/log']
        #end of configurations
        self.Email = Email
        self.password = password
        self.log_path = log_path
        self.test_mode = testmode
        self.attachments_path = attachments_path
        self.sender = MailSender(Email, password)
        self.receiver = MailReceiver(Email, password, self.attachments_path)
        self.receiver.logger(self.log_path)
        
    def send_email(self, title, body, target, file=None) :
        m = Mail("Hey there!")
        m.set_body("I'm here ...")
        m.receiver("ut.discretemathematics@gmail.com")
        m.logger(self.log_path)
        if file != None :
            m.set_file("./SSD")

    def listen(self) :
        while True:
            # try:
            try:
                new_mail = self.receiver.get()
                new_mail.receiver = self.extract_email(new_mail)
                print('new mail form : ' + new_mail.receiver)
                self.handle_new_mail(new_mail)
            except:
                self.send_invalid_format(new_mail)
                print('Command was not valid.\n')
            # except:
            #     e = sys.exc_info()[0]
            #     print(str(e))


    
    def handle_new_mail(self, new_mail):
        self.df = pd.read_csv('user_database.csv')
        self.tas = pd.read_csv('ta_database.csv')
        authentication = self.is_email_address_valid(new_mail.receiver)
        print('authentication : ' + str(authentication))
        if (authentication):
            self.validate_command(new_mail,authentication)
        else:
            print('Authentication failed for : ' + new_mail.receiver + '\n')
            self.send_failed_authentication(new_mail)

    def validate_command(self,mail,authentication):
        body = mail.body
        print('body : ' + body)
        sliced_body = body.split()
        if (len(body) <= 0 or not(sliced_body[0])):
            self.send_invalid_format(mail)
            print('Command was not valid.\n')
            return
        if (len(body) <= 0 or str(sliced_body[0])[0] != '/'):
            self.send_invalid_format(mail)
            print('Command was not valid.\n')
            return
        command = sliced_body[0]
        self.check_permission(command,sliced_body,mail,authentication,body)


    def check_permission (self,command,sliced_body,mail,authentication,body):
        #TODO: Fix this Later
        command = command.strip().lower()
        if ((command == '/start' or command == '/log') and authentication != 3):
            self.send_permission_denied(mail)
            print('command : "'+ command + '". Permission Denied.')
            return
        elif (command == '/grade' and authentication != 2):
            self.send_permission_denied(mail)
            print('command : "'+ command + '". Permission Denied.')
            return
        self.switch_command(command,sliced_body,mail,body)
    
    def switch_command(self,command,sliced_body,mail,body):
        #TODO: complete this.
        if (self.test_mode):
            self.send_testmode(mail)
            return
        if (command == '/status'):
            self.send_status(mail)
        elif (command == '/buy' and len(sliced_body) > 1):
            self.buy_question(sliced_body,mail)
        elif (command == '/sell' and len(sliced_body) > 1):
            self.sell_question(sliced_body,mail)
        elif (command == '/commands'):
            self.send_commands(mail)
        elif (command == '/submit' and len(sliced_body) > 1):
            self.submit_question(sliced_body,mail)
        elif (command == '/grade' and len(sliced_body) > 2):
            self.grade_question(sliced_body,mail,body)
        else:
            print('command was : ' + command + '  it was invalid')
            self.send_invalid_format(mail)
        
    def grade_question(self,sliced_body,mail,body):
        question_name = str(sliced_body[1]).lower().strip()
        difficulty = self.switch_question_name(question_name)
        a = body.find('<')
        b = body.find('>')
        if (a == -1 or b == -1 or b <= a):
            self.send_invalid_format()
            print('invlaid format\n')
            return
        feedback = body[a+1:b]
        if (difficulty == -1):
            self.send_invalid_format()
            print('invlaid format\n')
            return
        user_email = str(sliced_body[2]).lower().strip()
        ta_email = mail.receiver
        mail.receiver = user_email
        if (not self.user_has_question(mail,question_name)):
            mail.receiver = ta_email
            self.send_dont_have_question_ta_edition(mail)
            print ('User did not have the question.\n')
            return
        question_stat = str(sliced_body[3]).lower().strip()
        configure = pd.read_csv('question_configuration.csv')
        configure = configure.loc[difficulty,:]
        index = self.find_users_index(mail)
        mail.receiver = ta_email
        if (index == -1):
            mail.receiver = ta_email
            self.send_email_not_found(mail)
            print('The user ta stated was not found.\n')
            return
        mail.set_body('Grade was submitted.\nThank you.')
        mail.title = 'Grade submitted'
        mail.have_file = False
        self.sender.send(mail)
        if (question_stat == 'accept'):
            mail.receiver = '<'+ user_email+'>'
            chunk = self.df.loc[index,:]
            score = int(chunk['score'])
            score += configure['score']
            money = int(chunk['money'])
            money += configure['bounty']
            mail.receiver = user_email
            self.change_team_status(chunk['team'],money,score,chunk['buyed_questions'])
            self.send_submission_accepted(mail,question_name,score,money)
            print('anwer accepted. team ' + chunk['team'] + ' now has ' + str(score) + ' score.')
        elif (question_stat == 'reject'):
            mail.receiver = user_email
            self.send_submission_not_accepted(mail,feedback)
            print('answer not accepted.')
        else:
            self.send_invalid_format(mail)

    def submit_question(self,sliced_body,mail):
        if (mail.have_file == False):
            self.send_no_file_attached(mail)
            print('no file attached.\n')
            return
        question_name = str(sliced_body[1]).lower().strip()
        if (not self.user_has_question(mail,question_name)):
            self.send_dont_have_question(mail)
            print ('User did not have the question.\n')
            return
        user_index = self.find_users_index(mail)
        user = self.df.loc[user_index,:]
        question_database = pd.read_csv('question_database.csv')
        question_series = pd.Series(question_database['name']).unique()
        if (question_name in question_series):
            index = question_database[question_database['name']==question_name].index.values.astype(int)[0]
            question = question_database.loc[index,:]
            mail_sender = mail.receiver
            mail.receiver = question['ta_email']
            mail.set_body('Hey '+ question['ta_name'] + ' please grade this question from team: ' + user['team'] +' and sender : <' + mail_sender + '> report the grade with "/grade"  ASAP.\nIf you do not know the format please read the doc on grading in this contest.\nThank you for helping us in advance.')
            mail.title = 'Grade ' + question_name            
            self.sender.send(mail)
            mail.receiver = mail_sender
            mail.set_body('Your answer has been submitted.\n We will inform you as soon as possible.')
            mail.title = 'Answer Submitted.'
            mail.have_file = False
            self.sender.send(mail)
        else:
            print('did not find question ' + question_name)
            self.send_question_not_found(mail)

    def switch_question_name(self,question_name):
        difficulty = 0
        if (question_name[0] == 'e'):
            difficulty = 0
        elif(question_name[0] == 'm'):
            difficulty = 1
        elif(question_name[0] == 'h'):
            difficulty = 2
        elif(question_name[0] == 'l'):
            difficulty = 3
        else:
            self.send_invalid_format(mail)
            return -1
        return difficulty

    def sell_question(self,scliced_body,mail):
        question_name = str(scliced_body[1]).lower().strip()
        index = self.find_users_index(mail)
        chunk = self.df.loc[index,:]
        money = int(chunk['money'])
        buyed_questions = chunk['buyed_questions']
        configure = pd.read_csv('question_configuration.csv')
        if (buyed_questions == '-'):
            buyed_questions = []
        else:
            buyed_questions = buyed_questions.split('#')
        if (question_name in buyed_questions):
            buyed_questions.remove(question_name)
            difficulty = self.switch_question_name(question_name)
            if (difficulty == -1):
                print('invlaid format\n')
                return
            configure = configure.loc[difficulty,:]
            money += int(configure['sell_price'])
            string = self.list_to_buyedQuestions_format(buyed_questions)
            self.change_team_status(chunk['team'],money,chunk['score'],string)
            self.send_sell_successful(mail,question_name,money)
        else:
            print('The user does not have ' + question_name)
            self.send_dont_have_question(mail)

    def buy_question(self,sliced_body,mail):
        level = str(sliced_body[1]).lower().strip()
        index = self.find_users_index(mail)
        if (index == -1):
            self.send_email_not_found(mail)
            print('email is not a user')
        user = self.df.loc[index,:]
        buyed_questions = str(user['buyed_questions'])
        money = int(user['money'])
        configure = pd.read_csv('question_configuration.csv')
        difficulty = 0
        if (buyed_questions == '-'):
            buyed_questions = []
        else:
            buyed_questions = buyed_questions.split('#')
        buys_counter = [0,0,0,0]
        for x in buyed_questions:
            if (x[0] == 'e'):
                buys_counter[0] += 1
            elif (x[0] == 'm'):
                buys_counter[1] += 1
            elif (x[0] == 'h'):
                buys_counter[2] += 1
            elif (x[0] == 'l'):
                buys_counter[3] += 1
        if (level == 'easy'):
            difficulty = 0
        elif (level == 'medium'):
            difficulty = 1
        elif (level == 'hard'):
            difficulty = 2
        elif (level == 'legend'):
            difficulty = 3
        else:
            self.send_invalid_format(mail)
            print('invlaid format\n')
            return
        configure = configure.loc[difficulty,:]
        if (money < configure['price']):
            self.send_insufficient_funds(mail)
            print('Insufficient funds.\n')
            return
        if (self.number_of_questions[difficulty] == buys_counter[difficulty]):
            self.send_no_more_questions(mail)
            print('no more '+ configure['difficulty'] +' questions was available to them.\n')
            return
        money -= configure['price']
        question_number = floor(random.random() * self.number_of_questions[difficulty])
        question_name = str(configure['difficulty'])[0] + str(question_number)
        while (question_name in buyed_questions):
            question_number = floor(random.random() * self.number_of_questions[difficulty])
            question_name = str(configure['difficulty'])[0] + str(question_number)
        print (mail.receiver + ' bought ' + question_name)
        buyed_questions.append(question_name)
        buyed_questions_string = self.list_to_buyedQuestions_format(buyed_questions)
        self.change_team_status(str(user['team']),money,str(user['score']),buyed_questions_string)
        self.send_buy_successful(mail,question_name,money)
    
    
    def change_team_status(self,team_name,money,score,buyed_questions):
        team_name = team_name.strip()
        chunk = self.df.index[self.df['team'] == str(team_name)]
        self.df.loc[chunk,['money']] = int(money)
        self.df.loc[chunk,['score']] = int(score)
        self.df.loc[chunk,['buyed_questions']] = str(buyed_questions)

        self.sort_df_by_score()
        self.save_df()

    def list_to_buyedQuestions_format(self,buyed_questions_list):
        string = ''
        if (len(buyed_questions_list) == 0):
            string += '-'
        else:
            for i in range(len(buyed_questions_list)):
                if (i == 0):
                    string += str(buyed_questions_list[i])
                else:
                    string += '#' + str(buyed_questions_list[i])
        return string


    def is_email_address_valid (self,email_address):
        user_series = pd.Series(self.df['user']).unique()
        ta_series = pd.Series(self.tas[self.tas['role'] != 'admin']['user']).unique()
        admin_series = pd.Series(self.tas[self.tas['role'] == 'admin']['user']).unique() 
        if (email_address in user_series):
            return 1
        elif (email_address in admin_series):
            return 3
        elif (email_address in ta_series):
            return 2
        else:
            return 0
    
    def user_has_question(self,mail,question_name):
        index = self.find_users_index(mail)
        chunk = self.df.loc[index,:]
        buyed_questions = chunk['buyed_questions']
        if (buyed_questions == '-'):
            buyed_questions = []
        else:
            buyed_questions = buyed_questions.split('#')
        if (question_name in buyed_questions):
            return True
        else:
            return False

    def find_users_index(self,mail):
        email_address = mail.receiver
        user_series = pd.Series(self.df['user']).unique()
        if (email_address in user_series):
            return self.df[self.df['user']==email_address].index.values.astype(int)[0]
        else:
            print(email_address + ' was not found')
            return -1
        
    def extract_email(self, mail):
        string = mail.receiver
        a = string.find('<')
        b = string.find('>')
        return string[a+1:b]

    def sort_df_by_score(self):
        self.df = self.df.sort_values(["score"], ascending = False)

    def save_df(self):
        self.df = self.df.loc[:, ~self.df.columns.str.contains('^Unnamed')]
        self.df.to_csv('./user_database.csv')

    def send_failed_authentication(self,mail):
        mail.set_body('Authentication failed.\n You are not registered in our database.\n If you think this is a mistake contact "sininoir@gmail.com" or "behzad.shayegh.b@gmail.com" immediately.')
        mail.have_file = False
        mail.title = 'Authentication failed'
        self.sender.send(mail)

    def send_submission_not_accepted(self,mail,feedback):
        mail.set_body('Your submission was not accepted by our team.\n change your answer and submit again.\n This is your TAs feedback: <' + feedback + '>' )
        mail.have_file = False
        mail.title = 'Submission not Accepted'
        self.sender.send(mail)

    def send_submission_accepted(self,mail,question_name,score,money):
        mail.set_body('Your answer on '+ question_name +' has been accepted.\n You now have ' + str(money) + ' money and ' + str(score) + ' score.\n good job.')
        mail.title = 'Submission has been Accepted'
        mail.have_file = False
        self.sender.send(mail)

    def send_invalid_format(self,mail):
        mail.set_body('Invalid format detected.\n Please note that you can view commands via "/commands".')
        mail.have_file = False
        mail.title = 'Invalid format'
        self.sender.send(mail)

    def send_dont_have_question(self,mail):
        mail.set_body('You do not have the stated question. If you want to view buyed questions send "/status".')
        mail.have_file = False
        mail.title = 'Question Not Buyed'
        self.sender.send(mail)

    def send_dont_have_question_ta_edition(self,mail):
        mail.set_body('User did not have the stated question.\nDouble check the name you wrote and grade again or maybe they just sold the question.\nThank you.')
        mail.have_file = False
        mail.title = 'User Question Not Buyed'
        self.sender.send(mail)

    def send_email_not_found(self,mail):
        mail.set_body('The email you entered was not found.\nplease double check it.\n Thank you.')
        mail.have_file = False
        mail.title = 'User email not found'
        self.sender.send(mail)

    def send_permission_denied(self,mail):
        mail.set_body("Permission denied.\n You don't have the permission to use that command.\n For the list of your command send '/commands'.")
        mail.have_file = False
        mail.title = 'Permission denied'
        self.sender.send(mail)

    def send_no_more_questions(self,mail):
        mail.set_body("There are no more questions remaining for your team in this level of difficulty.\nplease choose another diffuculty.")
        mail.have_file = False
        mail.title = 'No more Questions remaining'
        self.sender.send(mail)

    def send_buy_successful(self,mail,question_name,money):
        mail.set_body("You have successfully bought question "+ question_name+'.\n You now have ' + str(money) +' money left.\nYou can find the file attached to your email.\n You can submit your answer with "/submit #question_name#" and attaching your solution to the email.')
        mail.set_file ('./questions/' + question_name + '.pdf')
        mail.title = 'Buy Successful'
        self.sender.send(mail)

    def send_sell_successful(self,mail,question_name,money):
        mail.set_body("You have successfully selled question "+ question_name+'.\n You now have ' + str(money) +' money left.\nNote that you might get this same question again if you buy from the same difficulty because the question drops are random.')
        mail.have_file = False
        mail.title = 'Sell Successful'
        self.sender.send(mail)

    def send_question_not_found(self,mail):
        mail.set_body("Did not find the question.\n Please check and send your answer again.\n Thank you.")
        mail.have_file = False
        mail.title = 'Question not Found'
        self.sender.send(mail)

    def send_insufficient_funds(self,mail):
        mail.set_body("You don't have enough money to buy at this level.\n Earn more money at lower levels and try again.")
        mail.have_file = False
        mail.title = 'Insufficient Funds'
        self.sender.send(mail)

    def send_commands(self,mail):
        mail.set_body("All commands start with a '/' and are as followed:\n '/buy' : lets you buy a new question of selected difficulty.\n '/submit' : lets you submit your answer on a selceted question.you have to attach your answer. \n '/sell' : lets you sell a question that you have buyed and cannot solve.\n 'status': lets you see the status of the Contest.\n '/commands : :D")
        mail.have_file = False
        mail.title = 'Commands List'
        self.sender.send(mail)

    def send_no_file_attached(self,mail):
        mail.set_body("There was no file attached to the email you sent us.\n Plese make sure you uploaded correctly and try again.")
        mail.have_file = False
        mail.title = 'No File Was Attached'
        self.sender.send(mail)

    def send_testmode(self,mail):
        mail.set_body("We are currently in test mode. If you are getting this email it means you are registered in our database.\n Try to adapt with the new enviroment. Please wait at least 5 minutes if you don't get an answer from us because the serves will be very crowded at the begining of the contest.\n the contest begins at 2:00 pm.\n good luck.")
        mail.have_file = False
        mail.title = 'Test Mode'
        self.sender.send(mail)

    def send_status(self,mail):
        mail.have_file = False
        mail.title = 'Status Of The Contest'
        string = 'Contest OF DM Spring of 99\n'
        for i in range(3):
            chunk = self.df.loc[i*3,:]
            string += '#' + str(i+1) + ': ' + self.df['team'].iloc[i*3] + '   score : ' + str(self.df['score'].iloc[i*3]) + '\n'
        index = self.find_users_index(mail)
        string += '\n\n You have '+ str(self.df['money'].iloc[index]) + ' money left. your score is '+ str(self.df['score'].iloc[index]) + '\n'
        mail.set_body(string)
        self.sender.send(mail)
        
s = server('ut.discretemathematics@gmail.com', 'DM99forever')
s.listen()
