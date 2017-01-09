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

    def sign_up(self, email, password, first_name=None, last_name=None, address=None):
        newbody = User.create(email, password)
        if newbody is None:
            return {"status": False, "message": "Mail address is already in use."}
        if first_name is not None:
            pass
        if last_name is not None:
            pass
        if address is not None:
            pass
        result = self.authservice.login(email, password)
        return {"status": True, "token": result["token"]}

    def fetch_user_data(self, token):
        user = self.authservice.get_email_from_token(token)
        if "status" not in user or not user["status"]:
            print("Accounting")
            return {"status": False, "message": "Invalid Token."}
        ruser = User(user["email"], readonly=True)
        return {"status": True, "user": ruser.get_data_dict()}

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

    def sign_up(self, email, password):
        return self.call("sign_up", email, password)

    def fetch_user_data(self, token):
        return self.call("fetch_user_data", token)

    def reserve_parking_spot(self, token: str, lot_id: int) -> bool:
        return self.call("reserve_parking_spot", token, lot_id)


if __name__ == "__main__":
    service = AccountingAndBillingService()
