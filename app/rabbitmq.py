"""
RabbitMQ client for the ingestion service.
"""

import json
import threading
import pika

from app.settings import settings


class RabbitMQClient:
    """
    RabbitMQ client for the ingestion service.
    """

    def __init__(self, url: str):
        self.url = url
        self.connection = None
        self.channel = None
        self._lock = threading.Lock()

    def connect(self):
        """
        Connect to the RabbitMQ server.
        """
        self.connection = pika.BlockingConnection(pika.URLParameters(self.url))
        self.channel = self.connection.channel()

        self.channel.exchange_declare(
            exchange=settings.rabbitmq_queue, exchange_type="direct", durable=True
        )
        self.channel.queue_declare(queue=settings.rabbitmq_queue, durable=True)
        self.channel.queue_bind(
            queue=settings.rabbitmq_queue,
            exchange=settings.rabbitmq_queue,
            routing_key=settings.rabbitmq_queue,
        )

    def _ensure_connected(self):
        """
        Ensure that the connection is established.
        """
        if self.connection is None or self.connection.is_closed:
            self.connect()
        elif self.channel is None or self.channel.is_closed:
            self.channel = self.connection.channel()

    def send_message(self, exchange, routing_key, message):
        """
        Send a message to the RabbitMQ server.
        """
        with self._lock:
            self._ensure_connected()
            self.channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2, content_type="application/json"
                ),
            )


mq_client = RabbitMQClient(url=settings.rabbitmq_url)
