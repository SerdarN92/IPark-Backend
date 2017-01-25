from decimal import Decimal

from communication.Service import Service
from communication.Client import Client
import AuthService
from datetime import datetime
from model.DomainClasses import Reservation
from model.ParkingLot import ParkingLot, ParkingSpot
from model.User import User
from flask import json

DATEFORMAT = "%Y-%m-%d %H:%M:%S"


def merge(j, j2) -> bool:
    if type(j) is not type(j2):
        return False

    if isinstance(j, list):
        j.extend(j2)
        return True
    elif isinstance(j, dict):
        for k2 in j2:
            if k2 not in j:
                j[k2] = j2[k2]
            else:
                if not merge(j[k2], j2[k2]):
                    return False
        return True
    return False


def any_to_datetime(o):
    if isinstance(o, str):
        return datetime.strptime(o, DATEFORMAT)
    if isinstance(o, datetime):
        return o
    assert False


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

    def update_user_data(self, token: str, updata: dict, join: bool) -> dict:
        user = self.authservice.get_email_from_token(token)
        if "status" not in user or not user["status"]:
            return {"status": False, "message": "Invalid Token."}
        if any(k in updata for k in ["password", "balance", "dataflags", "user_id"]):
            return {"status": False, "message": "Invalid Arguments."}
        wuser = User(user["email"])

        for field in ['first_name', 'last_name', 'street', 'number', 'plz', 'city', 'country', 'client_settings']:
            if field in updata:
                if join and field == 'client_settings':
                    j = json.loads(wuser.client_settings)  # type: json
                    j2 = json.loads(updata[field])
                    merge(j, j2)
                    wuser.client_settings = json.dumps(j)
                else:
                    setattr(wuser, field, updata[field])

        wuser.save()
        wuser.flush()
        return {"status": True}

    def reserve_parking_spot(self, token: str, lot_id: int, spottype: int) -> bool:
        response = self.authservice.get_email_from_token(token)
        if not response['status']:
            return False
        user = User(response['email'], readonly=True)
        if any(r.parking_end is None for r in user.reservations):
            return False

        lot = ParkingLot(lot_id)
        spot_id = lot.reserve_free_parkingspot(spottype)
        spot = ParkingSpot(spot_id)

        res = Reservation()
        res.res_id = Reservation.get_next_id()
        res.spot_id = spot_id
        res.user_id = user.user_id
        res.reservation_start = datetime.now().strftime(DATEFORMAT)
        user.reservations.append(res)
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
                dur = (any_to_datetime(r.parking_start) -
                       any_to_datetime(r.reservation_start)).total_seconds()
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
        begin = any_to_datetime(reservation.reservation_start)
        end = datetime.now()
        reservation.parking_start = end.strftime(DATEFORMAT)
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

    # diese Methode wird durch IoT Gateway aufgerufen
    def end_parking(self, token, reservationid):
        response = self.authservice.get_email_from_token(token)
        if not response['status']:
            return False
        user = User(response['email'])
        reservation = self.get_user_reservation_for_id(user, reservationid)
        if reservation is None:
            return False
        lot = ParkingLot(reservation.spot_id)
        begin = any_to_datetime(reservation.parking_start)
        end = datetime.now()
        reservation.parking_end = end.strftime(DATEFORMAT)
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
        # TODO check if reservation is active

        response = self.authservice.get_email_from_token(token)
        if not response['status']:
            return False
        user = User(response['email'])
        if user.balance is None:
            user.balance = Decimal(0)
        reservation = self.get_user_reservation_for_id(user, reservationid)
        if reservation is None:
            return False

        spot = ParkingSpot(reservation.spot_id)
        lot = ParkingLot(spot.lot_id)
        begin, end = any_to_datetime(reservation.reservation_start), datetime.now()
        reservation.parking_start = reservation.parking_end = end.strftime(DATEFORMAT)

        duration = (end - begin).total_seconds()
        days = (end - begin).days
        tax = (lot.reservation_tax * Decimal(duration)) / Decimal(3600)
        if tax > lot.max_tax * Decimal(days + 1):  # todo müssen wir mehrtägiges Parken berücksichtigen?
            tax = lot.max_tax * Decimal(days + 1)
        user.balance -= Decimal(tax)
        user.save()
        user.flush()

        lot.removeReservation(reservation.spot_id)
        return tax

    @staticmethod
    def get_user_reservation_for_id(user, reservationid):
        try:
            return next(x for x in user.reservations if int(x.res_id) == int(reservationid))
        except StopIteration as ex:
            return None


class AccountingAndBillingClient(Client):
    def __init__(self):
        super().__init__("Accounting")

    def sign_up(self, info):
        return self.call("sign_up", info)

    def fetch_user_data(self, token):
        return self.call("fetch_user_data", token)

    def update_user_data(self, token: str, updata: dict, join: bool) -> dict:
        return self.call("update_user_data", token, updata, join)

    def reserve_parking_spot(self, token: str, lot_id: int, spottype: int) -> bool:
        return self.call("reserve_parking_spot", token, lot_id, spottype)

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
