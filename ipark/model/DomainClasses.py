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

    database_fields = ['res_id', 'user_id', 'spot_id', 'reservation_start', 'parking_start', 'parking_end']

    @staticmethod
    def get_next_id() -> int:
        return DatabaseObject.r.incr('reservationsLastId')

    def __init__(self):
        super(Reservation, self).__init__()

        self.res_id = None  # type: int
        self.user_id = None
        self.spot_id = None

        self.reservation_start = None
        self.parking_start = None
        self.parking_end = None

    def __str__(self):
        return str(self.__dict__)

    def map_to_email(self, email: str) -> bool:
        return DatabaseObject.r.set('res_user:' + str(self.res_id), email)

    def remove_mapping(self) -> bool:
        return DatabaseObject.r.delete('res_user:' + str(self.res_id))

    @staticmethod
    def get_email_from_resid(res_id: int) -> str:
        return DatabaseObject.r.get('res_user:' + str(res_id))


class Invoice(DomainClassBase):
    database_fields = []  # Todo

    def __init__(self):
        super(Invoice, self).__init__()

        self.user = None  # type: User  # leider zyklisch
        self.date = ""
        self.deadline = ""  # Frist für die Begleichung
        self.payment_method = None  # type: PaymentMethod
        self.status = 0  # bezahlt?
