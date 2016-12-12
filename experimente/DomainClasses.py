class User(object):
    def __init__(self):
        self.firstName = ""  # string
        self.lastName = ""  # string
        self.address = ""  # string oder extra Datentyp?
        self.paymentMethods = []  # liste mit PaymentMethods
        self.reservations = []  # liste mit Reservations
        self.invoices = []  # liste mit Invoices


class PaymentMethod(object):
    def __init__(self):
        self.validFrom = ""
        self.validUntil = ""
        # weiteres? ggf. abhängig von der Zahlungsmethode


class ParkingLot(object):
    def __init__(self):
        self.id = ""  # ID des Parkplatzes / Parkhauses (vllt UUID?)
        self.address = "" # siehe oben zu den Adressen
        self.capacity = 1
        self.reservationCapacity = 1
        self.reservations = []
        self.parkingSpots = []
        self.tariffs = [] # ggf. mehrere Tarife pro Parkhaus?
        self.long = 1234.1231
        self.lat = 1234.123124


class ParkingSpot(object):
    def __init__(self):
        self.number = "" #Nummer des Parkplatzes
        self.status = "" #Statusobjekt
        self.parkingLot = "" #zyklisch mit ParkingLot.parkingSpots. leider sehe ich grad keine andere Variante (s.u.)


class Reservation(object):
    def __init__(self):
        self.id = "" # UUID
        self.validFrom = ""
        self.validUntil = ""
        self.duration = 1234
        self.parkingSpot = "" # eindeutiger Parkplatz
        self.tariff = ""


class Invoice(object):
    def __init__(self):
        self.User = ""  # leider zyklisch
        self.date = ""
        self.deadline = "" # Frist für die Begleichung
        self.paymentMethod = ""
        # fehlt da noch was?


class Tariff(object):
    pass # TODO dringend modellieren. Keine Ahnung!