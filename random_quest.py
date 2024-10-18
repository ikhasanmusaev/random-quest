import telebot
import redis
from deep_translator import GoogleTranslator

from random import randint, choice

import requests
from bs4 import BeautifulSoup

bot = telebot.TeleBot("2112349081:AAEtQUqwxGq0Bf58V-u2zmt-2EuJlHncpA0", parse_mode=None)
# bot = telebot.TeleBot("1378773433:AAHgkDMO01SZ5GNstTpBpbRnNJ4kfQA4LLs", parse_mode=None)
r = redis.Redis(host='localhost', port=6379, db=0)


def translate(text_input):
    translator = GoogleTranslator(target='uzbek')
    if not text_input:
        return text_input
    try:
        translation = translator.translate(text_input)
    except Exception as e:
        print(f'Error while translate: {e}')
        translation = text_input
    return translation


def get_soup(url):
    response = requests.get(url)

    return BeautifulSoup(response.text, 'html.parser')


def get_random_q(question_block):
    li_list = question_block.find_all('li')
    question = choice(li_list)
    return question


def get_random_text_q(questions):
    try:
        random_ol = choice(questions.find_all('ol'))
        random_qs = get_random_q(random_ol)
        qs_link = random_qs.findChild('a').attrs['href']
    except:
        qs_link = choice(questions.find_all('p')).findChild('a').attrs['href']

    soup_qs_page = get_soup(qs_link)

    return soup_qs_page


def select_qs(questions):
    get_qs_page = get_random_text_q(questions)
    questions_block = get_qs_page.find('div', attrs={'class': 'entry-content'})
    qs_list = questions_block.find_all('p', attrs={'class': 'has-black-color has-text-color'})
    _question = choice(qs_list)

    answers_text = get_qs_page.find('div', class_='sh-content post-content sh-hide').text

    return _question.text, answers_text


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Новый вопрос, /new. Текущий вопрос /question. Ответ /answer")


@bot.message_handler(commands=['new'])
def new_question(message):
    try:
        url = choice(['https://quizvopros.ru/', 'https://viktorinavopros.ru/'])
        all_questions = get_soup(url).find('div', {'class': ['wp-block-columns', 'is-layout-flex', 'wp-container-3']})

        text_of_qs, text_of_answers = select_qs(all_questions)
        number_of_quest = text_of_qs.split('.')[0]

        answers_list = [a.replace('\t', '') for a in text_of_answers.split('\n') if a]
        answer = ''
        for a in answers_list:
            if number_of_quest == a.split('.')[0]:
                answer = a

        r.set(str(message.chat.id) + 'question', text_of_qs)
        r.set(str(message.chat.id) + 'answer', answer)

        bot.reply_to(message, f'''
        Вопрос: {text_of_qs} \n Savol: {translate(text_of_qs).capitalize()}
        ''',)
    except Exception as e:
        print(e)
        bot.reply_to(message, 'Возникла ощибка, попробуйте чуть позже')


@bot.message_handler(commands=['answer'])
def answer(message):
    if message.chat.type != 'private' and message.from_user.id not in [x.user.id for x in bot.get_chat_administrators(message.chat.id)]:
        bot.reply_to(message, 'You are not an admin')
        return
    answer_text = r.get(str(message.chat.id) + 'answer')
    bot.reply_to(message, f'''
        Ответ: {answer_text.decode('utf-8')} \n Javob: {translate(answer_text.decode('utf-8')).capitalize()}'''
                 )


@bot.message_handler(commands=['question'])
def question(message):
    question_text = r.get(str(message.chat.id) + 'question')
    bot.reply_to(message, f'''
        Вопрос: {question_text.decode('utf-8')} \n Savol: {translate(question_text.decode('utf-8')).capitalize()}
        ''', )


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    if message.chat.type == 'private':
        bot.reply_to(message, '/start or /help')
    else:
        pass


bot.infinity_polling()

# if __name__ == '__main__':
#     url = 'https://quizbaza.ru/'
#     all_questions = get_soup(url).find_all('div', class_='wp-block-columns')[0]
#
#     text_of_qs, text_of_answers = select_qs(all_questions)
#     number_of_quest = text_of_qs.split('.')[0]
#
#     answers_list = [a.replace('\t', '') for a in text_of_answers.split('\n') if a]
#     answer = ''
#     for a in answers_list:
#         if number_of_quest == a.split('.')[0]:
#             answer = a
#
#     print(text_of_qs, '\n\n')
#     print(answer)
