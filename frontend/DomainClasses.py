class User(object):
    def __init__(self):
        self.firstName = ""  # string
        self.lastName = ""  # string
        self.address = ""  # string oder extra Datentyp?
        self.paymentMethods = []  # type: list[PaymentMethod]
        self.reservations = []  # type: list[Reservation]
        self.invoices = []  # type: list[Invoice]
        self.authorization_secret = ""
        self.balance = 0  # interner Kontostand?


class PaymentMethod(object):
    def __init__(self):
        self.paymentProvider = None
        self.validFrom = ""
        self.validUntil = ""
        # weiteres? ggf. abhängig von der Zahlungsmethode


class ParkingLot(object):
    def __init__(self):
        self.id = 0  # ID des Parkplatzes / Parkhauses (vllt UUID?)
        self.address = ""  # siehe oben zu den Adressen
        self.capacity = 1
        self.reservationCapacity = 1
        self.reservations = []  # type: list[Reservation]
        self.parkingSpots = []  # type: list[ParkingSpot]
        self.tariffs = []  # type: list[Tariff]
        self.location = (1234.1231, 1234.123124)  # lat, lon


class ParkingSpot(object):
    def __init__(self):
        self.number = 0  # Nummer des Parkplatzes
        self.status = None  # Statusobjekt
        self.parkingLot = None  # type: ParkingLot # zyklisch mit ParkingLot.parkingSpots. leider sehe ich grad keine andere Variante (s.u.)
        self.location = 0  # Ebene oä?
        self.tariffID = 0


class Reservation(object):
    def __init__(self):
        self.id = ""  # UUID
        self.validFrom = ""
        self.validUntil = ""
        self.duration = 1234
        self.parkingSpot = None  # type: ParkingSpot # eindeutiger Parkplatz
        self.tariff = None  # type: Tariff


class Invoice(object):
    def __init__(self):
        self.user = None  # type: User  # leider zyklisch
        self.date = ""
        self.deadline = ""  # Frist für die Begleichung
        self.paymentMethod = None  # type: PaymentMethod
        self.status = 0  # bezahlt?


class Tariff(object):
    def __init__(self):
        self.pricePerMinute = 0.01
        self.minDuration = 30
        self.maxDuration = 120
