import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

import logging

load_dotenv()

logger = logging.getLogger(__name__)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, text=message)
        logger.info(f'Сообщение в чат {TELEGRAM_CHAT_ID}: {message}')
    except telegram.error.TelegramError(message):
        logger.error(f'Ошибка отправки сообщения:{message}', exc_info=True)


def get_api_answer(current_timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time())
    kwargs = dict(
        url=ENDPOINT,
        headers=HEADERS,
        params={'from_date': timestamp}
    )
    try:
        homework_statuses = requests.get(**kwargs)

        if homework_statuses.status_code != HTTPStatus.OK:
            status_code = homework_statuses.status_code
            raise Exception(f'Ошибка {status_code}')
        return homework_statuses.json()
    except Exception as error:
        logging.error(error, exc_info=True)
        raise Exception(f'Ошибка при получении ответа с сервера: {error}')


def check_response(response):
    """Проверяет ответ API на корректность."""
    if not isinstance(response, dict):
        raise TypeError('Ответ API отличен от словаря')
    homeworks_list = response.get('homeworks')
    if homeworks_list is None:
        raise Exception('В ответе API нет словаря с домашками')
    if len(homeworks_list) == 0:
        raise Exception('За последнее время домашек нет')
    if not isinstance(homeworks_list, list):
        raise Exception('Ответ API отличен от списка')
    return homeworks_list


def parse_status(homework):
    """Извлекает информацию о статусе домашней работе статус."""
    homework_name = homework.get('homework_name')
    if homework_name is None:
        raise KeyError('Отсутствует ключ "homework_name" в ответе API')
    homework_status = homework.get('status')
    if homework_status is None:
        raise KeyError('Отсутствует ключ "status" в ответе API')
    if homework_status not in HOMEWORK_VERDICTS:
        raise KeyError(f'Неизвестный статус работы: {homework_status}')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


# маин начал делать
def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('Отсутствуют одна или несколько переменных окружения')
        sys.exit('Отсутствуют одна или несколько переменных окружения')
    # дальше изменеий нет
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    STATUS = ''
    ERROR_CACHE_MESSAGE = ''

    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response.get('current_date')
            message = parse_status(check_response(response))
            if message != STATUS:
                send_message(bot, message)
                STATUS = message
            time.sleep(RETRY_TIME)
        except Exception as error:
            logger.error(error)
            message_t = str(error)
            if message_t != ERROR_CACHE_MESSAGE:
                send_message(bot, message_t)
                ERROR_CACHE_MESSAGE = message_t
        time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format=('%(asctime)s,'
                ' %(levelname)s,'
                ' %(message)s,'
                ' %(funcName)s,'
                ' %(lineno)d'),
        encoding='UTF-8',
        handlers=[logging.FileHandler(
            'logging/main.log',
            mode='w',
            encoding='UTF-8'),
            logging.StreamHandler(sys.stdout)])
    main()
