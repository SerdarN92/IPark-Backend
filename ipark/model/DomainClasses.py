from builtins import property
from datetime import datetime
from decimal import Decimal

from ipark.model.DatabaseObject import DomainClassBase, DatabaseObject
from ipark.model.ParkingLot import ParkingLot
from ipark.model.ParkingLot import ParkingSpot


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
    """Convert various date representations to datetime object"""
    if o is None:
        return None
    if isinstance(o, str):
        return datetime.strptime(o, DATEFORMAT)
    if isinstance(o, datetime):
        return o
    assert False


def any_to_string(o):
    """Convert various date representations to string"""
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
        """Get and increment next database id for a new Reservation"""
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
        """Get current reservation fee"""
        if self.reservation_start is None:
            return Decimal(0)
        begin = any_to_datetime(self.reservation_start)
        end = any_to_datetime(self.parking_start) or datetime.now()

        spot = ParkingSpot(self.spot_id)
        lot = ParkingLot(spot.lot_id)

        tax = (lot.reservation_tax * Decimal((end - begin).total_seconds())) / Decimal(3600)
        tax = min(tax, lot.max_tax * Decimal((end - begin).days + 1))

        return round(Decimal(tax), 2)

    @property
    def parking_fee(self) -> Decimal:
        """Get current parking fee"""
        if self.parking_start is None:
            return Decimal(0)
        begin = any_to_datetime(self.parking_start)
        end = any_to_datetime(self.parking_end) or datetime.now()

        spot = ParkingSpot(self.spot_id)
        lot = ParkingLot(spot.lot_id)

        tax = (lot.tax * Decimal((end - begin).total_seconds())) / Decimal(3600)
        tax = min(tax, lot.max_tax * Decimal((end - begin).days + 1))

        return round(Decimal(tax), 2)

    @reservation_fee.setter
    def reservation_fee(self, *args):
        """Reservation fees cannot be set -> ignore"""
        pass

    @parking_fee.setter
    def parking_fee(self, *args):
        """Parking fees cannot be set -> ignore"""
        pass

    def __str__(self):
        return str(self.__dict__)

    def map_to_email(self, email: str) -> bool:
        """Create mapping to retrieve user email"""
        return DatabaseObject.r.set('res_user:' + str(self.res_id), email)

    def remove_mapping(self) -> bool:
        """Remove extra mapping between reservation and user email"""
        return DatabaseObject.r.delete('res_user:' + str(self.res_id))

    @staticmethod
    def get_email_from_resid(res_id: int) -> str:
        """Get mapped user email address to get user from reservation id"""
        return DatabaseObject.r.get('res_user:' + str(res_id)).decode()

    def get_data_dict(self):
        """get raw representation of object"""
        data = super(Reservation, self).get_data_dict()
        for e in ['reservation_start', 'parking_start', 'parking_end']:
            data[e] = any_to_datetime(getattr(self, e, None))
        for e in ['reservation_fee', 'parking_fee']:
            data[e] = getattr(self, e, None)
        data['id'] = data['res_id'] = self.res_id if self.res_id is not None else -1

        spot = ParkingSpot(self.spot_id)
        data['lot_id'] = spot.lot_id
        try:
            data['number'] = int(spot.number)
        except ValueError as ex:
            data['number'] = -1
        data['lot'] = ParkingLot(spot.lot_id).get_data_dict()

        return data


class Invoice(DomainClassBase):
    """Object Representation of an Invoice"""
    database_fields = []  # Todo

    def __init__(self):
        super(Invoice, self).__init__()

        self.user = None  # type: User  # leider zyklisch
        self.date = ""
        self.deadline = ""  # Frist für die Begleichung
        self.payment_method = None  # type: PaymentMethod
        self.status = 0  # bezahlt?
