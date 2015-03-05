import pika
class RabbitInterface(object):
    def __init__(self):
        connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.basic_publish(exchange='',
            routing_key='hello',
            body='Hello World!')
        print " [x] Sent 'Hello World!'"
        connection.close()
