from AccountingBillingService import AccountingAndBillingService
from AuthService import AuthService
from GeoService import GeoService
from frontend.APIFrontend import app

abservice = AccountingAndBillingService()
authservice = AuthService()
geoservice = GeoService()

# app.run(host="0.0.0.0", port=443, debug=False, threaded=True, ssl_context=('assets/cert.crt', 'assets/cert.key'))
# app.run(host="0.0.0.0", port=443, debug=False, threaded=True, ssl_context='adhoc')

app.run(host="0.0.0.0", port=80, debug=False, threaded=True)
