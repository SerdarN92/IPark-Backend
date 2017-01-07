from communication.Service import Service
from communication.Client import Client
import AuthService
import redis
from model.User import User


class AccountingAndBillingService(Service):
    def __init__(self):
        self.authservice = AuthService.AuthClient()
        super().__init__("Accounting")

    def sign_up(self, email, password):
        if User.create(email, password) is None:
            return {"status": False, "message": "Mail address is already in use."}
        result = self.authservice.login(email, password)
        return {"status": True, "token": result["token"]}


class AccountingAndBillingClient(Client):
    def __init__(self):
        super().__init__("Accounting")

    def sign_up(self, email, password):
        return self.call("sign_up", email, password)

if __name__ == "__main__":
    service = AccountingAndBillingService()
