import uuid

from communication.Client import Client
from communication.Service import Service
from model.User import User, NotFoundException


class AuthService(Service):
    def __init__(self):
        super().__init__("AuthService")
        from model.DatabaseObject import DatabaseObject
        self.r = DatabaseObject.r

        # start or increment a counter KEY[1] that expires KEY[2] seconds after start
        self.increx_script = self.r.script_load("local a = redis.call('incr', KEYS[1]) "
                                                "if a <= 1 then redis.call('expire', KEYS[1], KEYS[2]); end "
                                                "return a")

    def login(self, email, password):
        if not self.validate_user(email, password)["status"]:
            return {"status": False, "message": "Invalid password or user."}

        # limit token generation per user
        if self.r.evalsha(self.increx_script, 2, email + ':num_tokens', 180) > 5:
            return {"status": False, "message": "Too many concurrent logins"}

        return {"status": True, "token": self.issue_token(email)}

    def validate_user(self, email, password):
        try:
            User(email, password, readonly=True)
        except NotFoundException:
            return {"status": False, "message": "Invalid mail address or password."}
        return {"status": True}

    def validate_token(self, token):
        if not self.r.exists("token:" + token):
            return {"status": False, "message": "Invalid Token."}
        return {"status": True}  # Todo müssen wir hier nicht noch irgendwie email / user-ID zurückgeben?

    def issue_token(self, email):
        token = str(uuid.uuid4())  # das hier reicht mMn für den Proof of Concept erstmal
        # while self.r.exists("token:" + token):
        #    token = str(uuid.uuid4())
        # self.r.setex("token:" + token, 1800, email)
        while not self.r.setnx("token:" + token, email):
            token = str(uuid.uuid4())
        return token

    def get_email_from_token(self, token):
        if not self.r.exists("token:" + token):
            print("Auth")
            return {"status": False, "message": "Invalid Token"}
        return {"email": self.r.get("token:" + token).decode(), "status": True}


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
