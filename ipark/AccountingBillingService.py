from communication.Service import Service
from communication.Client import Client
import AuthService
from datetime import datetime
from model.DomainClasses import Reservation
from model.ParkingLot import ParkingLot, ParkingSpot
from model.User import User

DATEFORMAT = "%Y-%m-%d %H:%M:%S"


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
        if user.reservations[-1].parking_end is None or len(user.reservations[-1].parking_end) <= 0:
            return False

        lot = ParkingLot(lot_id)
        spot_id = lot.reserve_free_parkingspot()
        spot = ParkingSpot(spot_id)

        res = Reservation()
        res.res_id = Reservation.get_next_id()
        res.spot_id = spot_id
        res.user_id = user.user_id
        res.reservation_start = datetime.now().strftime(DATEFORMAT)
        user.reservations.append(res)
        user.save()
        user.flush()
        return True

    def fetch_reservation_data(self, token):
        response = self.authservice.get_email_from_token(token)
        if not response['status']:
            return False
        user = User(response['email'], readonly=True)
        reservations = []
        for r in user.reservations:
            p = ParkingSpot(r.spot_id)
            if r.parking_start is None:
                reservations.append({"id": r.res_id, "lot_id": p.lot_id, "spot_id": p.spot_id, "number": p.number,
                                     "time": r.reservation_start})
            else:
                dur = (datetime.strptime(r.parking_start, DATEFORMAT) -
                       datetime.strptime(r.reservation_start, DATEFORMAT)).total_seconds()
                reservations.append({"id": r.res_id, "lot_id": p.lot_id, "spot_id": p.spot_id, "number": p.number,
                                     "time": r.reservation_start, "duration": dur})

        return reservations

    def begin_parking(self, token, reservationid):
        response = self.authservice.get_email_from_token(token)
        if not response['status']:
            return False
        user = User(response['email'])
        reservation = self.get_user_reservation_for_id(user, reservationid)
        if reservation is None:
            return False
        lot = ParkingLot(reservation.spot_id)
        begin = datetime.strptime(reservation.reservation_start, DATEFORMAT)
        end = datetime.now()
        reservation.parking_start = end.strftime(DATEFORMAT)
        reservation.save()
        reservation.flush()
        # tax wird auf die Sekunde genau berechnet!
        duration = (end - begin).total_seconds()
        tax = (lot.reservation_tax * duration) / 3600
        days = (end - begin).days()
        if tax > lot.max_tax * (days + 1):  # todo müssen wir mehrtägiges Parken berücksichtigen?
            tax = lot.max_tax * (days + 1)
        user.balance -= tax
        user.save()
        user.flush()
        return tax

    def end_parking(self, token, reservationid):
        response = self.authservice.get_email_from_token(token)
        if not response['status']:
            return False
        user = User(response['email'])
        reservation = self.get_user_reservation_for_id(user, reservationid)
        if reservation is None:
            return False
        lot = ParkingLot(reservation.spot_id)
        begin = datetime.strptime(reservation.parking_start, DATEFORMAT)
        end = datetime.now()
        reservation.parking_end = end.strftime(DATEFORMAT)
        reservation.save()
        reservation.flush()
        duration = (end - begin).total_seconds()
        days = (end - begin).days()
        tax = (lot.tax * duration) / 3600
        if tax > lot.max_tax * (days + 1):  # todo müssen wir mehrtägiges Parken berücksichtigen?
            tax = lot.max_tax * (days + 1)
        lot.removeReservation(reservation.spot_id)
        user.balance -= tax
        user.save()
        user.flush()
        return tax

    def cancel_reservation(self, token, reservationid):
        response = self.authservice.get_email_from_token(token)
        if not response['status']:
            return False
        user = User(response['email'])
        reservation = self.get_user_reservation_for_id(user, reservationid)
        if reservation is None:
            return False
        lot = ParkingLot(reservation.spot_id)
        begin = datetime.strptime(reservation.reservation_start, DATEFORMAT)
        end = datetime.now()
        reservation.parking_start = end.strftime(DATEFORMAT)
        reservation.parking_end = end.strftime(DATEFORMAT)
        reservation.save()
        reservation.flush()
        duration = (end - begin).total_seconds()
        days = (end - begin).days()
        tax = (lot.reservation_tax * duration) / 3600
        if tax > lot.max_tax * (days + 1):  # todo müssen wir mehrtägiges Parken berücksichtigen?
            tax = lot.max_tax * (days + 1)
        lot.removeReservation(reservation.spot_id)
        user.balance -= tax
        user.save()
        user.flush()
        return tax

    @staticmethod
    def get_user_reservation_for_id(user, reservationid):
        reservations = [x for x in user.reservations if x.res_id == reservationid]
        if not reservations:
            return None
        reservation = reservations.pop()
        return reservation


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

    def fetch_reservation_data(self, token):
        return self.call("fetch_reservation_data", token)

    def cancel_reservation(self, token, resid):
        return self.call("cancel_reservation", token, resid)

    def begin_parking(self, token, resid):
        return self.call("begin_parking", token, resid)

    def end_parking(self, token, resid):
        return self.call("end_parking", token, resid)


if __name__ == "__main__":
    service = AccountingAndBillingService()
