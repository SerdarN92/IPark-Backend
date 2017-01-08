from communication.Service import Service
from communication.Client import Client
from model.User import User
import redis
import uuid


class AuthService(Service):
    def __init__(self):
        self.r = redis.StrictRedis(host='132.252.152.57')
        self.r.execute_command("AUTH GS~FsB3~&c7T")
        super().__init__("AuthService")

    def login(self, email, password):
        if not self.validate_user(email, password)["status"]:
            return {"status": False, "message": "Invalid password or user."}
        return {"status": True, "token": self.issue_token(email)}

    def validate_user(self, email, password):
        try:
            User(email, password, readonly=True)
        except User.NotFoundException:
            return {"status": False, "message": "Invalid mail address or password."}
        return {"status": True}

    def validate_token(self, token):
        if not self.r.exists("token:"+token):
            return {"status": False, "message": "Invalid Token."}
        return {"status": True}  # Todo müssen wir hier nicht noch irgendwie email / user-ID zurückgeben?

    def issue_token(self, email):  # das hier reicht mMn für den Proof of Concept erstmal
        token = str(uuid.uuid4())
        while self.r.exists("token:"+token):
            token = str(uuid.uuid4())
        self.r.setex("token:"+token, 1800, email)
        return token

    def get_email_from_token(self, token):
        if not self.r.exists("token:"+token):
            print("Auth")
            return {"status": False, "message": "Invalid Token"}
        return {"email": self.r.get("token:"+token).decode(), "status": True}


class AuthClient(Client):
    def __init__(self):
        super().__init__("AuthService")

    def login(self, email, password):
        return self.call("login", email, password)

    def validate_token(self, token):
        return self.call("validate_token", token)

    def validate_user(self, email, password):
        return self.call("validate_user", email, password)

    def get_email_from_token(self, token):
        return self.call("get_email_from_token", token)


if __name__ == "__main__":
    service = AuthService()