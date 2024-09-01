from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from scripts.kafka_sensor import KafkaSensor
from datetime import datetime

from confluent_kafka import Consumer, KafkaException
import logging
import json


def consume_kafka_message():

    consumer_config = {
        'bootstrap.servers': 'kafka:9092',
        'group.id': 'my-group', 
        'auto.offset.reset': 'latest'
    }

    consumer = Consumer(consumer_config)

    topic = 'my-topic'
    consumer.subscribe([topic])

    try:
        message = consumer.poll(timeout=100.0)

        if message is None:
            logging.info("No se encontraron mensajes.")
            return
        
        if message.error():
            raise KafkaException(message.error())

        received_message = message.value().decode('utf-8')

        try:
            received_message = json.loads(received_message)
        except json.JSONDecodeError as e:
            logging.error(f"Error al decodificar JSON: {e}")
            return
        
        process_id = received_message.get('processId')
        raw_start_time = received_message.get('startTime')
        start_time = raw_start_time.split(' ')[0] if ' ' in raw_start_time else raw_start_time
        
        logging.info(f"processId --> <{process_id}>")
        logging.info(f"startTime --> <{start_time}>")

    except KafkaException as e:
        logging.error(f"Error al consumir mensaje de Kafka: {e}")
    finally:
        consumer.close()



default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023, 1, 1),
    'retries': 1,
}

dag = DAG(
    'kafka_consumer_dag_sensor',
    default_args=default_args,
    schedule_interval= None,
    catchup=False,
)

kafka_sensor = KafkaSensor(
    task_id='kafka_sensor',
    mode='poke',  # Poke mode (polling)
    timeout=300,  # Timeout para el sensor en segundos
    poke_interval=30,  # Intervalo de polling en segundos
    kafka_bootstrap_servers='kafka:9092',
    topic='my-topic',
    dag=dag,
)

consume_task = PythonOperator(
    task_id='consume_kafka_message',
    python_callable=consume_kafka_message,
    dag=dag,
)


kafka_sensor >> consume_task