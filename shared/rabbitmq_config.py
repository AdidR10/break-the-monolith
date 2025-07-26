import pika
import json
import os
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class RabbitMQConfig:
    def __init__(self):
        self.host = os.getenv("RABBITMQ_HOST", "localhost")
        self.port = int(os.getenv("RABBITMQ_PORT", "5672"))
        self.username = os.getenv("RABBITMQ_USERNAME", "guest")
        self.password = os.getenv("RABBITMQ_PASSWORD", "guest")
        self.connection = None
        self.channel = None
        
    def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            credentials = pika.PlainCredentials(self.username, self.password)
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                credentials=credentials
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare exchanges and queues
            self._setup_exchanges_and_queues()
            logger.info("Connected to RabbitMQ successfully")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    def _setup_exchanges_and_queues(self):
        """Setup exchanges and queues for the application"""
        # Declare exchanges
        self.channel.exchange_declare(exchange='rides', exchange_type='topic', durable=True)
        self.channel.exchange_declare(exchange='notifications', exchange_type='topic', durable=True)
        self.channel.exchange_declare(exchange='payments', exchange_type='topic', durable=True)
        
        # Declare queues
        queues = [
            'ride.requested',
            'ride.accepted',
            'ride.started',
            'ride.completed',
            'ride.cancelled',
            'notification.email',
            'notification.sms',
            'notification.push',
            'payment.processed',
            'payment.failed'
        ]
        
        for queue in queues:
            self.channel.queue_declare(queue=queue, durable=True)
    
    def publish_message(self, exchange: str, routing_key: str, message: Dict[Any, Any]):
        """Publish message to RabbitMQ"""
        try:
            if not self.channel:
                self.connect()
                
            self.channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type='application/json'
                )
            )
            logger.info(f"Message published to {exchange}.{routing_key}")
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            raise
    
    def close(self):
        """Close RabbitMQ connection"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()

# Global instance
rabbitmq = RabbitMQConfig() 