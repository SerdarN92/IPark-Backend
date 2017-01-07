import pickle
import threading

import pika


class Service(threading.Thread):
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
        print("Connected")
        connection.channel(self.on_channel_open)

    def on_channel_open(self, channel):
        print("Channel")
        self.channel = channel
        self.channel.queue_declare(self.on_queue_declared, queue=self.name)
        self.channel.basic_consume(self.on_request, queue=self.name)

    def on_queue_declared(self, frame):
        pass

    def run(self):
        print(u"[{0:s}] Service running...".format(self.name))
        self.connection.ioloop.start()

    def on_request(self, ch, method, props, body):
        request = pickle.loads(body)

        try:
            function = getattr(self, request['function'])
            result = {'result': function(*request['args'], **request['kwargs'])}
        except Exception as ex:
            result = {'exception': ex}

        response = pickle.dumps(result)

        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(correlation_id=props.correlation_id),
                         body=response)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def stop(self):
        self.connection.close()
        self.join()
        self.run()