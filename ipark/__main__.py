import ssl

import MySQLdb

from AccountingBillingService import AccountingAndBillingService
from AuthService import AuthService
from GeoService import GeoService
from frontend.APIFrontend import app
from model.DatabaseObject import DatabaseObject
from model.ParkingLot import ParkingLot

# INITIALIZE REDIS
if not DatabaseObject.r.exists('reservationsLastId'):
    with DatabaseObject.my.cursor() as cur:
        try:
            if cur.execute("SELECT `AUTO_INCREMENT` - 1 as a FROM  INFORMATION_SCHEMA.TABLES "
                           "WHERE TABLE_SCHEMA = %s AND   TABLE_NAME   = %s", ('ipark', 'reservations')) != 1:
                assert False
            # print(cur.fetchall()[0].values()[0])
            DatabaseObject.r.set('reservationsLastId', cur.fetchall()[0]['a'])
        except MySQLdb.IntegrityError:
            assert False
        DatabaseObject.my.commit()

if not DatabaseObject.r.exists('parkinglots'):
    ParkingLot.import_parkinglots()

# START SERVICES
abservice = AccountingAndBillingService()
authservice = AuthService()
geoservice = GeoService()

# HTTP
# app.run(host="0.0.0.0", port=80, debug=False, threaded=True)
# HTTPS self signed
# app.run(host="0.0.0.0", port=443, debug=False, threaded=True, ssl_context='adhoc')
# HTTPS
context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
context.load_cert_chain('assets/fullchain1.pem', 'assets/privkey1.pem')
app.run(host="0.0.0.0", port=443, debug=False, threaded=True, ssl_context=context)
