from flask_restplus import Api
from AuthService import AuthClient
from AccountingBillingService import AccountingAndBillingClient
from flask import request
from hashlib import md5

users = {}  # type: dict[str: User]
auth_client = AuthClient()
accounting_client = AccountingAndBillingClient()


def user_signup(api: Api):
    sign_up_result = accounting_client.sign_up(api.payload['email'], api.payload['password'])
    if "token" in sign_up_result:
        return {"token": sign_up_result["token"]}, 200
    else:
        api.abort(422, "User already exists")


def user_login(api: Api):
    login_result = auth_client.login(api.payload["email"], api.payload["password"])
    if "token" in login_result:
        return {'token': login_result["token"]}, 200
    api.abort(422, "Invalid Credentials")


def user_status_get(api: Api, **kwargs):
    if 'X-Token' not in request.headers or not auth_client.validate_token(request.headers["X-Token"])["status"]:
        api.abort(401, "Invalid Token")
        return
    return {'info': {'lastname': 'noname'}}, 200


def user_status_set(api: Api, **kwargs):
    if 'X-Token' not in request.headers or request.headers['X-Token'] not in users:
        api.abort(401, "Invalid Token")
        return
    user = users[request.headers['X-Token']]

    if 'info' not in api.payload or 'lastname' not in api.payload['info']:
        api.abort(422, 'Invalid Arguments', argument='lastname')

    user['lastname'] = api.payload['info']['lastname'] or user.get('lastname', 'noname')
    return {'message': 'Success'}, 200


def generateToken(*args):
    m = md5()  # type: hashlib.md5
    m.update(''.join(args).encode())
    return m.hexdigest()
