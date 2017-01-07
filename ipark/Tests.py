from AccountingBillingService import AccountingAndBillingService
from AuthService import AuthService
import communication.Client


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
class TestAccountingAndBillingServiceClient(communication.Client.Client):
    def test_sign_up(self):
        print(PrintColors.HEADER + "Testing Accounting And Billing Sign up" + PrintColors.ENDC)
        test_case("token" in self.call("sign_up", "horst@localhorst", "password"), "Basic sign up")

        exp = {"status": False, "message": "Mail address is already in use."}
        test_case(self.call("sign_up", "horst@localhorst", "password") == exp, "Sign up with used mail address")

    def test_validate_user(self):
        print(PrintColors.HEADER + "Testing Accounting And Billing Validation" + PrintColors.ENDC)
        exp = {"status": True}
        test_case(self.call("validate_user", "horst@localhorst".encode(), "password".encode()) == exp, "Basic user validation")
        exp = {'status': False, 'message': 'Invalid mail address or password.'}
        test_case(self.call("validate_user", "horst@localhorst".encode(), "passxord".encode()) == exp, "Invalid password")
        test_case(self.call("validate_user", "horst@localorst".encode(), "passxord".encode()) == exp, "Invalid mail and password")
        test_case(self.call("validate_user", "horst@localorst".encode(), "password".encode()) == exp, "Invalid mail")

    def run_all_tests(self):
        self.test_sign_up()
        self.test_validate_user()


class TestAuthServiceClient(communication.Client.Client):
    def test_login(self,):
        print(PrintColors.HEADER + "Testing Auth Login" + PrintColors.ENDC)
        test_case("token" in self.call("login", "horst@localhorst".encode(), "password".encode()), "Basic Login")
        exp = {"status": False, "message": "Invalid password or user."}
        test_case(exp == self.call("login", "horst@localhorst".encode(), "passw0rd".encode()), "Wrong password")
        test_case(exp == self.call("login", "horst@localorst".encode(), "password".encode()), "Invalid User")
        test_case(exp == self.call("login", "horst@localorst".encode(), "passw0rd".encode()), "Invalid User using wrong password :-P")

    def run_all_tests(self):
        self.test_login()

if __name__ == "__main__":
    abservice = AccountingAndBillingService()
    authservice = AuthService()
    a = TestAccountingAndBillingServiceClient("Accounting")
    a.run_all_tests()
    b = TestAuthServiceClient("AuthService")
    b.run_all_tests()
# service.stop()
