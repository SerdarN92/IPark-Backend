import pickle
import sys
import threading
import traceback

import pika

"""Service Base for Micro Service via RabbitMQ"""


class Service(threading.Thread):
    """Service Base for Micro Service via RabbitMQ"""

    def __init__(self, name=None):
        threading.Thread.__init__(self)

        self.name = name or self.__class__.__name__

        self.channel = None
        self.connection = pika.SelectConnection(
            pika.ConnectionParameters(host='132.252.152.56',
                                      credentials=pika.PlainCredentials('ipark', 'GS~FsB3~&c7T')),
            self.on_connected)
        self.start()

    def on_connected(self, connection):
        """RabbitMQ Connected"""
        connection.channel(self.on_channel_open)

    def on_channel_open(self, channel):
        """RabbitMQ Channel opened"""
        self.channel = channel

        self.channel.exchange_declare(self.on_exchange_declared, exchange="delayed-x", type="x-delayed-message",
                                      arguments={"x-delayed-type": "direct"}, )

        self.channel.queue_declare(self.on_queue_declared, queue=self.name)
        self.channel.queue_bind(self.on_queue_bind, queue=self.name, exchange="delayed-x", routing_key=self.name)
        self.channel.basic_consume(self.on_request, queue=self.name)

    def on_queue_declared(self, frame):
        pass

    def on_exchange_declared(self, *args, **kwargs):
        pass

    def on_queue_bind(self, *args, **kwargs):
        pass

    def run(self):
        """Start Serving Client Requests"""
        print(u"[{0:s}] Service running...".format(self.name))
        self.connection.ioloop.start()

    def on_request(self, ch, method, props, body):
        """Handle incoming Service Request"""
        request = pickle.loads(body)

        try:
            function = getattr(self, request['function'])
            result = {'result': function(*request['args'], **request['kwargs'])}
        except BaseException as ex:
            result = {'exception': ex, 'traceback': "".join(traceback.format_exception(*sys.exc_info()))}

        response = pickle.dumps(result)

        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(correlation_id=props.correlation_id),
                         body=response)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def stop(self):
        """Terminate Serving"""
        self.connection.close()
        self.join()
        self.run()
