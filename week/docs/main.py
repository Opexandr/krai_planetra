"""RabbitMQ"""
import datetime
import json
import time
from datetime import datetime
import threading
import pika

from docs.database import settings, Serialize


queue = "krai_requests"


def str_to_date(start_date):
    """
    Переводит строку в datetime
    """
    if start_date and '.' in start_date:
        start_date = start_date[:start_date.index('.')]
    if start_date and isinstance(start_date, str):
        if 'Z' in start_date:
            start_date = start_date[:-1]
        start_date = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S")
    return start_date


def publish_message(msg, queues="krai_out"):
    message_params = {
        'msg_out': msg
    }

    # Сериализуем словарь в строку JSON
    for q in queues:
        msg_out = json.dumps(message_params)
        connection, new_channel = create_connection()
        if not connection or not new_channel:
            print("Ошибка: Не удалось подключиться для обработки сообщения")
            return
        try:
            new_channel.queue_declare(queue=q, durable=True)
            new_channel.basic_publish(exchange='', routing_key=q, body=msg_out)
        except Exception as e:
            print('чет не отправилось :c')
            print(e)
        finally:
            new_channel.close()
            connection.close()



def process_message(message, queue):
    print("process_message")
    connection, new_channel = create_connection()
    if not connection or not new_channel:
        print("Ошибка: Не удалось подключиться для обработки сообщения")
        return
    try:
        print("Смотрим что запускать")

        data = json.loads(message)  # Разбираем JSON
        command = data.get('requests')
        print(command)
        msg_out = ''
        print(f"{message}")
        start_date = str_to_date(data.get("start_data"))
        start_date = datetime(year=start_date.year, month=start_date.month, day=start_date.day, hour=0)
        Serialize.start_date = start_date
        Serialize.command = command
        q = []

        match Serialize.get_command():
            case "Трехмесячный оптимизатор":
                print(f"Запуск {Serialize.get_command()}")
                from docs.optimizer import three_month_start
                plan_id = data.get("digital_twin")
                three_month_start(plan_id)
                msg_out = "three_month_done"
                q = ["krai_out"]
                print("очистка")
            case "Недельный оптимизатор":
                print(f"Запуск {Serialize.get_command()}")
                from docs.optimizer import week_start
                plan_id = data.get("digital_twin")
                week_start(plan_id)
                msg_out = "week_done"
                q = "week_out"
                print("очистка")
            case "Оптимизатор поставок":
                print(f"Запуск {Serialize.get_command()}")
                from docs.optimizer import optimize_supplies
                optimize_supplies()
                msg_out = "sups_done"
                q = ["sups_out"]
            case _:
                print("Неправильное сообщение")


        # Отправляем сообщение в очередь
        publish_message(msg_out, q)
    except Exception as e:
        print(e)
    finally:
        new_channel.close()
        connection.close()
        print("Соединение закрыто.")


def callback(channel, method, properties, body):
    global queue

    print('callback')
    message = body.decode('utf-8')
    print(message)
    thread = threading.Thread(target=process_message, args=(message, queue))
    thread.start()


# Создаём соединение с RabbitMQ
def create_connection():
    credentials = pika.PlainCredentials(settings.RMQ_USER.get_secret_value(), password=settings.RMQ_PASS.get_secret_value())
    parameters = pika.ConnectionParameters(host=settings.RMQ_HOST.get_secret_value(), credentials=credentials)

    attempt = 0
    while attempt < 5:
        try:
            connection = pika.BlockingConnection(parameters)
            return connection, connection.channel()
        except pika.exceptions.AMQPConnectionError as e:
            print(f"Ошибка подключения (попытка {attempt + 1}/5): {e}")
            attempt += 1
            time.sleep(5)

    print("Не удалось подключиться к RabbitMQ.")
    return None, None


# Настраиваем подписку на очереди
def consume_messages():
    global queue
    while True:
        connection, channel = create_connection()
        if not connection or not channel:
            time.sleep(10)
            continue

        print("Подключено к RabbitMQ. Ожидание сообщений...")


        try:
            channel.queue_declare(queue=queue, durable=True)
            channel.basic_consume(
                queue=queue,
                on_message_callback=callback,
                auto_ack=True
            )
        except pika.exceptions.ChannelClosedByBroker:
            print(f"Ошибка доступа к очереди {queue}. Возможно, недостаточно прав.")

        try:
            channel.start_consuming()
        except pika.exceptions.AMQPConnectionError:
            print("Соединение потеряно. Переподключение...")
        finally:
            channel.close()
            connection.close()
            print("Соединение закрыто.")


# Запуск слушателя RabbitMQ
consume_messages()
#process_message('', 'q')
