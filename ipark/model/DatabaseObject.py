import pickle

import MySQLdb as mydb
import MySQLdb.cursors
import redis

"""Base Class for Database Objects"""

class ReadonlyException(BaseException):
    """Exception if Object cannot be written back to Database"""
    pass


class LockedException(BaseException):
    """Exception if Object cannot be opened r/w"""
    pass


class DomainClassBase:
    """Base Class for Database Objects"""
    database_fields = None

    def __init__(self):
        self._modified = None
        self._key = None

    def save(self):
        """Mark Object for saving"""
        assert self._modified is not None
        if self._modified == DatabaseObject.READONLY:
            raise ReadonlyException()

        if self._modified == DatabaseObject.NONE:
            self._modified = DatabaseObject.MODIFIED
            return True

        return False

    def flush(self):
        """Save, unlock and make Object readonly"""
        if self._modified not in (DatabaseObject.MODIFIED, DatabaseObject.NEW):
            return

        assert self._key is not None
        DatabaseObject._flush_and_unlock(self._key, self.get_data_dict())

        self._modified = DatabaseObject.READONLY

    def __del__(self):
        """Write on delete if changed"""
        self.flush()

    def get_data_dict(self):
        """get raw representation of object"""
        assert self.__class__.database_fields is not None
        return {k: getattr(self, k) for k in self.__class__.database_fields}


class DatabaseObject:
    """static helper methods and connection management for database objects (redis and MySQL)"""
    r = redis.StrictRedis(host='132.252.152.57', password="GS~FsB3~&c7T")
    READONLY = -1
    NONE = 0
    NEW = 1

    # r.flushall()

    MODIFIED = 2

    my = mydb.connect('132.252.152.57', 'root', 'GS~FsB3~&c7T', 'ipark',
                      cursorclass=mydb.cursors.DictCursor)

    database_fields = None

    def __init__(self):
        pass

    @staticmethod
    def load_and_lock_data(key: str, query: str, queryargs: tuple, factory: callable) -> any:
        """Load Object from DB in r/w"""
        assert query.lower()[:6] == 'select'

        lock = DatabaseObject.r.getset(key + ':locked', 1)
        if lock == 1:
            raise LockedException()

        data = DatabaseObject.load_data(key, query, queryargs, factory)

        return data

    @staticmethod
    def _flush_and_unlock(key: str, data: any) -> None:
        """Release working copy of object"""
        assert DatabaseObject.r.get(key + ':locked') == b'1'
        DatabaseObject.r.set(key, pickle.dumps(data))
        DatabaseObject.r.delete(key + ':locked')

    @staticmethod
    def load_data(key: str, query: str, queryargs: tuple, factory: callable) -> any:
        """Load Data from DB, it is readonly if not locked from outer call"""
        assert query.lower()[:6] == 'select'
        data = DatabaseObject.r.get(key)
        if data is None:
            with DatabaseObject.my.cursor() as cur:  # type: MySQLdb.cursors.DictCursor
                cur.execute(query, queryargs)
                data = cur.fetchall()
                data = factory(data)
                DatabaseObject.my.commit()

                if cur.rowcount > 0:
                    DatabaseObject.r.set(key, pickle.dumps(data))
        else:
            data = pickle.loads(data)

        return data

    @staticmethod
    def assign_dict(object: object, data: dict) -> object:
        """initialize object from raw representation"""
        for k, v in data.items():
            if hasattr(object, k):
                setattr(object, k, v)
        return object
