import ssl
import sys

import MySQLdb

from frontend.APIFrontend import app
from model.DatabaseObject import DatabaseObject
from model.DomainClasses import Reservation
from model.ParkingLot import ParkingLot
from services.AccountingBillingService import AccountingAndBillingService
from services.AuthService import AuthService
from services.GeoService import GeoService
from services.PersistencyService import flush_redis_to_mysql
from services.PollingService import PollingService

if '--reload' in sys.argv:
    # CLEAN UP FOR COLD START
    flush_redis_to_mysql()
    DatabaseObject.r.flushall()

# INITIALIZE REDIS
if not DatabaseObject.r.exists('reservationsLastId'):
    with DatabaseObject.my.cursor() as cur:
        try:
            if cur.execute("SELECT `AUTO_INCREMENT` - 1 AS a FROM INFORMATION_SCHEMA.TABLES "
                           "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s", ('ipark', 'reservations')) != 1:
                assert False
            DatabaseObject.r.set('reservationsLastId', cur.fetchall()[0]['a'])
        except MySQLdb.IntegrityError:
            assert False
        DatabaseObject.my.commit()

if not DatabaseObject.r.exists('parkinglots'):
    ParkingLot.import_parkinglots()

if not False:  # Check for Reservation mapping inefficient
    with DatabaseObject.my.cursor() as cur:
        try:
            if cur.execute("SELECT res_id, email FROM `reservations` NATURAL JOIN users WHERE ISNULL(parking_end)") > 0:
                rows = cur.fetchall()
                res = Reservation()
                for row in rows:
                    res.res_id = int(row['res_id'])
                    res.map_to_email(row['email'])
        except MySQLdb.IntegrityError:
            assert False
        DatabaseObject.my.commit()

# START SERVICES
services = []
for i in range(5):
    services +=[AccountingAndBillingService(),
                AuthService(),
                GeoService(),
		PollingService(),
    ]

# HTTP
# app.run(host="0.0.0.0", port=80, debug=False, threaded=True)

# HTTPS self signed
# app.run(host="0.0.0.0", port=443, debug=False, threaded=True, ssl_context='adhoc')

# HTTPS
#context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
#context.load_cert_chain('assets/fullchain1.pem', 'assets/privkey1.pem')
#app.run(host="0.0.0.0", port=443, debug=False, threaded=True, ssl_context=context)
