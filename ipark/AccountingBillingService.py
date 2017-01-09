from communication.Service import Service
from communication.Client import Client
import AuthService
from model.User import User


class AccountingAndBillingService(Service):
    def __init__(self):
        self.authservice = AuthService.AuthClient()
        super().__init__("Accounting")

    def sign_up(self, email, password, first_name=None, last_name=None, address=None):
        newbody = User.create(email, password)
        if newbody is None:
            return {"status": False, "message": "Mail address is already in use."}
        if first_name is not None:
            pass
        if last_name is not None:
            pass
        if address is not None:
            pass
        result = self.authservice.login(email, password)
        return {"status": True, "token": result["token"]}

    def fetch_user_data(self, token):
        user = self.authservice.get_email_from_token(token)
        if "status" not in user or not user["status"]:
            return {"status": False, "message": "Invalid Token."}
        ruser = User(user["email"], readonly=True)
        return {"status": True, "user": ruser.get_data_dict()}

    def update_user_data(self, token, updata):
        user = self.authservice.get_email_from_token(token)
        if "status" not in user or not user["status"]:
            return {"status": False, "message": "Invalid Token."}
        if "password" in updata or "balance" in updata or "dataflags" in updata or "user_id" in updata:
            return {"status": False, "message": "Invalid Arguments."}
        wuser = User(user["email"])
        if "address" in updata:
            wuser.address = updata["address"]
        if "last_name" in updata:
            wuser.last_name = updata["last_name"]
        if "first_name" in updata:
            wuser.first_name = updata["first_name"]
        wuser.save()
        wuser.flush()
        return {"status": True}


class AccountingAndBillingClient(Client):
    def __init__(self):
        super().__init__("Accounting")

    def sign_up(self, email, password):
        return self.call("sign_up", email, password)

    def fetch_user_data(self, token):
        return self.call("fetch_user_data", token)

    def update_user_data(self, token, updata):
        return self.call("update_user_data", token, updata)


if __name__ == "__main__":
    service = AccountingAndBillingService()
