# -*- coding: latin-1 -*-
import vk_api
import requests
from bs4 import BeautifulSoup
import re
from vk_api.longpoll import VkLongPoll, VkEventType
from datetime import datetime
from importlib import reload
import sys, os


reload(sys)
sys.setdefaultencoding('utf-8')

token = "1c089eedd463a37112c8a3911e68fb22f371c829ca4225ef31b9318858b732e5e0bc01a1fe5b591b2fecb"
vk_session = vk_api.VkApi(token=token)

session_api = vk_session.get_api()
longpoll = VkLongPoll(vk_session)

URL = 'https://kogda.by/'

HEADERS = {}
user_list = {}
user_id_list = []

transport_translator = {
    u'Автобус': 'autobus',
    u'Троллейбус': 'trolleybus',
    u'Трамвай': 'tram',
    u'Поезд/Электричка': 'all_train',
    u'Метро': 'metro'
}

city_translator = {
    u'Минск': 'minsk',
    u'Брест': 'brest',
    u'Витебск': 'vitebsk',
    u'Гродно': 'grodno',
    u'Гомель': 'gomel',
    u'Могилев': 'mogilev',
    u'Пинск': 'pinsk',
    u'Бобруйск': 'bobruisk',
    u'Барановичи':'baranovichi'
}

temp_stop_dict = []

basic_transport = {u'Автобус', u'Троллейбус', u'Трамвай', u'Метро'}

def get_html(url, params = None):
    data = requests.get(url, params = params)

    return data


def get_content(html, first_param, _class):
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.find_all(first_param, class_=_class)

    return items

def set_to_list(my_set):
    my_list = []

    for item in my_set:
        my_list.append(item)

    return my_list


def multiplicity_lower(list):
    #list to set and lower() function applied
    multiplicity = set()
    multiplicity = set([i.lower() for i in list])

    return multiplicity #return set()


def check_on_similar(List):
    # returned 0 - if not sililar items in list
    multiplicity = multiplicity_lower(List)

    if len(multiplicity) == len(List):
        return 0
    else:
        return 1


def multiplicity_upper(multiplicity):
    multiplicity = set_to_list(multiplicity)

    for index in range(len(multiplicity)):
        symb = multiplicity[index][0].upper()
        temp_str = symb + multiplicity[index][1:]
        multiplicity[index] = temp_str

        if '/' in multiplicity[index]:
            slash_index = multiplicity[index].index('/')
            symb = multiplicity[index][slash_index + 1].upper()
            temp_str = multiplicity[index][0:slash_index + 1] + symb + multiplicity[index][slash_index + 2:]
            multiplicity[index] = temp_str
    multiplicity = set(multiplicity)
    multiplicity = multiplicity & basic_transport
    multiplicity = set_to_list(multiplicity)
    return multiplicity


def get_cities(html, cities):
    cities_list = []
    cities_name = []
    for city in cities:

        transport = city.find('ul').get_text()
        transport = transport.replace("\n","").split()

        if check_on_similar(transport) == 1:
            transport = multiplicity_lower(transport)
            transport = multiplicity_upper(transport)

        cities_name.append(city.find('h4', class_='panel-title').get_text(strip = True))

        cities_list.append(
            {
                'city_name': city.find('h4', class_='panel-title').get_text(strip = True),
                'link': URL + city.find('a').get('href'),
                'transport': transport
            }
        )
    mydict = dict(zip(cities_name, cities_list))

    return mydict


def dict_checker(dictionary, key):
    if dictionary.get(key):
        return True
    else:
        return None


def get_transport_nums(link):
    html = get_html(link)
    nums_list = []
    content = get_content(html.text, 'a', 'btn btn-primary bold route')

    for item in content:
        nums_list.append(item.get_text(strip=True))
    return nums_list


def list_to_string(src_list, delim = ' '):
    string = ''
    for el in src_list:
        string += el + delim
    return string


def nums_list_to_message_format(src_list):
    string = ''
    for index in range(len(src_list)):
        string += src_list[index]
        if index % 4 == 0 and index != 0:
            string += '\n'
        else:
            string += '  '
    return string

def select_direction(link, event):
    List = get_stop(link, event)
    newList = []
    try:
        if int(event.text) == 1 or int(event.text) == 2:
            if int(event.text) == 1:
                newList = List[0:int(len(List) / 2) - 1]

            elif int(event.text) == 2:
                newList = List[0:int(len(List) / 2) - 1: -1]

            user_list[event.user_id]['stop'] = newList
            user_list[event.user_id]['depth'] += 1


            msg = "Выберите остановку:\n"
            number_item = 1
            for item in newList:
                msg += str(number_item) + ". " + item['name'] + "\n"
                number_item += 1
            vk_session.method('messages.send', {'user_id': event.user_id, 'message': msg, 'random_id': 0})

        else:
            print("Error")
    except:
        print("Error")

def get_stop(link, event):
    html = get_html(link)

    content = get_content(html.text, 'li', 'list-group-item')
    stop_List = []

    for item in content:
        stop_List.append({
        'name': item.find('a').get_text(strip=True),
        'link': item.find('a').get('href')
        })



    return stop_List

def get_timetable(link):
    html = get_html(link)
    content = get_content(html.text, 'div', 'text-center actions-block')
    url_to_timetable = ""
    for item in content:

        url_to_timetable = item.find('a', class_='btn btn-primary btn-wide btn-rounded desktop-wide').get('href')
        break

    html = get_html(url_to_timetable)
    content = get_content(html.text, 'span', 'time')

    timetable = []
    for time in content:
        timetable.append(time.get_text(strip=True))


    #
    return timetable


def view_timetable(event, index):

    timetable = get_timetable(user_list[event.user_id]['stop'][index]['link'])
    string = list_to_string(timetable)
    vk_session.method('messages.send', {'user_id': event.user_id, 'message': 'Расписание:\n' + string, 'random_id': 0})
    user_list[event.user_id]['depth'] = 0
    del user_list[event.user_id]
    user_id_list.remove(event.user_id)
    pass

def get_directrion(event):
    html = get_html(user_list[event.user_id]['link'])
    direction_html = get_content(html.text, 'h4', 'panel-title')
    directions = []

    for direction in direction_html:
        directions.append(direction.find('a').get_text(strip=True))


    return directions

def num_select(event):
    selected_num = event.text

    transport_nums = get_transport_nums(user_list[event.user_id]['link'])
    if selected_num == 'М1':
        selected_num = 'M1'
    elif selected_num == 'М2':
        selected_num = 'M2'
    print(selected_num)
    if selected_num in transport_nums:
        user_list[event.user_id]['link'] = user_list[event.user_id]['link'] + '/' + selected_num

        directions = get_directrion(event)
        msg = "1. " + directions[0] + "\n" + "2. " + directions[1]
        vk_session.method('messages.send', {'user_id': event.user_id, 'message': u"Выберите направление:\n" + msg, 'random_id': 0})
        user_list[event.user_id]['depth'] += 1

def stop_select(event):
    try:
        stop_number = int(event.text)
        if int(stop_number) > 0 and int(event.text) <= len(user_list[event.user_id]['stop']):
            view_timetable(event, stop_number)
        else:
            error = int("asd")
    except:
        print("Error")




def transport_select(cities_list, selected_city, event):

    if event.text == 'exit':
        user_list[event.user_id]['depth'] -= 1
    elif event.text in cities_list[selected_city]['transport']:
        print('Выбранный транспорт ' + str(event.text))
        user_list[event.user_id]['link'] = link = URL + '/routes/' + city_translator[selected_city] + '/' +  transport_translator[event.text]
        transport_nums = get_transport_nums(link)
        nums_msg = nums_list_to_message_format(transport_nums)
        vk_session.method('messages.send', {'user_id': event.user_id, 'message': "Выберите номер:\n" + nums_msg, 'random_id': 0})
        user_list[event.user_id]['transport'] = event.text
        user_list[event.user_id]['depth'] += 1

    else:
        print("Такого вида транспорта не существует")


def city_select(cities_list, event):
    if dict_checker(cities_list, event.text):
        print('Выбранный город: ' + str(event.text))
        selected_city = event.text
        string = list_to_string(cities_list[event.text]['transport'], '\n'
                                )
        vk_session.method('messages.send', {'user_id': event.user_id, 'message': "Выберите транспорт\n " + string + '\n Выбрать город заново(exit)', 'random_id': 0})
        user_list[event.user_id]['city'] = selected_city
        user_list[event.user_id]['depth'] += 1
    else:
        print('Такого города нет')


def parse():
    html = get_html(URL)
    if html.status_code == 200:
        cities_html = get_content(html.text, 'div', 'panel panel-default')
        cities_list = get_cities(html, cities_html)
        print(cities_list)

        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.from_user and not event.from_me:

                user_info = {
                    'city': None,
                    'transport': None,
                    'num': None,
                    'direction': None,
                    'stop': {},
                    'link': None,
                    'depth': 0
                }


                if event.user_id not in user_id_list:
                    user_list[event.user_id] = user_info
                    user_id_list.append(event.user_id)
                print(user_list[event.user_id])
                if user_list[event.user_id]['depth'] == 0:
                    city_select(cities_list, event)

                elif user_list[event.user_id]['depth'] == 1:
                    transport_select(cities_list, user_list[event.user_id]['city'], event)

                elif user_list[event.user_id]['depth'] == 2:
                    num_select(event)

                elif user_list[event.user_id]['depth'] == 3:
                    select_direction(user_list[event.user_id]['link'], event)

                elif user_list[event.user_id]['depth'] == 4:
                    stop_select(event)

    else:
        print("error 404")


parse()