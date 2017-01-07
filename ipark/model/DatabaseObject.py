import pickle

import MySQLdb as mydb
import MySQLdb.cursors
import redis


class DatabaseObject:
    r = redis.StrictRedis(host='132.252.152.57')
    r.execute_command("AUTH GS~FsB3~&c7T")

    # r.flushall()

    my = mydb.connect('132.252.152.57', 'root', 'GS~FsB3~&c7T', 'ipark',
                      cursorclass=mydb.cursors.DictCursor)

    def __init__(self):
        pass

    @staticmethod
    def get_data(key: str, query: str, queryargs: tuple, factory: callable) -> any:
        data = DatabaseObject.r.get(key)
        if data is None:
            cur = DatabaseObject.my.cursor()  # type: MySQLdb.cursors.DictCursor
            cur.execute(query, queryargs)
            data = cur.fetchall()
            data = factory(data)

            DatabaseObject.r.set(key, pickle.dumps(data))
        else:
            data = pickle.loads(data)

        return data

    @staticmethod
    def assign_dict(object: object, data: dict) -> object:
        for k, v in data.items():
            if hasattr(object, k):
                setattr(object, k, v)
        return object
