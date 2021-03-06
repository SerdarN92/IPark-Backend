import pickle
import threading
import uuid

import pika

"""Client Base for Micro Service via RabbitMQ"""


class Client(threading.Thread):
    """Client Base for Micro Service via RabbitMQ"""

    def __init__(self, name=None):
        super(Client, self).__init__()

        self.name = name or self.__class__.__name__
        self.responses = {}
        self.corr_ids = []

        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='132.252.152.56',
                                      credentials=pika.PlainCredentials('ipark', 'GS~FsB3~&c7T')))
        self.channel = self.connection.channel()

        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(self.on_response, no_ack=True, queue=self.callback_queue)

        self.start()

    def on_response(self, ch, method, props, body):
        """Handle respose and pass back to caller (internal use)"""
        if props.correlation_id in self.corr_ids:
            self.responses[props.correlation_id] = pickle.loads(body)
            self.corr_ids.remove(props.correlation_id)

    def delayed_call(self, function, delay_time, *args, **kwargs):
        """Schedule delayed Service Routine Call"""
        request = pickle.dumps({'function': function, 'args': args, 'kwargs': kwargs}, pickle.HIGHEST_PROTOCOL)
        self.channel.basic_publish(exchange='delayed-x',
                                   routing_key=self.name,
                                   properties=pika.BasicProperties(headers={"x-delay": delay_time},
                                                                   reply_to=self.callback_queue),
                                   body=request)

    def call(self, function, *args, **kwargs):
        """Call Service Routine"""
        request = pickle.dumps({'function': function, 'args': args, 'kwargs': kwargs}, pickle.HIGHEST_PROTOCOL)

        corr_id = str(uuid.uuid4())
        self.corr_ids.append(corr_id)
        self.channel.basic_publish(exchange='',
                                   routing_key=self.name,
                                   properties=pika.BasicProperties(reply_to=self.callback_queue,
                                                                   correlation_id=corr_id),
                                   body=request)
        while corr_id not in self.responses:
            self.connection.process_data_events()
            self.connection.sleep(0.01)

        response = self.responses.pop(corr_id)

        if 'exception' in response:
            ex = response['exception']  # type: BaseException
            if 'traceback' in response:
                if len(ex.args) > 0:
                    ex.args = (response['traceback'] + str(ex.args[0]),) + ex.args[1:]
                else:
                    ex.args = (response['traceback'],)
            raise response['exception']

        return response['result']

    def run(self):
        """Open connection to Service"""
        while True:
            self.connection.process_data_events()
            self.connection.sleep(10)
