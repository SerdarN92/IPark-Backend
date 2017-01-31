from decimal import Decimal

from communication.Service import Service
from communication.Client import Client
import AuthService
from datetime import datetime, timedelta
from model.DomainClasses import Reservation
from model.ParkingLot import ParkingLot, ParkingSpot
from model.User import User, NotFoundException
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
            if k2 not in j or type(j[k2]) not in (dict, list):
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


def any_to_string(o):
    if isinstance(o, str):
        return o
    if isinstance(o, datetime):
        return o.strftime(DATEFORMAT)
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
            return None
        user = User(response['email'], readonly=True)
        if any(r.parking_end is None for r in user.reservations):
            return None

        lot = ParkingLot(lot_id)
        spot_id = lot.reserve_free_parkingspot(spottype)
        spot = ParkingSpot(spot_id)

        res = Reservation()
        res.res_id = Reservation.get_next_id()
        res.spot_id = spot_id
        res.user_id = user.user_id
        res.reservation_start = datetime.now().strftime(DATEFORMAT)
        res.map_to_email(user.email)

        user.reservations.append(res)
        user.flush()

        r = {"id": res.res_id, "lot_id": lot.lot_id, "spot_id": spot_id, "number": spot.number,
             "reservation_start": any_to_string(res.reservation_start), 'lot': lot.get_data_dict()}
        if res.parking_start is not None:
            r["parking_start"] = any_to_string(res.parking_start)
        if res.parking_end is not None:
            r["parking_end"] = any_to_string(res.parking_end)
        return r

    def fetch_reservation_data(self, token):
        response = self.authservice.get_email_from_token(token)
        if not response['status']:
            return False
        user = User(response['email'], readonly=True)
        reservations = []
        for r in user.reservations:
            p = ParkingSpot(r.spot_id)
            res = {"id": r.res_id, "lot_id": p.lot_id, "spot_id": p.spot_id, "number": p.number,
                   "reservation_start": any_to_string(r.reservation_start)}
            if r.parking_start is not None:
                res["parking_start"] = any_to_string(r.parking_start)
            if r.parking_end is not None:
                res["parking_end"] = any_to_string(r.parking_end)
            reservations.append(res)
        return reservations

    def fetch_reservation_data_for_id(self, token, res_id):
        response = self.authservice.get_email_from_token(token)
        if not response['status']:
            return False
        user = User(response['email'], readonly=True)
        try:
            r = next(x for x in user.reservations if x.res_id == res_id)
        except StopIteration:
            return False
        p = ParkingSpot(r.spot_id)
        res = {"id": r.res_id, "lot_id": p.lot_id, "spot_id": p.spot_id, "number": p.number,
               "reservation_start": any_to_string(r.reservation_start)}
        if r.parking_start is not None:
            res["parking_start"] = any_to_string(r.parking_start)
        if r.parking_end is not None:
            res["parking_end"] = any_to_string(r.parking_end)
        return res

    def begin_parking(self, token, reservationid):
        response = self.authservice.get_email_from_token(token)
        if not response['status']:
            return False
        user = User(response['email'])
        reservation = self.get_user_reservation_for_id(user, reservationid)
        if reservation is None:
            return False
        spot = ParkingSpot(reservation.spot_id)
        lot = ParkingLot(spot.lot_id)
        begin = any_to_datetime(reservation.reservation_start)
        end = datetime.now()
        reservation.parking_start = end.strftime(DATEFORMAT)
        # tax wird auf die Sekunde genau berechnet!
        duration = (end - begin).total_seconds()
        tax = (lot.reservation_tax * Decimal(duration)) / Decimal(3600)
        days = (end - begin).days
        if tax > lot.max_tax * Decimal(days + 1):  # todo müssen wir mehrtägiges Parken berücksichtigen?
            tax = lot.max_tax * Decimal(days + 1)
        user.balance -= Decimal(tax)
        user.save()
        user.flush()
        return tax

    # diese Methode wird durch IoT Gateway aufgerufen
    def end_parking(self, reservationid, duration):
        try:
            user = User(Reservation.get_email_from_resid(reservationid))
        except NotFoundException:
            return  # todo ?
        reservation = self.get_user_reservation_for_id(user, reservationid)
        if reservation is None or reservation.parking_end is not None:
            return
        spot = ParkingSpot(reservation.spot_id)
        lot = ParkingLot(spot.lot_id)
        begin = any_to_datetime(reservation.parking_start)
        end = begin + timedelta(seconds=duration)
        reservation.parking_end = end.strftime(DATEFORMAT)
        duration = (end - begin).total_seconds()
        days = (end - begin).days
        tax = (lot.tax * Decimal(duration)) / Decimal(3600)
        if tax > lot.max_tax * Decimal(days + 1):  # todo müssen wir mehrtägiges Parken berücksichtigen?
            tax = lot.max_tax * Decimal(days + 1)
        lot.removeReservation(reservation.spot_id)
        user.balance -= Decimal(tax)
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
    def get_user_reservation_for_id(user: User, reservationid: int) -> Reservation:
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

    def end_parking(self, resid, duration):
        return self.call("end_parking", resid, duration)

    def fetch_reservation_data_for_id(self, token, res_id):
        return self.call("fetch_reservation_data_for_id", token, res_id)


if __name__ == "__main__":
    service = AccountingAndBillingService()
