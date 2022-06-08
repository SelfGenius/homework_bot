class ApiRequestError(Exception):
    """Ошибка запроса."""


class CurrentDateError(Exception):
    """Ошибка ключа current_date."""


class MessageNotSentError(Exception):
    """Ошибка отправки сообщение в телеграмм."""
