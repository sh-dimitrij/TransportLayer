import threading
import time
import json
import requests
import codecs

from confluent_kafka import Consumer

from confluent_kafka.admin import AdminClient, NewTopic
from .logger import Logger


logger = Logger().get_logger(__name__)


GET_MESSAGE_INTERVAL = 3
BOOTSTRAP_SERVER = 'localhost:29092'
CONSUMER_TOPIC = "assembling_message_topic"
GROUP_ID = "assembling_message_id"
AUTO_OFFSET_RESET = 'earliest'
URL_RECIVE ="http://localhost:8081/receive"


class KafkaMessageConsumer(threading.Thread):
    def __init__(self, interval):
        threading.Thread.__init__(self)
        
        self.interval = interval

        self.consumer = Consumer({
            'bootstrap.servers': BOOTSTRAP_SERVER,
            'group.id': GROUP_ID,
            'auto.offset.reset': AUTO_OFFSET_RESET
        })
        self.consumer.subscribe([CONSUMER_TOPIC])

    def run(self):
        logger.info("Запущен косъюмер...")
        while True:
            messages = self.get_messages_from_kafka()
            if messages:
                self.process_messages(messages)
            time.sleep(self.interval)

    def get_messages_from_kafka(self):
        result_messages = []
        try: 
            while True:
                msg = self.consumer.poll(1.0)
                if msg is None:
                    break
                if msg.error():
                    logger.error("Ошибка чтения из kafla: {}".format(msg.error()))
                    break
                
                json_data = json.loads(msg.value().decode('utf-8'))
                result_messages.append(json_data)
        except Exception as e:
            logger.error(f"Error: {e}")
            return []

        return result_messages

    def process_messages(self, messages): 
        try:
            sorted_messages = sorted(messages, key=lambda x: (x['timestamp'], x['segment_number']))
            logger.info(f"Обработка {sorted_messages}")
            result_message = []
            
            prev_timestamp = None
            curr_sender = None
            curr_message = []

            prev_id = None
            had_error = False
            
            for message in sorted_messages:

                if prev_timestamp == message['timestamp']:
                    curr_message.extend(list(eval(message['message'])))
                    if prev_id + 1 != message['segment_number'] or message['had_error']:
                        had_error = True
                    prev_id = message['segment_number']
                else:
                    if prev_timestamp is not None:
                        if prev_id + 1 != message['total_segments']:
                            had_error = True
                        result_message.append(
                            {
                                "sender": curr_sender,
                                "timestamp": prev_timestamp,
                                "message": bytes(curr_message).decode("utf-8"),
                                "had_error": had_error,
                            }
                        )
                    had_error = False
                    prev_id = message['segment_number']
                    if prev_id != 0 or message['had_error']:
                        had_error = True
                    prev_timestamp = message['timestamp']
                    curr_message = list(eval(message['message']))
                    curr_sender = message['sender']

            if prev_timestamp is not None:
                if prev_id + 1 != message['total_segments']:
                    had_error = True
                result_message.append(
                    {
                        "sender": curr_sender,
                        "timestamp": prev_timestamp,
                        "message": bytes(curr_message).decode("utf-8"),
                        "had_error": had_error,
                    }
                )

            logger.info(f"Обработанные сообщения {result_message}")

            for mes in result_message:
                logger.info(f"Пробуем отправить {mes}")
                response = requests.post(URL_RECIVE, data=mes)
                if response.status_code != 200:
                    logger.info(f"Получен статуc {response.status_code} от прикладного уровня")
                logger.info("Сообщение успешно доставленно на прикладной уровень")
        except requests.exceptions.ConnectionError as e:
            pass
            #logger.error(f"Не получилось отпправить сообщение {e}")
        except Exception as e:
            logger.error(f"Ошибка обработки сообщений {e}")


def assembling_message():
    a = AdminClient({'bootstrap.servers': BOOTSTRAP_SERVER})

    new_topics = [NewTopic(topic, num_partitions=1, replication_factor=1) for topic in [CONSUMER_TOPIC]]
    fs = a.create_topics(new_topics)
    for topic, f in fs.items():
        try:
            f.result()
            logger.info("Топик {} успешно создан".format(topic))
        except Exception as e:
            logger.error("Ошибка создания топика {}: {}".format(topic, e))

    kafka_consumer = KafkaMessageConsumer(interval=GET_MESSAGE_INTERVAL)
    kafka_consumer.start()