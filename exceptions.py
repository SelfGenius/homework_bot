class ApiRequestError(Exception):
    """Ошибка запроса."""
    pass


class CurrentDateError(Exception):
    """Ошибка ключа current_date."""
    pass


class MessageNotSentError(Exception):
    """Ошибка отправки сообщение в телеграмм."""
    pass
