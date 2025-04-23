import os
from datetime import datetime
import inspect

from docs.utils.logger import setup_logger
from docs.utils. colored_print import print_lblue

"""
Содержит в себе функции-декораторы
"""


def timing_decorator_text_name(text: str = ""):
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Определяем файл, откуда вызывается декорируемая функция
            caller_frame = inspect.stack()[1]
            module_filename = caller_frame.filename
            module_name = os.path.splitext(os.path.basename(module_filename))[0]
            logging = setup_logger(module_name)

            # Замер времени выполнения
            start_time = datetime.now()
            result = func(*args, **kwargs)
            end_time = datetime.now()
            execution_time = end_time - start_time

            # Логируем с указанием вызвавшего модуля
            logging.info(
                f"{func.__name__} - {text} {args[0] if args else ''} - Выполнено за {execution_time}")
            return result

        return wrapper

    return decorator


def timing_decorator_text(text: str = ""):
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Определяем файл, откуда вызывается декорируемая функция
            caller_frame = inspect.stack()[1]
            module_filename = caller_frame.filename
            module_name = os.path.splitext(os.path.basename(module_filename))[0]
            logging = setup_logger(module_name)

            # Замер времени выполнения
            start_time = datetime.now()
            result = func(*args, **kwargs)
            end_time = datetime.now()
            execution_time = end_time - start_time

            # Логируем с указанием вызвавшего модуля
            logging.info(
                f"{func.__name__} - {text} - Выполнено за {execution_time}")
            return result

        return wrapper

    return decorator


def print_time_with_text(func):
    def wrapper(*args, **kwargs):
        # print_lblue(f"Произошел запуск функции - {func.__name__}")
        func_start = datetime.now()
        result = func(*args, **kwargs)
        func_end = datetime.now()
        func_run_time = func_end - func_start
        if func_run_time:
            print_lblue(f"Функция {func.__name__} отработала за {func_run_time.total_seconds() * 1000} милисекунд")
        return result
    return wrapper
