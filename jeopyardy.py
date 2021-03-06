# Credits:
# JEOPARDY_CSV.csv original can be downloaded from https://www.kaggle.com/tunguz/200000-jeopardy-questions

# To run this project
# The CSV and database for the project can be downloaded here: https://drive.google.com/open?id=13MBHYBgc--F7Sned8J5XC4djgDBI4qCV

# jeoPyardy
# It's implementation is better than the name
# 2019 Colin Burke

# Done for this release


# Planned for future releases
# (todo) buzzers 
# (todo) multiple players
# (todo) save progress
# (todo) implement last week's winner / winstreaks
# (todo) GUI
# (todo) Endless question mode
# (todo) Regular game mode (introductions, rounds, daily double, final jeopardy, transitions)
# (todo) implement a way for images to be seen when there's a URL in the question
# (todo) custom games for date ranges
# (todo) category search

import csv
import random
import pyttsx3
from datetime import datetime as dt
from sqlite3 import connect
import os
import hashlib
import speech_recognition
from difflib import SequenceMatcher

# requires visual C++ Build Tools on windows: https://visualstudio.microsoft.com/visual-cpp-build-tools/

hasher = hashlib.md5()


# if string is at least 80% similar, will return true
def similarstring(a, b, likeness):
    ourratio = SequenceMatcher(None, a, b).ratio()
    if ourratio >= likeness:
        return True
    else:
        return False


# Creates mic, audio source, then tries to call google voice recognition.
def recognize_speech(recognizer, microphone):
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    response = 'No response'
    try:
        response = recognizer.recognize_google(audio)
    except speech_recognition.RequestError:
        print("RequestError")
    except speech_recognition.UnknownValueError:
        print('UnknownValueError')
    return response


class Player:
    def __init__(self, name='test_player', money=0, winstreak=0, hometown='Anywhere, USA', fact='Grows Peppers'):
        self.name = name
        self.money = money
        self.winstreak = winstreak
        self.hometown = hometown
        self.fact = fact
        self.date_joined = dt.now().date()

    def add_funds(self, value):
        self.money += value


class Talker:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.original_rate = self.engine.getProperty('rate')
        self.rate = self.original_rate
        self.engine.setProperty('rate', self.rate)
        self.voiceID = 0

    def say_fast(self, phrase):
        print(phrase)
        self.rate = 200
        self.engine.setProperty('rate', self.rate)
        # set volume to 40%
        self.engine.setProperty('volume', .40)
        self.engine.say(phrase)
        self.engine.runAndWait()

    def slow(self, phrase):
        print(phrase)
        self.rate = 130
        self.engine.setProperty('rate', self.rate)
        # set volume to 40%
        self.engine.setProperty('volume', .40)
        self.engine.say(phrase)
        self.engine.runAndWait()


class Game:
    def __init__(self):
        players = []
        self.dbpath = './game.db'
        self.db_md5 = 'c352294fd78d85fcd234227ee123c542'
        self.conn = connect(self.dbpath)
        self.cursor = self.conn.cursor()
        self.questions = {}
        self.query_questions = {}
        self.question_limit = 0
        self.todays_date = dt.now().date()
        self.last_weeks_winner = None

    def deletedb(self):
        self.conn.close()
        if os.path.exists('./game.db'):
            os.remove('./game.db')

    def opendb(self):
        self.conn = connect(self.dbpath)
        self.cursor = self.conn.cursor()

    def check_db_create_if_not_exists(self):
        if os.path.exists('./game.db'):
            with open('./game.db', 'rb') as afile:
                buf = afile.read()
                hasher.update(buf)
            # print(hasher.hexdigest())
            if hasher.hexdigest() == self.db_md5:
                print('Database Matches Hash')
            else:
                print('Database Doesn\'t match Hash with o. It\'s recommended you delete the DB and restart the script')
                # self.deletedb()
        else:
            print('database does not exist')
            self.setupdb()

    def setupdb(self):
        self.opendb()
        # JEOPARDY_CSV.csv can be downloaded from https://www.kaggle.com/tunguz/200000-jeopardy-questions
        with open('JEOPARDY_CSV.csv', newline='', encoding="utf8") as csvfile:
            reader = csv.DictReader(csvfile)
            self.cursor.execute(
                '''CREATE TABLE IF NOT EXISTS jeopardy_questions (i INT, date TEXT, category TEXT, value INT, question TEXT, answer TEXT)''')
            for i, row in enumerate(reader):
                # replaces all blank values with 200

                if (row[' Value'] is None or row[' Value'].lower() == "none"):
                    value = 200
                else:
                    value = int(str(row[' Value']).replace('$', '').replace(',', '').replace('\'', ''))
                self.questions[i] = {'date': str(row[' Air Date']), 'category': row[' Category'], 'value': value,
                                     'question': row[' Question'], 'answer': row[' Answer']}
                self.cursor.execute('INSERT INTO jeopardy_questions VALUES (?,?,?,?,?,?);',
                                    [i,
                                     str(row[' Air Date']),
                                     row[' Category'],
                                     value,
                                     row[' Question'],
                                     row[' Answer']])

            self.conn.commit()
            self.question_limit = len(self.questions)

    # (todo) retrieve_questions needs to build a custom SQL query for question filtering
    def question_query(self, date=None, value=None):
        d = '' if date in [None, 'None'] else 'date = \"{}\"'.format(date)
        v = '' if value in [None, 'None'] else 'value = {}'.format(value)
        and_chain = ' AND ' if d and v else ''
        where = ' WHERE ' if d or v else ''
        end = ';'
        query = """SELECT * FROM jeopardy_questions{}{}{}{}{}""".format(where, d, and_chain, v, end)
        # print(query)
        self.cursor.execute(query)
        desc = self.cursor.description
        column_names = [col[0] for col in desc]
        self.query_questions = [dict(zip(column_names, row)) for row in self.cursor.fetchall()]
        self.question_limit = len(self.query_questions)

    def standard_questions(self):
        two_hundred = []


def main():
    our_recognizer = speech_recognition.Recognizer()
    our_microphone = speech_recognition.Microphone()

    player_1 = Player('Colin B', 0)
    # read file in
    talker = Talker()
    # talker.say_fast(str('Welcome to Jeopardy. I\'m your host, HAL. Today\'s date is {}'.format(dt.now().date())))
    game = Game()
    game.check_db_create_if_not_exists()
    # here is where you input the values that go into the sql query.
    # game.question_query(value=200, date='2004-12-31')
    # game.question_query(value=200)
    # game.question_query(date='2004-12-31')
    game.question_query()
    playing = True
    question_number = 0
    while playing:
        # question_number = int(input('question number:'))
        question_number = random.randint(0, game.question_limit - 1)
        date = str(game.query_questions[question_number]['date'])
        category = str(game.query_questions[question_number]['category'])
        value = int(game.query_questions[question_number]['value'])
        question = str(game.query_questions[question_number]['question'])
        answer = str(game.query_questions[question_number]['answer']).strip('"')
        talker.say_fast(
            str('From the date: {}, category {}.\n for ${}, please answer the question:\n').format(date, category,
                                                                                                   value))
        # talker.say_fast(str('Category {}'.format(category)))
        talker.say_fast('{}'.format(question))
        # user_response = str(input('What/Who is: '))
        # time.sleep(2)
        # buzzer = input('press ENTER for buzzer')
        talker.say_fast('speak in 2 seconds')
        user_response = recognize_speech(
            our_recognizer, our_microphone).replace('what is ', '').replace('who is ', '').replace('where is ', '').replace('a ', '').replace('what are ', '')
        try:
            print("You said: \"{}\"".format(user_response))
        except 'UnknownValueError':
            print("Speech not recognizable or API not available")
            # todo make the word comparison better, currently someone can guess a subset of a word to get an answer right
        if similarstring(user_response.lower(), answer.lower(), .80) and user_response.lower() in answer.lower():
            talker.say_fast(('CORRECT!, the answer is {}, we add ${} to your total').format(answer, value))
            player_1.add_funds(value)
        else:
            talker.say_fast(('INCORRECT, the answer is {}, we deduct ${} from your total').format(answer, value))
            player_1.add_funds(-value)
        talker.say_fast('${} is the total for {}'.format(player_1.money, player_1.name))
    game.conn.close()


if __name__ == '__main__':
    main()
