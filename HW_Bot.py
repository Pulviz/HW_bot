import os
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from bs4 import BeautifulSoup
import requests
from datetime import datetime
from threading import Thread


token = "c7974328168f8d8d0a46d707d25f175c314e3a46dea31708aa2452845b8037d9f4735ccd2cb98623ce65a"
vk_group_id = 210986020
vk_session = vk_api.VkApi(token=token)
vk_session.get_api()
longpool = VkBotLongPoll(vk_session, vk_group_id)
commands = ["дз", "123", "расписание", "очистка"]
days = ["понедельник", "вторник", "среда", "четверг", "пятница"]
threads = [True, True, True, True]
admins = open("admins.txt").readlines()
for i in range(len(admins)):
    num = admins[i]
    if "\n" in num:
        admins[i] = num[:-1]
vip_users = open("vip_users.txt").readlines()
for i in range(len(vip_users)):
    num = vip_users[i]
    if "\n" in num:
        vip_users[i] = num[:-1]
timetable = {
    "русский язык": [2, 4, 5],
    "алгебра": [1, 2, 5],
    "физика": [3, 4],
    "химия": [5],
    "английский язык": [1, 2, 3],
    "геометрия": [3],
    "история": [2, 3],
    "биология": [1],
    "литература": [1, 3],
    "обж": [4],
    "информатика": [1],
    "география": [5],
    "обществознание": [2, 4],
    "вероятность и статистика": [3]
}
print(vip_users)


def get_time():
    req = requests.get("https://my-calend.ru")
    bs = BeautifulSoup(req.text, "html.parser")
    time = clean_all_tag_from_str(str(bs.findAll("p"))).split()[3]
    result = ""
    for c in time:
        if c.isdigit():
            result += str(c)
    return int(result)


def clean_all_tag_from_str(string_line):
    result = ""
    flag = True
    for i in list(string_line):
        if flag:
            if i == "<":
                flag = False
            else:
                result += i
        else:
            if i == ">":
                result += " "
                flag = True
    return result


def send_msg(user, message):
    vk_session.method('messages.send', {'user_id': user, 'message': str(message), 'random_id': 0})


def wait(user):
    for event in longpool.listen():
        if event.type == VkBotEventType.MESSAGE_NEW and user == event.object.message['from_id']:
            return event


def read_files(file, day=""):
    result = ""
    with open(file + ".txt", "r", encoding='utf-8') as f:
        if day == "":
            for line in f.readlines():
                result += line
        else:
            flag = False
            for line in f.readlines():
                if line[:-1].lower() == day:
                    flag = True
                elif line[:-1].lower() in days:
                    flag = False
                if flag and line != "":
                    result += line
    return result


def homework():
    days_to = 1
    if datetime.now().strftime("%A") == "Friday":
        days_to = 3
    elif datetime.now().strftime("%A") == "Saturday":
        days_to = 2
    if os.path.isfile(f"days/{str(get_time() + days_to)}.txt"):
        return read_files(f"days/{str(get_time() + days_to)}")
    else:
        return "Ничего не задано"


def admin(user):
    if str(user) in admins:
        send_msg(user, "Введите название предмета")
        subject = wait(user).object.message['text'].lower()
        if subject in timetable:
            week = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
            today = datetime.now().strftime("%A")
            temp = week.index(today)
            day = 0
            counter = 0
            for i in range(temp + 1, temp + 8):
                counter += 1
                if i % 7 in timetable[subject]:
                    day = get_time() + counter
                    break
            arg = ""
            if os.path.isfile(f"days/{day}.txt"):
                arg = "a"
            else:
                arg = "w"
            with open(f"days/{day}.txt", arg) as f:
                send_msg(user, "Введите домашние задание")
                f.write(f"{subject}: {str(wait(user).object.message['text'])}\n")
        elif subject != "x":
            send_msg(user, "Предмет введен неверно")
            admin(user)
        return "Подтвержденно"
    return "???"


def time_table(request):
    req = request.split()
    if req[0].lower() == commands[2] and len(req) > 1:
        num = ""
        char = 0
        day = ""
        for c in req[1]:
            if c.isdigit():
                num += c

        if (len(req[1]) == 2 and len(num) == 1) or (len(req[1]) == 3 and len(num) == 2):
            if req[1][-1].lower() == "а":
                char = 1
            elif req[1][-1].lower() == "б":
                char = 2
        elif len(req[1]) == 2 and len(num) == 2:
            char = 1

        if len(req) == 3 and req[2].lower() in days:
            day = req[2].lower()

        if os.path.isfile(f"TimeTables/{num}_{char}.txt"):
            return read_files(f"TimeTables/{num}_{char}", day)
        else:
            return "???"
    else:
        return "???"


def clear(user):
    if str(user) in admins:
        files = os.listdir("days")
        today = get_time()
        for c in files:
            if int(c[:-4]) < today:
                os.remove("days/" + c)
        return "Очистка завершена"
    else:
        return "???"


def new_message(message, user):
    if str(user) not in vip_users:
        return time_table(message)
    elif message.lower() == commands[0]:
        return homework()
    elif message.lower() == commands[1]:
        return admin(user)
    elif message.split()[0].lower() == commands[2]:
        return time_table(message)
    elif message.lower() == commands[3]:
        return clear(user)
    else:
        return "???"


def start(event, thread):
    request = event.object.message['text']
    user_id = event.object.message['from_id']
    print(f"{user_id} : {request}")
    send_msg(user_id, new_message(request, user_id))
    threads[thread] = True


print("Successful")
while True:
    try:
        for event in longpool.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                if threads[0]:
                    threads[0] = False
                    t1 = Thread(target=start, args=(event, 0))
                    t1.start()
                elif threads[1]:
                    threads[1] = False
                    t2 = Thread(target=start, args=(event, 1))
                    t2.start()
                elif threads[2]:
                    threads[2] = False
                    t3 = Thread(target=start, args=(event, 2))
                    t3.start()
                elif threads[3]:
                    threads[3] = False
                    t4 = Thread(target=start, args=(event, 3))
                    t4.start()
                else:
                    send_msg(event.object.message['from_id'], "Слишком много запросов, повторите попытку позже")
    except Exception as e:
        print(e)
