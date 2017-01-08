from flask import Flask
from flask_restplus import Api, Resource, fields, errors

from frontend.APIFrontendRequests import *

app = Flask(__name__)
api = Api(app, version='1.0', title='iPark', description='iPark Frontend')

ns = api.namespace('ipark/v1', description='iPark API')

credentials = api.model('User Credentials', {
    'email': fields.String(required=True, description='E-Mail Address'),
    'password': fields.String(required=True, description='Password')
})

authentication = api.model('User Authentication', {
    'email': fields.String(required=True, description='E-Mail Address'),
    'token': fields.String(required=True, description='Authentication Token')
})

location = api.model('Location', {
    'lat': fields.Fixed(decimals=7, required=True, description='Latitude'),
    'lon': fields.Fixed(decimals=7, required=True, description='Longitude')
})
spot = api.inherit('Parking Spot', location, {})
tariff = api.model('Tariff', {'pricePerMinute': fields.Arbitrary(description="Price per Minute")})
reservation = api.model('Reservation', {
    'spot': fields.Nested(spot, required=True, description="Parking Spot"),
    'time': fields.DateTime(required=True, description="Time of Reservation"),
    'duration': fields.Integer(description="Minutes of Reservation (-1 if active)", min=-1),
    'active': fields.Boolean(required=True, description="if reservation duration is increasing"),
    'tariff': fields.Nested(tariff, required=True, description="Tariff")
})
invoice = api.model('Invoice', {'reservation': fields.Nested(reservation, description="Reservation")})
payment_method = api.model('Payment Methods', {})
nearby_lots = api.model('Nearby Lots', {
    'precision': fields.Integer(description='Radius of Parking Lots'),
    'lots': fields.List(fields.Nested(location))
})
info = api.model('User Info', {'lastname': fields.String(description="Last Name", required=False),
                               "password": fields.String(description="Password")})
userstatus = api.model('Status', {
    'info': fields.Nested(info, description="General User Information"),
    'used_spots': fields.List(fields.Nested(spot), description="Currently used parking spots"),
    'reservations': fields.List(fields.Nested(reservation), description="Active reservations")
})

authentication_error = api.model('User Authentication Error', {
    'message': fields.String(readOnly=True, required=False, description='Error Message')
})
argument_error = api.inherit('Argument Error', authentication_error, {
    'argument': fields.String(readOnly=True, required=False, description='Invalid Argument')
})


@ns.route("/user/sign_up")
class UserSignup(Resource):
    """User Sign Up"""

    @ns.doc('')
    @ns.expect(credentials, validate=True)
    @ns.marshal_with(api.model('Token', {'token': fields.String(required=True)}),
                     code=200, description='Sign Up successful')
    @ns.response(401, 'Authentication Error', model=authentication_error)
    @ns.response(422, 'Invalid Arguments', model=argument_error)
    def post(self):
        """User Sign Up"""
        return user_signup(api)


@ns.route("/user/login")
class UserLogin(Resource):
    """ Request Authentication Token """

    @ns.doc('Request Authentication Token')
    @ns.expect(credentials, validate=True)
    @ns.marshal_with(api.model('Token', {'token': fields.String(required=True)}),
                     code=200, description='Login successful')
    @ns.response(401, 'Authentication Error', model=authentication_error)
    def post(self):
        """ Request Authentication Token """
        return user_login(api)


@ns.route("/user/status/<string:ufilter>")
@ns.param("ufilter")
@ns.header('X-Token', 'Authentication Token', required=True, type=str)
@ns.response(401, 'Authentication Error', model=authentication_error)
@ns.response(422, 'Invalid Arguments', model=argument_error)
class UserStatus(Resource):
    """ Request User Status """

    @ns.marshal_with(userstatus, code=200, description='Successful')
    @ns.doc('Request User Status')
    def get(self, ufilter):
        """ Request User Status """
        return user_status_get(api, ufilter)

    @ns.expect(userstatus, validate=True)
    @ns.marshal_with(api.model('Successful', {'message': fields.String()}), code=200, description='Successful')
    @ns.doc('Set User Status')
    def post(self, **kwargs):
        """ Set User Status """
        return user_status_set(api, **kwargs)


@ns.route("/billing")
class UserBilling(Resource):
    """ List of Invoices """

    @ns.doc('List of Invoices')
    @ns.header('X-Token', 'Authentication Token', required=True, type=str)
    @ns.marshal_list_with(invoice, code=200, description='Successful')
    @ns.marshal_with(authentication_error, code=401, description='Authentication Error')
    @ns.marshal_with(argument_error, code=422, description='Invalid Arguments')
    def post(self):
        """ Request List of Invoices """
        return None, 500


@ns.route('/user/payment_methods')
class PaymentMethods(Resource):
    """List of Payment Methods"""

    @ns.doc('')
    @ns.header('X-Token', 'Authentication Token', required=True, type=str)
    @ns.marshal_list_with(payment_method, code=202, description='List of Payment Methods')
    def get(self):
        """List of Payment Methods"""
        return None, 500

    @ns.doc('')
    @ns.header('X-Token', 'Authentication Token', required=True, type=str)
    @ns.marshal_with(api.model('Payment Method Edited', {}), code=200, description='Payment Method Edited')
    @ns.marshal_with(api.model('Payment Method Added', {}), code=201, description='Payment Method Added')
    @ns.marshal_with(authentication_error, code=401, description='Authentication Error')
    @ns.marshal_with(argument_error, code=422, description='Invalid Arguments')
    def post(self):
        """Edit of Payment Methods"""
        return None, 500


@ns.route('/parking')
class ParkingSpots(Resource):
    """ Parking Lots and Spots """

    @ns.doc('')
    @ns.header('X-Token', 'Authentication Token', required=True, type=str)
    @ns.marshal_with(nearby_lots, code=200, description='List of Parking Lots')
    @ns.marshal_with(authentication_error, code=401, description='Authentication Error')
    @ns.marshal_with(argument_error, code=422, description='Invalid Arguments')
    def get(self):
        """ List of nearby Parking Lots """
        return None, 500

    @ns.doc('')
    @ns.header('X-Token', 'Authentication Token', required=True, type=str)
    # @ns.expect()
    @ns.marshal_with(api.model('Reservation Successful', {}), code=201, description='Reservation Successful')
    @ns.marshal_with(authentication_error, code=401, description='Authentication Error')
    @ns.marshal_with(argument_error, code=422, description='Invalid Arguments')
    def post(self):
        """ Reservate Parking Spots """
        return None, 500


@ns.route('/barrier/<int:id>')
@ns.param('id', description='ID of Reservation')
class Barrier(Resource):
    @ns.header('X-Token', 'Authentication Token', required=True, type=str)
    @ns.marshal_with(api.model('Barrier Status', {'status': fields.Integer('Status Open (1)/Closed (2)')}),
                     code=200, description='Barrier Status')
    @ns.marshal_with(authentication_error, code=401, description='Authentication Error')
    @ns.marshal_with(argument_error, code=422, description='Invalid Arguments')
    def get(self):
        """ Get Barrier State """
        return None, 500


@ns.route('/barrier/<int:id>/<int:status>')
@ns.param('status', required=False, description='Requested Status [Open (1)/Closed (2)]')
class BarrierSet(Resource):  # Barrier

    @ns.marshal_with(api.model('Barrier State', {'status': fields.Integer('Status Open (1)/Closed (2)')}),
                     code=200, description='Barrier State')
    @ns.marshal_with(authentication_error, code=401, description='Authentication Error')
    @ns.marshal_with(argument_error, code=422, description='Invalid Arguments')
    @ns.marshal_with(api.model('Too Many Requests', {}), code=429, description='Too Many Requests')
    def post(self):
        """ Open/Close Barrier """
        return None, 500


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=443, debug=False, threaded=True, ssl_context=('assets/cert.crt', 'assets/cert.key'))

