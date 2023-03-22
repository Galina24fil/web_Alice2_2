from flask import Flask, request
import logging
import json
import random

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

cities = {
    'москва': ['1652229/668c7cc8acab68093f5f',
               '1533899/b22df0bec60bdaf006bd'],
    'кострома': ['1533899/36baf3e89e046c2c8271',
                 '1656841/a8766f940816255c0b7e'],
    'одинцово': ["1533899/b874a02c205d8c069871",
                 '1533899/9c93c859e2552c591c88']
}
yes_no_but = [{'title': 'Да', 'hide': True}, {'title': 'Нет', 'hide': True}, {'title': 'Помощь', 'hide': True},
              {'title': 'Что ты умеешь?', 'hide': True}]

sessionStorage = {}


def get_city(req):
    # перебираем именованные сущности
    for entity in req['request']['nlu']['entities']:
        # если тип YANDEX.GEO, то пытаемся получить город(city), если нет, то возвращаем None
        if entity['type'] == 'YANDEX.GEO':
            # возвращаем None, если не нашли сущности с типом YANDEX.GEO
            return entity['value'].get('city', None)


def get_country(req):
    # перебираем именованные сущности
    for entity in req['request']['nlu']['entities']:
        # если тип YANDEX.GEO, то пытаемся получить город(city), если нет, то возвращаем None
        if entity['type'] == 'YANDEX.GEO':
            # возвращаем None, если не нашли сущности с типом YANDEX.GEO
            return entity['value'].get('country', None)


def get_first_name(req):
    # перебираем сущности
    for entity in req['request']['nlu']['entities']:
        # находим сущность с типом 'YANDEX.FIO'
        if entity['type'] == 'YANDEX.FIO':
            # Если есть сущность с ключом 'first_name', то возвращаем её значение.
            # Во всех остальных случаях возвращаем None.
            return entity['value'].get('first_name', None)


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
    logging.info('Response: %r', response)
    return json.dumps(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']
    if req['session']['new']:
        res['response']['text'] = 'Привет! Назови своё имя!'
        sessionStorage[user_id] = {
            'first_name': None,  # здесь будет храниться имя
            'game_started': False,  # здесь информация о том, что пользователь начал игру. По умолчанию False
            'attempt': 0,
            'guessed_cities': []
        }
        return

    if sessionStorage[user_id]['first_name'] is None:
        first_name = get_first_name(req)
        if first_name is None:
            res['response']['text'] = 'Не расслышала имя. Повтори, пожалуйста!'
        else:
            sessionStorage[user_id]['first_name'] = first_name
            # создаём пустой массив, в который будем записывать города, которые пользователь уже отгадал
            sessionStorage[user_id]['guessed_cities'] = []
            # как видно из предыдущего навыка, сюда мы попали, потому что пользователь написал своем имя.
            # Предлагаем ему сыграть и два варианта ответа "Да" и "Нет".
            res['response'][
                'text'] = f'Приятно познакомиться, {first_name.title()}. Я - Алиса. Отгадаешь город по фото?'
            res['response']['buttons'] = yes_no_but
    else:
        name = sessionStorage[user_id]['first_name'].capitalize()
        # У нас уже есть имя, и теперь мы ожидаем ответ на предложение сыграть.
        # В sessionStorage[user_id]['game_started'] хранится True или False в зависимости от того,
        # начал пользователь игру или нет.
        if not sessionStorage[user_id]['game_started']:
            # игра не начата, значит мы ожидаем ответ на предложение сыграть.
            if 'да' in req['request']['nlu']['tokens']:
                # если пользователь согласен, то проверяем не отгадал ли он уже все города.
                # По схеме можно увидеть, что здесь окажутся и пользователи, которые уже отгадывали города
                if len(sessionStorage[user_id]['guessed_cities']) == len(cities.keys()):
                    # если все три города отгаданы, то заканчиваем игру
                    res['response']['text'] = f'{name}, ты отгадал все города!'
                    res['response']['end_session'] = True
                else:
                    # если есть неотгаданные города, то продолжаем игру
                    sessionStorage[user_id]['game_started'] = True
                    # номер попытки, чтобы показывать фото по порядку
                    sessionStorage[user_id]['attempt'] = 1
                    # функция, которая выбирает город для игры и показывает фото
                    play_game(res, req)
            elif 'нет' in req['request']['nlu']['tokens']:
                res['response']['text'] = 'Ну и ладно!'
                res['response']['end_session'] = True
            elif 'помощь' in req['request']['nlu']['tokens']:
                res['response']['text'] = f'Памятка по использованию бота:\n' \
                                          f'Этот навык создан для угадывания городов по фото\n' \
                                          f'Отвечайте "Да" и "Нет" на вопросы или нажимайте на кнопку ' \
                                          f'и предлагайте название города)\n' \
                                          f'А еще я могу показать отгаданный город (или неугаданный)'
                res['response']['end_session'] = False
                res['response']['buttons'] = yes_no_but
            elif 'что' in req['request']['nlu']['tokens'] and 'ты' in req['request']['nlu']['tokens'] and 'умеешь' in \
                    req['request']['nlu']['tokens']:
                res['response']['text'] = f'Вот, что я могу:\n' \
                                          f'1) Предлагать фотографии разных городов\n' \
                                          f'2) Проверять правильность вашего ответа\n' \
                                          f'3) Показать город на карте\n' \
                                          f'Если у вас остались вопросы, нажмите кнопку "Помощь"'
                res['response']['end_session'] = False
                res['response']['buttons'] = yes_no_but
            elif 'покажи' in req['request']['nlu']['tokens'] and 'город' in req['request']['nlu']['tokens'] and 'на' in \
                    req['request']['nlu']['tokens'] and 'карте' in req['request']['nlu']['tokens']:
                res['response']['buttons'] = yes_no_but
                res['response']['end_session'] = False
                res['response']['text'] = f'{name}, сыграем ещё?'
            else:
                res['response']['text'] = f'{name}, не поняла ответа! Так да или нет?'
                res['response']['buttons'] = yes_no_but
        else:
            play_game(res, req)


def play_game(res, req):
    user_id = req['session']['user_id']
    attempt = sessionStorage[user_id]['attempt']
    name = sessionStorage[user_id]['first_name'].capitalize()
    global s
    if attempt == 1:
        # если попытка первая, то случайным образом выбираем город для гадания
        city = random.choice(list(cities))
        # выбираем его до тех пор пока не выбираем город, которого нет в sessionStorage[user_id]['guessed_cities']
        while city in sessionStorage[user_id]['guessed_cities']:
            city = random.choice(list(cities))
        # записываем город в информацию о пользователе
        sessionStorage[user_id]['city'] = city
        sessionStorage[user_id]['country'] = 'россия'
        # добавляем в ответ картинку
        res['response']['card'] = {}
        res['response']['card']['type'] = 'BigImage'
        res['response']['card']['title'] = f'{name}, что это за город?'
        res['response']['card']['image_id'] = cities[city][attempt - 1]
        res['response']['text'] = 'Тогда сыграем!'
        s = 0
    else:
        # сюда попадаем, если попытка отгадать не первая
        city = sessionStorage[user_id]['city']
        open_city = [{'title': 'Да', 'hide': True}, {'title': 'Нет', 'hide': True},
                     {'title': 'Покажи город на карте',
                      'url': f'https://yandex.ru/maps/?mode=search&text={city.title()}', 'hide': True},
                     {'title': 'Помощь', 'hide': True},
                     {'title': 'Что ты умеешь?', 'hide': True}]
        # проверяем есть ли правильный ответ в сообщение
        if s == 1:
            country = sessionStorage[user_id]['country']
            if country == get_country(req):
                res['response']['text'] = f'{name}, правильно! Сыграем ещё?'
                res['response']['buttons'] = open_city
                sessionStorage[user_id]['game_started'] = False
                s = 0
                return
            else:
                res['response']['text'] = f'{name}, вы не угадали! Этот город находится в России. Сыграем ещё?'
                res['response']['buttons'] = open_city
                sessionStorage[user_id]['game_started'] = False
                s = 0
                return
        if get_city(req) == city:
            # если да, то добавляем город к sessionStorage[user_id]['guessed_cities'] и
            # отправляем пользователя на второй круг. Обратите внимание на этот шаг на схеме.
            res['response']['text'] = f'{name}, правильно! А в какой стране этот город?'
            res['response']['buttons'] = []
            sessionStorage[user_id]['guessed_cities'].append(city)
            sessionStorage[user_id]['game_started'] = True
            s = 1
            return
        else:
            # если нет
            if attempt == 3:
                # если попытка третья, то значит, что все картинки мы показали.
                # В этом случае говорим ответ пользователю,
                # добавляем город к sessionStorage[user_id]['guessed_cities'] и отправляем его на второй круг.
                # Обратите внимание на этот шаг на схеме.
                res['response']['text'] = f'{name}, вы пытались. Это {city.title()}. Сыграем ещё?'
                sessionStorage[user_id]['game_started'] = False
                sessionStorage[user_id]['guessed_cities'].append(city)
                res['response']['buttons'] = open_city
                return
            else:
                # иначе показываем следующую картинку
                res['response']['card'] = {}
                res['response']['card']['type'] = 'BigImage'
                res['response']['card']['title'] = f'{name}, неправильно. Вот тебе дополнительное фото'
                res['response']['card']['image_id'] = cities[city][attempt - 1]
                res['response']['text'] = 'А вот и не угадал!'
    # увеличиваем номер попытки доля следующего шага
    sessionStorage[user_id]['attempt'] += 1


if __name__ == '__main__':
    app.run()
