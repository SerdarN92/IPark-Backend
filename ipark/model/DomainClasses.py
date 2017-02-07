from builtins import property
from datetime import datetime
from decimal import Decimal

from model.DatabaseObject import DomainClassBase, DatabaseObject
from model.ParkingLot import ParkingLot
from model.ParkingLot import ParkingSpot


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


DATEFORMAT = "%Y-%m-%d %H:%M:%S"


def any_to_datetime(o):
    if o is None:
        return None
    if isinstance(o, str):
        return datetime.strptime(o, DATEFORMAT)
    if isinstance(o, datetime):
        return o
    assert False


def any_to_string(o):
    if o is None:
        return None
    if isinstance(o, datetime):
        return o.strftime(DATEFORMAT)
    return str(o)


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

    @property
    def reservation_fee(self) -> Decimal:
        if self.reservation_start is None:
            return Decimal(0)
        begin = any_to_datetime(self.reservation_start)
        end = any_to_datetime(self.parking_start) or datetime.now()

        spot = ParkingSpot(self.spot_id)
        lot = ParkingLot(spot.lot_id)

        tax = (lot.reservation_tax * Decimal((end - begin).total_seconds())) / Decimal(3600)
        tax = min(tax, lot.max_tax * Decimal((end - begin).days + 1))

        return Decimal(tax)

    @property
    def parking_fee(self) -> Decimal:
        if self.parking_start is None:
            return Decimal(0)
        begin = any_to_datetime(self.parking_start)
        end = any_to_datetime(self.parking_end) or datetime.now()

        spot = ParkingSpot(self.spot_id)
        lot = ParkingLot(spot.lot_id)

        tax = (lot.tax * Decimal((end - begin).total_seconds())) / Decimal(3600)
        tax = min(tax, lot.max_tax * Decimal((end - begin).days + 1))

        return Decimal(tax)

    @reservation_fee.setter
    def reservation_fee(self, *args):
        pass

    @parking_fee.setter
    def parking_fee(self, *args):
        pass

    def __str__(self):
        return str(self.__dict__)

    def map_to_email(self, email: str) -> bool:
        return DatabaseObject.r.set('res_user:' + str(self.res_id), email)

    def remove_mapping(self) -> bool:
        return DatabaseObject.r.delete('res_user:' + str(self.res_id))

    @staticmethod
    def get_email_from_resid(res_id: int) -> str:
        return DatabaseObject.r.get('res_user:' + str(res_id)).decode()

    def get_data_dict(self):
        data = super(Reservation, self).get_data_dict()
        for e in ['reservation_start', 'parking_start', 'parking_end']:
            data[e] = any_to_datetime(getattr(self, e, None))
        for e in ['reservation_fee', 'parking_fee']:
            data[e] = getattr(self, e, None)
        data['id'] = data['res_id'] = self.res_id if self.res_id is not None else -1

        spot = ParkingSpot(self.spot_id)
        try:
            data['number'] = int(spot.number)
        except ValueError as ex:
            data['number'] = -1
        data['lot'] = ParkingLot(spot.lot_id).get_data_dict()

        return data


class Invoice(DomainClassBase):
    database_fields = []  # Todo

    def __init__(self):
        super(Invoice, self).__init__()

        self.user = None  # type: User  # leider zyklisch
        self.date = ""
        self.deadline = ""  # Frist für die Begleichung
        self.payment_method = None  # type: PaymentMethod
        self.status = 0  # bezahlt?
