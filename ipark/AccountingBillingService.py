from communication.Service import Service
from model.DomainClasses import User
from communication.Client import Client
import AuthService


class AccountingAndBillingService(Service):
    def __init__(self):
        self.users = {}
        self.authservice = AuthService.AuthClient()
        super().__init__("Accounting")

    def sign_up(self, email, password):
        if email in self.users:
            return {"status": False, "message": "Mail address is already in use."}
        self.users[email] = User(email, password)  # Todo weitere Userdaten
        result = self.authservice.login(email, password)
        print(result)
        return {"status": True, "token": result["token"]}

    def validate_user(self, email, password):
        if email not in self.users:
            return {"status": False, "message": "Invalid mail address or password."}
        user = self.users[email]
        if password != user.password:
            return {"status": False, "message": "Invalid mail address or password."}
        return {"status": True}


class AccountingAndBillingClient(Client):
    def __init__(self):
        super().__init__("Accounting")

    def sign_up(self, email, password):
        return self.call("sign_up", email, password)

    def validate_user(self, email, password):
        return self.call("validate_user", email, password)

if __name__ == "__main__":
    service = AccountingAndBillingService()
