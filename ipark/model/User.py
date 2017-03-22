from decimal import Decimal

import MySQLdb
import bcrypt

from model.DatabaseObject import DatabaseObject, DomainClassBase
from model.DomainClasses import PaymentMethod, Reservation, Invoice

"""Representation Object of the User (Data)"""

def check_hash(pwhash: str, password: str) -> bool:
    """Validate hased password"""
    try:
        return bcrypt.checkpw(password.encode(), pwhash.encode())
    except ValueError as ex:
        return False


def hash_password(password: str) -> str:
    """Generate password hash"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


class NotFoundException(BaseException):
    """Exception if the User is not found or the password is invalid"""
    pass


class User(DomainClassBase):
    """Objects of this class hold the master data of the customers."""

    database_fields = ['user_id', 'first_name', 'last_name', 'email', 'password',
                       'street', 'number', 'plz', 'city', 'country', 'dataflags', 'balance', 'client_settings']

    def __init__(self, email: str, password: str = None, readonly: bool = False):
        """ Load User Data
        :param password: None disables check
        """
        super(User, self).__init__()
        self.user_id = None
        self.email = None
        self.password = None

        self.first_name = None  # type: str
        self.last_name = None  # type: str
        self.street = None  # type: str
        self.number = None  # type: str
        self.plz = None  # type: str
        self.city = None  # type: str
        self.country = None  # type: str
        self.client_settings = None  # type: str

        self.dataflags = None  # z.B. ist ist 0x01 == delete
        self.balance = Decimal(0)  # interner Kontostand?

        self._payment_methods = None  # type: list[PaymentMethod]
        self._reservations = None  # type: list[Reservation]
        self._invoices = None  # type: list[Invoice]

        self._key = 'user:' + email
        self._modified = DatabaseObject.READONLY if readonly else DatabaseObject.NONE  # type: int

        # Load
        load_func = DatabaseObject.load_data if readonly else DatabaseObject.load_and_lock_data
        data = load_func(self._key, "SELECT * FROM users WHERE email = %s",
                         (email,),
                         lambda x: len(x) and x[0])

        # Check
        if not data or (password is not None and not check_hash(data['password'], password)):
            raise NotFoundException()

        # Assign
        for e in data:
            setattr(self, e, data[e])

    def save(self):
        """Mark User Object for saving, write external properties"""
        super(User, self).save()
        self.save_properties()

    def save_properties(self):
        """save external properties"""
        for p in ['reservations', 'payment_methods', 'invoices']:
            self._save_list_property(p)

    def flush(self):
        """write properties and data marked for saving, Object becomes readonly"""
        self.save_properties()
        super(User, self).flush()

    def _save_list_property(self, name):
        private_name = '_' + name
        if getattr(self, private_name) is not None:
            assert self.user_id is not None
            key = 'user:' + name + ':' + str(self.user_id)
            DatabaseObject._flush_and_unlock(key, getattr(self, private_name))
            setattr(self, private_name, None)

    @staticmethod
    def create(email, password, **additional_data):
        """Create new user in Database (sign up)"""
        with DatabaseObject.my.cursor() as cur:
            try:
                data = [email, hash_password(password)]
                data.extend([additional_data.get(field, '') for field
                             in ['first_name', 'last_name', 'street', 'number', 'plz', 'city', 'country',
                                 'client_settings']])
                if cur.execute("INSERT INTO users (email, password, first_name, last_name, "
                               "street, `number`, plz, city, country, client_settings) "
                               "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                               tuple(data)) != 1:
                    return None  # unknown error :)
            except MySQLdb.IntegrityError:
                return None  # the mail is already in use
            DatabaseObject.my.commit()
        return User(email, password, readonly=True)

    @property
    def payment_methods(self):
        """
            Load and get Payment Methods of User
        :rtype: list[PaymentMethod]
        """
        if self._payment_methods is None:
            self._payment_methods = DatabaseObject \
                .load_and_lock_data('user:payment_methods:' + str(self.user_id),
                                    "SELECT * FROM payment_methods WHERE user_id = %s", (self.user_id,),
                                    lambda d: [DatabaseObject.assign_dict(PaymentMethod(), x) for x in d])
        return self._payment_methods

    @property
    def reservations(self):
        """
            Load and get Reservations of User
        :rtype: list[Reservation]
        """
        if self._reservations is None:
            self._reservations = DatabaseObject \
                .load_and_lock_data('user:reservations:' + str(self.user_id),
                                    "SELECT * FROM reservations WHERE user_id = %s", (self.user_id,),
                                    lambda d: [DatabaseObject.assign_dict(Reservation(), x) for x in d])
        return self._reservations

    @property
    def invoices(self):
        """
            Load and get Invoices of User
        :rtype: list[Invoice]
        """
        pass  # Todo

    def __str__(self):
        return str({k: v for k, v in self.__dict__.items() if k[0] != '_'})
