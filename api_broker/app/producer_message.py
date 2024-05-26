import json

from confluent_kafka import Producer

from .logger import Logger


logger = Logger().get_logger(__name__)
CONSUMER_TOPIC = "assembling_message_topic"


class KafkaMessageProducer():
    def __init__(self):
        self.producer = Producer({'bootstrap.servers': 'localhost:29092'})

    @staticmethod
    def _delivery_report(err, msg):
        """ Called once for each message produced to indicate delivery result.
            Triggered by poll() or flush(). """
        if err is not None:
            logger.error('Сообщение не доставлено: {}'.format(err))
        else:
            logger.info('Сообщение доставлено в {}, партиция {}'.format(msg.topic(), msg.partition()))
    
    def produced_data(self, buffer: list[dict]):
        try:
            for data in buffer:
                self.producer.poll(0)
                json_data = json.dumps(data)
                self.producer.produce(
                    CONSUMER_TOPIC,
                    json_data.encode('utf-8'),
                    callback=self._delivery_report
                )
            self.producer.flush()
        except Exception as e:
            logger.error(f"Ошибка в продъюсере: {e}")
