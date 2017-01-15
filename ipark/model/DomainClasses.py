from model.DatabaseObject import DomainClassBase, DatabaseObject


class PaymentMethod(DomainClassBase):
    """This class is used to represent different payment methods."""

    database_fields = ['pm_id', 'user_id', 'payment_provider', 'valid_from', 'valid_until']

    def __init__(self):
        super(PaymentMethod, self).__init__()

        self.pm_id = None
        self.user_id = None
        self.payment_provider = None
        self.valid_from = None
        self.valid_until = None
        # weiteres? ggf. abhängig von der Zahlungsmethode

    def __str__(self):
        return '{' + str(self.payment_provider) + ': "' + str(self.valid_from) + '" - "' + str(self.valid_until) + '"}'


class Reservation(DomainClassBase):
    """This class represents a reservation."""

    database_fields = ['res_id', 'user_id', 'spot_id', 'valid_from', 'valid_until', 'duration']

    @staticmethod
    def get_next_id() -> int:
        return DatabaseObject.r.incr('reservationsLastId')

    def __init__(self):
        super(Reservation, self).__init__()

        self.res_id = None  # type: int
        self.user_id = None
        self.spot_id = None

        self.valid_from = None
        self.valid_until = None
        self.duration = None

    def __str__(self):
        return str(self.__dict__)


class Invoice(DomainClassBase):
    database_fields = []  # Todo

    def __init__(self):
        super(Invoice, self).__init__()

        self.user = None  # type: User  # leider zyklisch
        self.date = ""
        self.deadline = ""  # Frist für die Begleichung
        self.payment_method = None  # type: PaymentMethod
        self.status = 0  # bezahlt?
