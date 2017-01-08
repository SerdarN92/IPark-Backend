from GeoService import GeoService
from model.DomainClasses import PaymentMethod
from model.User import User
from model.ParkingLot import ParkingLot, ParkingSpot

from model.DatabaseObject import DatabaseObject

# DatabaseObject.r.flushall()

# ParkingLot.import_parkinglots()  # only fast on localhost

try:
    user = User("test@test.de", "123")

    print(user)
    print(user.payment_methods[0])
    # print(user.reservations[0])

    user.first_name = 'Neuer Name'
    p = PaymentMethod()
    p.payment_provider = "AddingTest"
    user.payment_methods.append(p)

    user.save()  # indicate saving of User, saves properties

    print(user._payment_methods)  # internal cache is cleared on save
    print(user.payment_methods[1])
    print('Number of payment_methods', len(user.payment_methods))

    user.flush()  # actual save, now readonly

except User.NotFoundException as ex:
    print("User not found (or invalid password)")

lots = GeoService.find_near_parking_lots(None, 51.4, 7.03, 6, 3)
print('Found Lots:', len(lots), [x.__dict__ for x in lots])

lot = lots[2]  # type: ParkingLot
print(lot.__dict__)
print('Free Spots:', lot.getFreeParkingSpots())

spot_id = lot.reserve_free_parkingspot()
spot = ParkingSpot(spot_id)
print('Reserved Spot:', spot.spot_id)
print('Free Spots:', lot.getFreeParkingSpots())

lot = ParkingLot(spot.lot_id)
lot.removeReservation(spot.spot_id)
print('Returned Spot\nFree Spots:', lot.getFreeParkingSpots())
