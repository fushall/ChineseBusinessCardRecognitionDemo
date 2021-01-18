import os

KAFKA_HOST = os.getenv('KAFKA_HOST', '192.168.8.124')
KAFKA_CONSUMER_TOPIC = os.getenv('KAFKA_CONSUMER_TOPIC', 'card_recognition_source')
KAFKA_PRODUCER_TOPIC = os.getenv('KAFKA_PRODUCER_TOPIC', 'card_recognition_target')
