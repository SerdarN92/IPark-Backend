import pickle
import threading
import time
import uuid

import pika


class Client:
    def __init__(self, name=None):
        self.name = name or self.__class__.__name__
        self.response = None
        self.corr_id = None

        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.channel = self.connection.channel()

        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(self.on_response, no_ack=True, queue=self.callback_queue)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = pickle.loads(body)
            self.corr_id = None

    def call(self, function, *args, **kwargs):
        if self.corr_id is not None:
            raise 0  # Todo

        request = pickle.dumps({'function': function, 'args': args, 'kwargs': kwargs}, pickle.HIGHEST_PROTOCOL)

        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(exchange='',
                                   routing_key=self.name,
                                   properties=pika.BasicProperties(reply_to=self.callback_queue,
                                                                   correlation_id=self.corr_id, ),
                                   body=request)
        while self.response is None:
            self.connection.process_data_events()
            self.connection.sleep(0.01)

        if 'exception' in self.response:
            raise self.response['exception']

        return self.response['result']
