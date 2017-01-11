from communication.Service import Service
from communication.Client import Client
import AuthService
from model.DatabaseObject import DatabaseObject
from model.DomainClasses import Reservation
from model.ParkingLot import ParkingLot, ParkingSpot
from model.User import User


class AccountingAndBillingService(Service):
    def __init__(self):
        self.authservice = AuthService.AuthClient()
        super().__init__("Accounting")

    def sign_up(self, info):
        if 'email' not in info or 'password' not in info or len(info['email']) * len(info['password']) == 0:
            return {"status": False, "message": "Invalid Arguments"}

        newbody = User.create(**info)
        if newbody is None:
            return {"status": False, "message": "Mail address is already in use."}

        result = self.authservice.login(info['email'], info['password'])
        return {"status": True, "token": result["token"]}

    def fetch_user_data(self, token):
        user = self.authservice.get_email_from_token(token)
        if "status" not in user or not user["status"]:
            return {"status": False, "message": "Invalid Token."}
        ruser = User(user["email"], readonly=True)
        return {"status": True, "user": ruser.get_data_dict()}

    def update_user_data(self, token, updata):
        user = self.authservice.get_email_from_token(token)
        if "status" not in user or not user["status"]:
            return {"status": False, "message": "Invalid Token."}
        if "password" in updata or "balance" in updata or "dataflags" in updata or "user_id" in updata:
            return {"status": False, "message": "Invalid Arguments."}
        wuser = User(user["email"])

        for field in ['first_name', 'last_name', 'street', 'number', 'plz', 'city', 'country']:
            if field in updata:
                setattr(wuser, field, updata[field])

        wuser.save()
        wuser.flush()
        return {"status": True}

    def reserve_parking_spot(self, token: str, lot_id: int) -> bool:
        response = self.authservice.get_email_from_token(token)
        if not response['status']:
            return False
        user = User(response['email'], readonly=True)

        lot = ParkingLot(lot_id)
        spot_id = lot.reserve_free_parkingspot()
        spot = ParkingSpot(spot_id)

        res = Reservation()
        res.spot_id = spot_id
        res.user_id = user.user_id
        user.reservations.append(res)
        user.flush()


class AccountingAndBillingClient(Client):
    def __init__(self):
        super().__init__("Accounting")

    def sign_up(self, info):
        return self.call("sign_up", info)

    def fetch_user_data(self, token):
        return self.call("fetch_user_data", token)

    def update_user_data(self, token, updata):
        return self.call("update_user_data", token, updata)

    def reserve_parking_spot(self, token: str, lot_id: int) -> bool:
        return self.call("reserve_parking_spot", token, lot_id)


if __name__ == "__main__":
    service = AccountingAndBillingService()
