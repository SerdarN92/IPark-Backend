from flask import Flask
from flask_restplus import Resource, fields, Mask

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
lot = api.model('ParkingLot', {
    'lot_id': fields.String(required=True, description=''),
    'name': fields.String(required=True, description=''),
    'total_spots': fields.String(required=True, description=''),
    'longitude': fields.String(required=True, description=''),
    'latitude': fields.String(required=True, description=''),
    'tax': fields.String(required=True, description='Tax (€/h)'),
    'max_tax': fields.String(required=True, description='Tax limit per day'),
    'reservation_tax': fields.String(required=True, description='Reservation tax (€/h)'),
    'information': fields.String(required=True, description=''),
    'flags': fields.String(required=True, description=''),
    'free_spots': fields.List(fields.Integer()),
})
reservation = api.model('Reservation', {
    'id': fields.Integer(required=True, description="Unique identifier"),
    'lot_id': fields.Integer(required=True, description="Parking Lot id"),
    'number': fields.Integer(description="Parking spot number inside the parking lot (not globally unique)"),
    'spot_id': fields.Integer(description="Globally unique identifier of the parking spot"),
    'reservation_start': fields.String(required=True, description="Time of Reservation (e.g. 2017-01-14 18:43:56)"),
    'parking_start': fields.String(required=True,
                                   description="Beginning time of parking. Implies end of Reservation. "
                                               "(e.g. 2017-01-14 18:43:56)"),
    'parking_end': fields.String(required=True, description="End time of parking. (e.g. 2017-01-14 18:43:56)"),
    'lot': fields.Nested(lot, allow_null=True),
    'reservation_fee': fields.Arbitrary(),
    'parking_fee': fields.Arbitrary(),
})
invoice = api.model('Invoice', {'reservation': fields.Nested(reservation, description="Reservation", allow_null=True)})
payment_method = api.model('Payment Methods', {})
nearby_lots = api.model('Nearby Lots', {
    'found_lots': fields.Integer(required=True, description='Number of found Parking Lots'),
    'lots': fields.List(fields.Nested(lot, allow_null=True), required=True, description='Array of ParkingLots')
})
nearby_lots_request = api.model('Nearby Lots Request', {
    'radius': fields.Integer(description='Radius of Parking Lots in km'),
    'location': fields.Nested(location, required=True, allow_null=True),
    'type': fields.Integer(min=0)
})
info = api.model('User Info', {
    'first_name': fields.String(description="First Name"),
    'last_name': fields.String(description="Last Name"),
    "email": fields.String(description="E-Mail address"),
    'street': fields.String(description="new street"),
    'number': fields.String(description="new number"),
    'plz': fields.String(description="new plz"),
    'city': fields.String(description="new city"),
    'country': fields.String(description="new country"),
    'balance': fields.Arbitrary(description="Account balance"),
    'client_settings': fields.String(description="Arbitrary field for user settings")
})
userstatus = api.model('Status', {
    'info': fields.Nested(info, description="General User Information", allow_null=True),
    # 'used_spots': fields.List(fields.Nested(spot), description="Currently used parking spots",allow_null=True),
    # 'reservations': fields.List(fields.Nested(reservation), description="Active reservations",allow_null=True)
})

userupdate = api.model("User Update Info", {
    'last_name': fields.String(description="new last name"),
    'first_name': fields.String(description="new first name"),
    'street': fields.String(description="new street"),
    'number': fields.String(description="new number"),
    'plz': fields.String(description="new plz"),
    'city': fields.String(description="new city"),
    'country': fields.String(description="new country"),
    'client_settings': fields.String(description="Arbitrary field for user settings")
})

sign_up = api.inherit("Sign Up Request", userupdate, {
    'email': fields.String(required=True, description='E-Mail Address'),
    'password': fields.String(required=True, description='Password')
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
    @ns.expect(sign_up, validate=True)
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


@ns.route("/user/info")
@ns.header('X-Token', 'Authentication Token', required=True, type=str)
@ns.response(401, 'Authentication Error', model=authentication_error)
@ns.response(422, 'Invalid Arguments', model=argument_error)
class UserInfo(Resource):
    """ Request User Info """

    @ns.marshal_with(info, code=200, description='Successful')
    @ns.doc('Request User Info')
    def get(self):
        """ Request User Info """
        return user_info_get(api)

    @ns.param('join', description='Joins JSON Objects', _in='query')
    @ns.expect(userupdate, validate=True)
    @ns.marshal_with(api.model('Successful', {'message': fields.String()}), code=200, description='Successful')
    @ns.doc('Update User Details')
    def put(self):
        """ Set User Status """
        return user_info_set(api)


@ns.route("/user/info/<string:ufilter>")
@ns.param("ufilter", description="Key in info Object")
@ns.header('X-Token', 'Authentication Token', required=True, type=str)
@ns.response(401, 'Authentication Error', model=authentication_error)
@ns.response(422, 'Invalid Arguments', model=argument_error)
class UserStatus(Resource):
    """ Request User Status """

    @ns.marshal_with(userstatus, code=200, description='Successful', mask=Mask(skip=True))
    @ns.doc('Request User Status')
    def get(self, ufilter):
        """ Request User Status """
        return user_status_get(api, ufilter)


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
        api.abort(501)


@ns.route('/user/payment_methods')
@ns.response(401, 'Authentication Error', model=authentication_error)
@ns.response(422, 'Invalid Arguments', model=argument_error)
class PaymentMethods(Resource):
    """List of Payment Methods"""

    @ns.doc('')
    @ns.header('X-Token', 'Authentication Token', required=True, type=str)
    @ns.marshal_list_with(payment_method, code=202, description='List of Payment Methods')
    def get(self):
        """List of Payment Methods"""
        api.abort(501)

    @ns.doc('')
    @ns.header('X-Token', 'Authentication Token', required=True, type=str)
    @ns.marshal_with(api.model('Payment Method Edited', {}), code=200, description='Payment Method Edited')
    # @ns.marshal_with(api.model('Payment Method Added', {}), code=201, description='Payment Method Added')
    def post(self):
        """Edit of Payment Methods"""
        api.abort(501)


@ns.route('/parking/nearby_lots')
@ns.response(401, 'Authentication Error', model=authentication_error)
@ns.response(422, 'Invalid Arguments', model=argument_error)
class ParkingSpots(Resource):
    """ Parking Lots and Spots """

    @ns.doc('')
    @ns.header('X-Token', 'Authentication Token', required=True, type=str)
    @ns.marshal_with(nearby_lots, code=200, description='List of Parking Lots')
    @ns.expect(nearby_lots_request, validate=False)
    def post(self):
        """ List of nearby Parking Lots """
        return get_nearby_parkinglots(api)


@ns.route('/parking/reserve')
@ns.response(401, 'Authentication Error', model=authentication_error)
@ns.response(422, 'Invalid Arguments', model=argument_error)
@ns.response(409, 'This user cannot reserve spots (anymore)', model=api.model('Conflict', {}))
class ReserveParkingSpot(Resource):
    @ns.doc('Reserve Parking Spot by lot_id')
    @ns.header('X-Token', 'Authentication Token', required=True, type=str)
    @ns.expect(api.model('Parking lot', {'lot_id': fields.Integer('ID of parking lot'),
                                         'type': fields.Integer('Type of parking spot')}), validate=True)
    @ns.marshal_with(api.model('Reservation Successful', reservation),
                     code=201, description='Reservation Successful')
    def post(self):
        """ Reserve Parking Spots """
        return reserve_parking_spot(api)

    @ns.doc("Get the users reservations")
    @ns.header('X-Token', 'Authentication Token', required=True, type=str)
    @ns.marshal_with(api.model('Reservation List',
                               {"reservations": fields.List(fields.Nested(reservation),
                                                            description="List of reservations",
                                                            required=False,
                                                            allow_null=True)}))
    def get(self):
        return get_reservation_data(api)


@ns.route("/parking/<int:reservation_id>")
@ns.param('reservation_id', description='ID of Reservation')
@ns.response(401, 'Authentication Error', model=authentication_error)
@ns.response(422, 'Invalid Arguments', model=argument_error)
class ReservationData(Resource):
    @ns.doc("Get the reservation corresponding to the ID, if it belongs to the user")
    @ns.header('X-Token', 'Authentication Token', required=True, type=str)
    @ns.marshal_with(reservation, code=200, description="Reservation data")
    def get(self, reservation_id):
        return fetch_reservation(api, reservation_id)


@ns.route("/parking/<int:reservation_id>/cancel")
@ns.param('reservation_id', description='ID of Reservation')
@ns.response(401, 'Authentication Error', model=authentication_error)
@ns.response(422, 'Invalid Arguments', model=argument_error)
class CancelReservation(Resource):
    @ns.header('X-Token', 'Authentication Token', required=True, type=str)
    @ns.marshal_with(authentication_error, code=401, description='Authentication Error')
    @ns.marshal_with(argument_error, code=422, description='Invalid Arguments')
    @ns.marshal_with(api.model('Result of action', {
        'status': fields.Boolean(description="Whether the request could be fulfilled or not")}),
                     code=200, description='Status of the reservation')
    def post(self, reservation_id):
        return cancel_reservation(api, reservation_id)


@ns.route('/barrier/<int:reservation_id>')
@ns.param('reservation_id', description='ID of Reservation')
class Barrier(Resource):
    @ns.header('X-Token', 'Authentication Token', required=True, type=str)
    @ns.marshal_with(api.model('Barrier Status', {'status': fields.Integer('Status Open (1)/Closed (2)')}),
                     code=200, description='Barrier Status')
    @ns.marshal_with(authentication_error, code=401, description='Authentication Error')
    @ns.marshal_with(argument_error, code=422, description='Invalid Arguments')
    def get(self, reservation_id):
        """ Get Barrier State """
        api.abort(501)

    @ns.header('X-Token', 'Authentication Token', required=True, type=str)
    @ns.marshal_with(authentication_error, code=401, description='Authentication Error')
    @ns.marshal_with(argument_error, code=422, description='Invalid Arguments')
    @ns.marshal_with(api.model('Result of action', {
        'status': fields.Boolean(description="Whether the request could be fulfilled or not")}),
                     code=200, description='Status of the reservation')
    def put(self, reservation_id):
        return begin_parking(api, reservation_id)


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
        api.abort(501)


@ns.route('/parking/lotinfo/<int:lot_id>')
@ns.param('lot_id', required=True, description='ID of Lot')
@ns.header('X-Token', 'Authentication Token', required=True, type=str)
class LotInfo(Resource):
    @ns.marshal_with(lot, code=200)
    def get(self, lot_id):
        return get_lot_info(api, lot_id)


@ns.route('/iot/push/<int:lot_id>')
@ns.param('lot_id', required=True, description='ID of Lot')
@ns.header('X-Auth', 'Lot Authentication Key', required=True, type=str)
class IoTPush(Resource):
    def get(self, lot_id):
        return iot_push(api, lot_id)


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=1443, debug=False,
            threaded=True)  # , ssl_context=('assets/cert.crt', 'assets/cert.key'))
