import uuid


class AuthService(object):
    id = 0

    def __init__(self, svc_repo):
        self.tokens_issued = []
        # 0:0>4X bedeutet: 0. Index, fülle mit 0en auf, rechtbündig, 4 Stellen, Hexadezimal
        self.token_prefix = "{0:0>4X}".format(AuthService.id)
        AuthService.id += 1
        self.service_repo = svc_repo
        self.account_billing_service = None

    def login_user(self, email, password):
        self.acquire_required_services()
        if self.account_billing_service[0].login_user(email, password):
            return True, self.issue_token(email)
        return False, "Some error occured"

    def validate_token(self, token):  # TODO ggf. anpassen falls Rechtemanagement etc. erforderlich
        if token in self.tokens_issued:
            return True
        return False

    def acquire_required_services(self):
        if self.account_billing_service is None:
            self.account_billing_service = self.service_repo.get_service("A&B")
        if self.account_billing_service is None:
            raise Exception("No A&B Service available")

    def issue_token(self, email):  # das hier reicht mMn für den Proof of Concept erstmal
        token = self.token_prefix + str(uuid.uuid4())
        while token in self.tokens_issued:
            token = self.token_prefix + str(uuid.uuid4())
        self.tokens_issued[token] = email
        return token