import logging
from colorlog import ColoredFormatter


def setup_logger(name=''):
    # Создаем цветной форматтер
    formatter = ColoredFormatter(
        "%(log_color)s%(levelname)s%(reset)s - %(asctime)s - %(name_log_color)s%(name)s - %(message_log_color)s%(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={
            'message': {
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            },
            'name': {
                'DEBUG': 'purple',
                'INFO': 'purple',
                'WARNING': 'purple',
                'ERROR': 'purple',
                'CRITICAL': 'purple',
            }
        },
        style='%'
    )

    # Создаем логгер
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Удаляем все старые обработчики
    while logger.handlers:
        logger.handlers.pop()

    # Создаем обработчик
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)

    # Добавляем обработчик к логгеру
    logger.addHandler(handler)

    return logger
