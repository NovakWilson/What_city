from flask import Flask, request
import logging
import json
# импортируем функции из нашего второго файла geo
from geo import get_country, get_distance, get_coordinates
import os

app = Flask(__name__)

# Добавляем логирование в файл.
# Чтобы найти файл, перейдите на pythonwhere в раздел files,
# он лежит в корневой папке
logging.basicConfig(level=logging.INFO, filename='app.log',
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')

'''
git:
https://github.com/NovakWilson/What_city/tree/maps


Webhook URL:
https://whatcity2.herokuapp.com/post
'''

sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info('Request: %r', response)
    return json.dumps(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']
    if req['session']['new']:
        res['response']['text'] = 'Привет! Я могу показать город или сказать расстояние между городами! Назови себя'
        sessionStorage[user_id] = {
            'first_name': None,
            'game_started': False
        }
        return

    if sessionStorage[user_id]['first_name'] is None:
        first_name = get_first_name(req)
        if first_name is None:
            res['response']['text'] = 'Не расслышала имя. Повтори, пожалуйста!'
        else:
            sessionStorage[user_id]['first_name'] = first_name
            sessionStorage[user_id]['guessed_cities'] = []
            res['response']['text'] = 'Приятно познакомиться, ' \
                                      + first_name.title() \
                                      + '. Я - Алиса. Введи название одного или двух городов.'
            return
    else:
        cities = get_cities(req)
        if not cities:
            res['response']['text'] = '{}, вы не написали название не одного города!'.format(sessionStorage[user_id]['first_name'])
        elif len(cities) == 1:
            res['response']['text'] = '{1}, этот город в стране - {0}'.format(get_country(cities[0]), sessionStorage[user_id]['first_name'])
        elif len(cities) == 2:
            distance = get_distance(get_coordinates(
                cities[0]), get_coordinates(cities[1]))
            res['response']['text'] = '{}, расстояние между этими городами: {} км.'.format(sessionStorage[user_id]['first_name'], str(round(distance)))
        else:
            res['response']['text'] = '{}, вы вводите слишком много городов!'.format(sessionStorage[user_id]['first_name'])


def get_cities(req):
    cities = []
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.GEO':
            if 'city' in entity['value']:
                cities.append(entity['value']['city'])
    return cities


def get_first_name(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.FIO':
            return entity['value'].get('first_name', None)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
