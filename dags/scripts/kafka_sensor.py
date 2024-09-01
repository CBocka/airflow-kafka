from airflow.sensors.base import BaseSensorOperator
from confluent_kafka import Consumer, KafkaException
import logging

class KafkaSensor(BaseSensorOperator):
    def __init__(self, topic, kafka_bootstrap_servers, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.topic = topic
        self.kafka_bootstrap_servers = kafka_bootstrap_servers  

    def poke(self, context):
        consumer_config = {
            'bootstrap.servers': self.kafka_bootstrap_servers,
            'group.id': 'sensor-group',
            'auto.offset.reset': 'latest'
        }

        consumer = Consumer(consumer_config)
        consumer.subscribe([self.topic])

        logging.info("Sensor subscrito al topic.")

        try:
            message = consumer.poll()
            if message is None:
                logging.info("No se encontraron mensajes, continuará esperando.")
                return False

            if message.error():
                raise KafkaException(message.error())

            logging.info(f"Mensaje recibido: {message.value().decode('utf-8')}")

            return True

        except KafkaException as e:
            logging.error(f"Error en el sensor Kafka: {e}")
            return False

        finally:
            consumer.close()


