from frontend.DomainClasses import *
from flask_restplus import Api, marshal
from flask import request
from hashlib import md5

users = {}  # type: dict[str: User]


def user_signup(api: Api):
    m = generateToken(api.payload['email'], api.payload['password'])
    if m not in users:
        users[m] = api.payload
        return user_login(api)
    else:
        api.abort(422, "User already exists")


def user_login(api: Api):
    m = generateToken(api.payload['email'], api.payload['password'])
    if m in users:
        return {'token': m}, 200
    api.abort(422, "Invalid Credentials")


def user_status_get(api: Api, **kwargs):
    if 'X-Token' not in request.headers or request.headers['X-Token'] not in users:
        api.abort(401, "Invalid Token")
        return
    user = users[request.headers['X-Token']]

    return {'info': {'lastname': user.get('lastname', 'noname')}}, 200


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
