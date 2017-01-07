from model.User import User

from model.DatabaseObject import DatabaseObject

DatabaseObject.r.flushall()

try:
    user = User("test@test.de", "123")

    print(user)
    print(user.payment_methods[0])
    print(user.reservations[0])

except User.NotFoundException as ex:
    print("User not found (or invalid password)")
