from model.DomainClasses import PaymentMethod
from model.User import User
from model.ParkingLot import ParkingLot

from model.DatabaseObject import DatabaseObject

# DatabaseObject.r.flushall()

# ParkingLot.import_parkinglots()  # only fast on localhost

try:
    user = User("test@test.de", "123")

    print(user)
    print(user.payment_methods[0])
    print(user.reservations[0])

    user.first_name = 'Neuer Name'
    p = PaymentMethod()
    p.payment_provider = "AddingTest"
    user.payment_methods.append(p)

    user.save()  # indicate saving of User, saves properties

    print(user._payment_methods)  # internal cache is cleared on save
    print(user.payment_methods[1])

    user.flush()  # actual save, now readonly

except User.NotFoundException as ex:
    print("User not found (or invalid password)")


