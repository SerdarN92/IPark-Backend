from AccountingBillingService import AccountingAndBillingService, AccountingAndBillingClient
from AuthService import AuthService, AuthClient
from GeoService import GeoService, GeoClient
from model.DatabaseObject import DatabaseObject


class PrintColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def test_case(condition, name):
    if condition:
        print(PrintColors.OKGREEN + "OK:\t" + name + PrintColors.ENDC)
    else:
        print(PrintColors.FAIL + "ERR:\t" + name + PrintColors.ENDC)


# Test Client
class TestAccountingAndBillingServiceClient(AccountingAndBillingClient):
    def test_sign_up(self):
        print(PrintColors.HEADER + "Testing Accounting And Billing Sign up" + PrintColors.ENDC)
        test_case("token" in self.sign_up("horst@localhorst", "password"), "Basic sign up")

        exp = {"status": False, "message": "Mail address is already in use."}
        test_case(self.sign_up("horst@localhorst", "password") == exp, "Sign up with used mail address")

    def run_all_tests(self):
        self.test_sign_up()


class TestAuthServiceClient(AuthClient):
    def test_login(self,):
        print(PrintColors.HEADER + "Testing Auth Login" + PrintColors.ENDC)
        test_case("token" in self.login("horst@localhorst", "password"), "Basic Login")
        exp = {"status": False, "message": "Invalid password or user."}
        test_case(exp == self.login("horst@localhorst", "passw0rd"), "Wrong password")
        test_case(exp == self.login("horst@localorst", "password"), "Invalid User")
        test_case(exp == self.login("horst@localorst", "passw0rd"), "Invalid User using wrong password :-P")

    def test_validate_user(self):
        print(PrintColors.HEADER + "Testing Auth User Validation" + PrintColors.ENDC)
        exp = {"status": True}
        test_case(self.validate_user("horst@localhorst", "password") == exp, "Basic user validation")
        exp = {'status': False, 'message': 'Invalid mail address or password.'}
        test_case(self.validate_user("horst@localhorst", "passxord") == exp, "Invalid password")
        test_case(self.validate_user("horst@localorst", "passxord") == exp, "Invalid mail and password")
        test_case(self.validate_user("horst@localorst", "password") == exp, "Invalid mail")

    def test_validate_token(self):
        print(PrintColors.HEADER + "Testing Auth Token Validation" + PrintColors.ENDC)
        result = self.login("horst@localhorst", "password")
        test_case(self.validate_token(result["token"])["status"], "Token Validation")

    def run_all_tests(self):
        self.test_login()
        self.test_validate_user()
        self.test_validate_token()


if __name__ == "__main__":
    abservice = AccountingAndBillingService()
    authservice = AuthService()
    geoservice = GeoService()
    print(GeoClient().find_near_parking_lots(51.4, 7.03, 6))
    a = TestAccountingAndBillingServiceClient()
    a.run_all_tests()
    b = TestAuthServiceClient()
    b.run_all_tests()
# service.stop()
