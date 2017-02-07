from random import randint

from flask import request
from flask_restplus import Api
from werkzeug.exceptions import HTTPException

from model.ParkingLot import FullException
from model.User import NotFoundException
from services.AccountingBillingService import AccountingAndBillingClient
from services.AuthService import AuthClient
from services.GeoService import GeoClient

auth_client = AuthClient()
accounting_client = AccountingAndBillingClient()
geo_client = GeoClient()


def user_signup(api: Api):
    try:
        sign_up_result = accounting_client.sign_up(api.payload)
    except NotFoundException as ex:
        api.abort(500, "Created user not found")
    if "token" in sign_up_result:
        return {"token": sign_up_result["token"]}, 200
    else:
        api.abort(422, "User already exists")


def user_login(api: Api):
    login_result = auth_client.login(api.payload["email"], api.payload["password"])
    if "token" in login_result:
        return {'token': login_result["token"]}, 200
    api.abort(422, "Invalid Credentials")


def user_info_get(api: Api):
    if not check_auth(request.headers):
        api.abort(401, "Invalid Token")
        return
    user_result = accounting_client.fetch_user_data(request.headers["X-Token"])
    if "status" not in user_result or not user_result["status"]:
        api.abort(401, "Invalid Token")
        return
    if "user" in user_result:
        return user_result["user"], 200
    api.abort(500, "We apologize for having really bad behaving servers. Please try again later.")
    return


def user_status_get(api: Api, ufilter):
    if not check_auth(request.headers):
        api.abort(401, "Invalid Token")
        return
    user_result = accounting_client.fetch_user_data(request.headers["X-Token"])
    if "status" not in user_result or not user_result["status"]:
        api.abort(401, "Invalid Token")
        return
    if "user" in user_result and ufilter in user_result["user"]:
        return {'info': {ufilter: user_result["user"][ufilter]}}, 200
    api.abort(500, "We apologize for having really bad behaving servers. Please try again later.")
    return


def user_info_set(api: Api):
    if not check_auth(request.headers):
        api.abort(401, "Invalid Token")
        return
    status = accounting_client.update_user_data(request.headers["X-Token"], api.payload, 'join' in request.args)
    if "status" not in status or not status["status"]:
        api.abort(401, "Invalid Token or arguments")
        return
    return {'message': 'Success'}, 200


def get_nearby_parkinglots(api: Api):
    if not check_auth(request.headers):
        api.abort(401, "Invalid Token")
        return
    lots = geo_client.find_near_parking_lots(api.payload['location']['lon'], api.payload['location']['lat'],
                                             api.payload['radius'],
                                             lot_type=api.payload.get('type', None))  # type: list[ParkingLot]
    lots = [x.get_data_dict() for x in lots]
    return {'found_lots': len(lots), 'lots': lots}, 200


def reserve_parking_spot(api: Api):
    if not check_auth(request.headers):
        api.abort(401, "Invalid Token")
        return
    try:
        res = accounting_client.reserve_parking_spot(request.headers["X-Token"],
                                                     api.payload['lot_id'], api.payload['type'])
        if res is not None:
            return res, 201
        else:
            api.abort(409, 'Denied')
    except HTTPException as ex:
        raise
    except FullException as ex:
        api.abort(422, "Lot is full")
    except BaseException as ex:
        api.abort(500, ex.__class__.__name__)


def get_reservation_data(api: Api):
    if not check_auth(request.headers):
        api.abort(401, "Invalid Token")
        return
    res = accounting_client.fetch_reservation_data(request.headers["X-Token"])
    return {"reservations": res}, 200


def begin_parking(api: Api, reservation_id):
    if not check_auth(request.headers):
        api.abort(401, "Invalid Token")
    result = accounting_client.begin_parking(request.headers["X-Token"], reservation_id)

    if result:
        # FOR DEMO
        duration = randint(200, 400)
        accounting_client.delayed_call('end_parking', duration * 1000, reservation_id, duration)

        return {"status": True}, 200
    else:
        api.abort(422, "Invalid Arguments")


def fetch_reservation(api: Api, reservation_id):
    if not check_auth(request.headers):
        api.abort(401, "Invalid Token")
    result = accounting_client.fetch_reservation_data_for_id(request.headers["X-Token"], reservation_id)
    if result:
        return result, 200
    else:
        api.abort(422, "Invalid Arguments")


def cancel_reservation(api: Api, reservation_id):
    if not check_auth(request.headers):
        api.abort(401, "Invalid Token")
    if accounting_client.cancel_reservation(request.headers["X-Token"], reservation_id):
        return {"status": True}, 200
    else:
        api.abort(422, "Invalid Arguments")


def check_auth(headers):
    return 'X-Token' in headers and auth_client.validate_token(headers["X-Token"])["status"]


def get_lot_info(api: Api, lot_id: int):
    if not check_auth(request.headers):
        api.abort(401, "Invalid Token")
    lot = geo_client.get_lot(lot_id)  # type: ParkingLot
    if lot is not None:
        return lot.get_data_dict(), 200
    else:
        api.abort(422, 'lot_id not found')


def iot_push(api: Api, lot_id: int):
    if 'X-Auth' in request.headers and auth_client.validate_lot_pw(lot_id, request.headers['X-Auth']):
        return {}, 200
    else:
        return {}, 401
