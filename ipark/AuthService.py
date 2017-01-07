from communication.Service import Service
from communication.Client import Client
import AccountingBillingService

import uuid


class AuthService(Service):
    def __init__(self):
        self.tokens_issued = {}
        self.token_prefix = str(uuid.uuid4())  # ist das ok?
        self.abservice = AccountingBillingService.AccountingAndBillingClient()
        super().__init__("AuthService")

    def login(self, email, password):
        if not self.abservice.validate_user(email, password)["status"]:
            return {"status": False, "message": "Invalid password or user."}
        return {"status": True, "token": self.issue_token(email)}

    def validate_token(self, token):
        if token not in self.tokens_issued:
            return {"status": False, "message": "Invalid Token."}
        return {"status": True}  # Todo müssen wir hier nicht noch irgendwie email / user-ID zurückgeben?

    def issue_token(self, email):  # das hier reicht mMn für den Proof of Concept erstmal
        token = self.token_prefix + str(uuid.uuid4())
        while token in self.tokens_issued:
            token = self.token_prefix + str(uuid.uuid4())
        self.tokens_issued[token] = email
        return token


class AuthClient(Client):
    def __init__(self):
        super().__init__("AuthService")

    def login(self, email, password):
        return self.call("login", email, password)

    def validate_token(self, token):
        return self.call("validate_token", token)


if __name__ == "__main__":
    service = AuthService()