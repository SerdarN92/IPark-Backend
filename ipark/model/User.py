from model.DatabaseObject import DatabaseObject
from model.DomainClasses import PaymentMethod, Reservation, Invoice
import MySQLdb

class User(DatabaseObject):
    """Objects of this class hold the master data of the customers."""

    class NotFoundException(BaseException):
        pass

    def __init__(self, email: str, password: str = None):
        """ Load User Data
        :param password: None disables check
        """
        super(User, self).__init__()
        self.user_id = None
        self.first_name = None  # type: str
        self.last_name = None  # type: str

        self.email = None
        self.password = None
        self.address = None  # string oder extra Datentyp?
        self.dataflags = None  # z.B. ist ist 0x01 == delete
        self.balance = None  # interner Kontostand?

        self._payment_methods = None  # type: list[PaymentMethod]
        self._reservations = None  # type: list[Reservation]
        self._invoices = None  # type: list[Invoice]

        # Load
        data = DatabaseObject.get_data('user:' + email, "SELECT * from users WHERE email = %s",
                                       (email,),
                                       lambda x: len(x) and x[0])

        # Check
        if not data or (password is not None and data['password'] != password):
            raise User.NotFoundException()

        # Assign
        for e in data:
            setattr(self, e, data[e])

    @staticmethod
    def create(email, password):
        cur = DatabaseObject.my.cursor()
        try:
            if cur.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, password)) != 1:
                return None  # unknown error :)
        except MySQLdb.IntegrityError:
            return None  # the mail is already in use
        return User(email, password)

    @property
    def payment_methods(self):
        """

        :rtype: list[PaymentMethod]
        """
        if self._payment_methods is None:
            self._payment_methods = \
                DatabaseObject.get_data('user:payment_methods:' + str(self.user_id),
                                        "SELECT * FROM payment_methods WHERE user_id = %s", (self.user_id,),
                                        lambda d: [DatabaseObject.assign_dict(PaymentMethod(), x) for x in d])
        return self._payment_methods

    @property
    def reservations(self):
        """

        :rtype: list[Reservation]
        """
        if self._reservations is None:
            self._reservations = \
                DatabaseObject.get_data('user:reservations:' + str(self.user_id),
                                        "SELECT * FROM reservations WHERE user_id = %s", (self.user_id,),
                                        lambda d: [DatabaseObject.assign_dict(Reservation(), x) for x in d])
        return self._reservations

    @property
    def invoices(self):
        """

        :rtype: list[Invoice]
        """
        pass  # Todo

    def __str__(self):
        return str({k: v for k, v in self.__dict__.items() if k[0] != '_'})
