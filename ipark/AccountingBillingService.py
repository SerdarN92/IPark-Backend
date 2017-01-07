from communication.Service import Service
from communication.Client import Client
import AuthService
import redis


class AccountingAndBillingService(Service):
    def __init__(self):
        self.authservice = AuthService.AuthClient()
        self.r = redis.StrictRedis(host='132.252.152.57')
        self.r.execute_command("AUTH GS~FsB3~&c7T")
        super().__init__("Accounting")

    def sign_up(self, email, password):
        if self.r.exists("user:" + email):
            return {"status": False, "message": "Mail address is already in use."}
        u = {"email": email, "password": password}  # Todo weitere Userdaten
        self.r.hmset("user:"+email, u)
        result = self.authservice.login(email, password)
        return {"status": True, "token": result["token"]}

    def validate_user(self, email, password):
        if not self.r.exists(b"user:" + email):
            return {"status": False, "message": "Invalid mail address or password."}
        user = self.r.hgetall(b"user:"+email)
        if password != user[b"password"].decode():
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
