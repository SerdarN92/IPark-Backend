from flask_restplus import Api
from AuthService import AuthClient
from AccountingBillingService import AccountingAndBillingClient
from GeoService import GeoClient
from model.ParkingLot import FullException
from flask import request

auth_client = AuthClient()
accounting_client = AccountingAndBillingClient()
geo_client = GeoClient()


def user_signup(api: Api):
    sign_up_result = accounting_client.sign_up(api.payload)
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
    if 'X-Token' not in request.headers or not auth_client.validate_token(request.headers["X-Token"])["status"]:
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
    if 'X-Token' not in request.headers or not auth_client.validate_token(request.headers["X-Token"])["status"]:
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
    if 'X-Token' not in request.headers or not auth_client.validate_token(request.headers["X-Token"])["status"]:
        api.abort(401, "Invalid Token")
        return
    status = accounting_client.update_user_data(request.headers["X-Token"], api.payload)
    print(status)
    if "status" not in status or not status["status"]:
        api.abort(401, "Invalid Token or arguments")
        return
    return {'message': 'Success'}, 200


def get_nearby_parkinglots(api: Api):
    if 'X-Token' not in request.headers or not auth_client.validate_token(request.headers["X-Token"])["status"]:
        print("X-Token")
        api.abort(401, "Invalid Token")
    lots = geo_client.find_near_parking_lots(api.payload['location']['lon'], api.payload['location']['lat'],
                                             api.payload['radius'])  # type: list[ParkingLot]

    lots = [x.get_data_dict() for x in lots]
    return {'found_lots': len(lots), 'lots': lots}, 200


def reserve_parking_spot(api: Api):
    if 'X-Token' not in request.headers or not auth_client.validate_token(request.headers["X-Token"])["status"]:
        print("X-Token")
        api.abort(401, "Invalid Token")
    try:
        accounting_client.reserve_parking_spot(request.headers["X-Token"], api.payload['lot_id'])
        return {}, 201
    except FullException as ex:
        api.abort(422, "Lot is full")
    except BaseException as ex:
        api.abort(400, ex.__class__.__name__)

def get_reservation_data(api: Api):
    if 'X-Token' not in request.headers or not auth_client.validate_token(request.headers["X-Token"])["status"]:
        print("X-Token")
        api.abort(401, "Invalid Token")
    reservation_result = accounting_client.fetch_reservation_data(request.headers["X-Token"])
    print(reservation_result)
