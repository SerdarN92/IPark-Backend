class User(object):
    """Objects of this class hold the master data of the customers."""

    def __init__(self, email, password):
        self.first_name = ""  # string
        self.last_name = ""  # string
        self.email = email
        self.password = password
        self.address = ""  # string oder extra Datentyp?
        self.payment_methods = []  # type: list[PaymentMethod]
        self.reservations = []  # type: list[Reservation]
        self.invoices = []  # type: list[Invoice]
        self.authorization_secret = ""
        self.flags = 0 # z.B. ist ist 0x01 == delete
        self.balance = 0  # interner Kontostand?


class PaymentMethod(object):
    """This class is used to represent different payment methods."""
    def __init__(self):
        self.payment_provider = None
        self.valid_from = ""
        self.valid_until = ""
        # weiteres? ggf. abhängig von der Zahlungsmethode


class ParkingLot(object):
    """This class represents a geographical location in which the system manages a set of parking spots."""
    def __init__(self):
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
        self.number = 0  # Nummer des Parkplatzes
        self.status = None  # Statusobjekt
        self.parking_lot = None  # type: ParkingLot # zyklisch mit ParkingLot.parkingSpots. leider sehe ich grad keine
                                #  andere Variante (s.u.)
        self.location = 0  # Ebene oä?
        self.tariffID = 0


class Reservation(object):
    """This class represents a reservation."""
    def __init__(self):
        self.id = ""  # UUID
        self.valid_from = ""
        self.valid_until = ""
        self.duration = 1234
        self.parking_spot = None  # type: ParkingSpot # eindeutiger Parkplatz
        self.tariff = None  # type: Tariff


class Invoice(object):
    def __init__(self):
        self.user = None  # type: User  # leider zyklisch
        self.date = ""
        self.deadline = ""  # Frist für die Begleichung
        self.payment_method = None  # type: PaymentMethod
        self.status = 0  # bezahlt?


class Tariff(object):
    def __init__(self):
        self.price_per_minute = 0.01
        self.minDuration = 30
        self.maxDuration = 120
