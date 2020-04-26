#!/usr/bin/env python3
import time
from datetime import datetime
import codecs
import sys
from flask import Flask, request, send_file
from threading import Thread

app = Flask(__name__)
port_id = 5000
end = False
level = 1
score = 0
sended = False
level_change = False
users = {'root': '2'}
messages = []
hints = {1: '1',
         2: '1',
         3: '2',
         4: '1',
         5: '1',
         6: '1',
         7: '1'
         }
files = {
    1: False,
    2: 'jpg',
    3: False,
    4: 'jpg',
    5: 'txt',
    6: False,
    7: 'jpg'
}


def end_func():
    if level == 8:
        global end
        end = True
        messages.append(
            {"username": "SYSTEM", "text": "Поздравляем вас с успешным завершением заданий", "time": time.time()})
        messages.append(
            {"username": "SYSTEM", "text": "Позже будет загружено больше заданий", "time": time.time()})
        messages.append(
            {"username": "SYSTEM", "text": "Следите за новостями в группе ИИТиАД ИРНИТУ", "time": time.time()})


def score_write(sender):
    with codecs.open("./score.txt", "a", "utf-8") as file:
        file.write("Счёт: " + str(score) + " Уровень: " + str(level) + " Время: " + str(
            datetime.now().strftime('%d/%m/%Y %H:%M:%S') + " Отправитель: " + sender) + "\n")


def bad_answer():
    global sended
    sended = True
    score_write("bad_answer")
    messages.clear()
    messages.append({"username": "CHARON", 'text': 'Ответ неверный', 'time': time.time()})


def good_answer():
    global sended
    sended = True
    global level
    level += 1
    global level_change
    level_change = True
    global score
    score += 1
    score_write("good_answer")
    messages.clear()
    messages.append({"username": "CHARON", 'text': 'Ответ принят', 'time': time.time()})
    post()
    end_func()


def post():
    global sended
    sended = True
    file = codecs.open("./levels/" + str(level - 1) + "/" + str(level - 1) + "_post.txt", "r", "utf-8")
    for line in file.readlines():
        messages.append({'username': 'PROMETHEUS', 'text': line, 'time': time.time()})


def messages_for_current_task():
    task = []
    file = codecs.open("./levels/" + str(level) + "/" + str(level) + "_task.txt", "r", "utf-8")
    for line in file.readlines():
        task.append({'username': 'CHARON', 'text': line, 'time': time.time()})
    return task


def hint_for_current_task(number):
    global sended
    sended = True
    global score
    score -= 0.3
    score_write("hint_answer")
    messages.clear()
    file = codecs.open("./levels/" + str(level) + "/" + str(level) + "_hint_" + number + ".txt", "r", "utf-8")
    for line in file.readlines():
        messages.append({'username': 'CHARON', 'text': line, 'time': time.time()})


def answer_for_current_task():
    with codecs.open("./levels/" + str(level) + "/" + str(level) + "_answer.txt", "r", "utf-8") as file:
        answer = [row.strip() for row in file]
    return answer


@app.route("/")
def hello_view():
    return {'answer': sended}


@app.route("/status")
def status_view():
    return {
        'status': True,
        'time': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        'level': level,
        'end':end
    }


@app.route("/task")
def task_0():
    if end:
        return {}
    else:
        global sended
        sended = False
        global level_change
        level_change = False
        if files[level] != False:
            down = files[level]
        else:
            down = False
        return {'messages': messages_for_current_task(), 'down': down}


@app.route("/messages")
def messages_view():
    global sended
    sended = False
    return {'messages': messages, 'level++': level_change}


@app.route("/send", methods=['POST'])
def send_view():
    """
    Отправка сообщений
    input: {
        "username": str,
        "password": str,
        "text": str
    }
    output: {"ok": bool}
    """
    data = request.json
    username = data["username"]
    password = data["password"]
    text = data["text"]
    if username not in users or users[username] != password:
        return {"ok": False}
    if 'hint' in text:
        if '1' in text:
            hint_for_current_task('1')
            return {'ok': True}
        elif '2' in text:
            try:
                hint_for_current_task('2')
            except:
                messages.append(
                    {'username': 'SYSTEM', 'text': 'Доступных подсказок для задания: ', 'time': time.time()})
                messages.append({'username': 'SYSTEM', 'text': hints[level], "time": time.time()})
                messages.append({'username': 'SYSTEM', 'text': 'Чтобы получить подсказку введите hint #номер_подсказки',
                                 'time': time.time()})
            finally:
                return {'ok': True}
        else:
            messages.clear()
            global sended
            sended = True
            messages.append({'username': 'SYSTEM', 'text': 'Доступных подсказок для задания: ', 'time': time.time()})
            messages.append({'username': 'SYSTEM', 'text': hints[level], "time": time.time()})
            messages.append({'username': 'SYSTEM', 'text': 'Чтобы получить подсказку введите hint #номер_подсказки',
                             'time': time.time()})
            return {'ok': True}

    else:
        text = data["text"]
        if text in answer_for_current_task():
            good_answer()
        else:
            bad_answer()
        return {'ok': True}


@app.route("/auth", methods=['POST'])
def auth_view():
    """
    Авторизовать пользователя или сообщить что пароль неверный.
    input: {
        "username": str,
        "password": str
    }
    output: {"ok": bool}
    """
    data = request.json
    username = data["username"]
    password = data["password"]
    if username not in users:
        return {"ok": False}
    elif users[username] == password:
        return {"ok": True}
    else:
        return {"ok": False}


@app.route("/download")
def download():
    score_write("download")
    data = request.args
    task = data["task"]
    affix = data["affix"]
    return send_file("./download/" + task + "." + affix)


@app.route("/test")
def test_view():
    return{}


app.run(host='0.0.0.0', port=port_id)
