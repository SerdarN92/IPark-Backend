from model.DatabaseObject import DomainClassBase


class PaymentMethod(DomainClassBase):
    """This class is used to represent different payment methods."""

    database_fields = ['payment_provider', 'valid_from', 'valid_until']

    def __init__(self):
        super(PaymentMethod, self).__init__()

        self.payment_provider = None
        self.valid_from = ""
        self.valid_until = ""
        # weiteres? ggf. abhängig von der Zahlungsmethode

    def __str__(self):
        return '{' + str(self.payment_provider) + ': "' + str(self.valid_from) + '" - "' + str(self.valid_until) + '"}'


class Reservation(DomainClassBase):
    """This class represents a reservation."""

    database_fields = ['res_id', 'user_id', 'lot_id', 'tariff_id', 'valid_from', 'valid_until', 'duration']

    def __init__(self):
        super(Reservation, self).__init__()

        self.res_id = None  # UUID
        self.user_id = None
        self.lot_id = None
        # self.parking_spot = None  # type: ParkingSpot # eindeutiger Parkplatz
        self.tariff_id = None  # type: Tariff

        self.valid_from = None
        self.valid_until = None
        self.duration = None

    def __str__(self):
        return str(self.__dict__)


class ParkingLot(object):
    """This class represents a geographical location in which the system manages a set of parking spots."""

    def __init__(self):
        super(ParkingLot, self).__init__()

        self.id = 0  # ID des Parkplatzes / Parkhauses (vllt UUID?)
        self.address = ""  # siehe oben zu den Adressen
        self.capacity = 1
        self.reservation_capacity = 1
        self.reservations = []  # type: list[Reservation]
        self.parking_spots = []  # type: list[ParkingSpot]
        self.tariffs = []  # type: list[Tariff]
        self.location = (1234.1231, 1234.123124)  # lat, lon


class ParkingSpot(object):
    """This class represents a single spot to park a car on. This always belongs to exactly one ParkingLot."""

    def __init__(self):
        super(ParkingSpot, self).__init__()

        self.number = 0  # Nummer des Parkplatzes
        self.status = None  # Statusobjekt
        self.parking_lot = None  # type: ParkingLot # zyklisch mit ParkingLot.parkingSpots. leider sehe ich grad keine
        #  andere Variante (s.u.)
        self.location = 0  # Ebene oä?
        self.tariffID = 0


class Invoice(DomainClassBase):

    database_fields = [] # Todo

    def __init__(self):
        super(Invoice, self).__init__()

        self.user = None  # type: User  # leider zyklisch
        self.date = ""
        self.deadline = ""  # Frist für die Begleichung
        self.payment_method = None  # type: PaymentMethod
        self.status = 0  # bezahlt?


class Tariff(object):
    def __init__(self):
        super(Tariff, self).__init__()

        self.price_per_minute = 0.01
        self.minDuration = 30
        self.maxDuration = 120
