from DomainClasses import User
import uuid

class ServiceRepository(object):
    """This class manages the different services"""

    def __init__(self):
        self.services = dict()  # Key: Name des service, value: Liste von IP-Adressen

    def register_service(self, kind: str, ip: object) -> bool:  # TODO ip wird mal str
        if kind in self.services:
            self.services[kind].append(ip)
            return True
        self.services[kind] = [ip]
        return True

    def get_service(self, kind: str) -> [object]:
        if kind not in self.services:
            return None  # TODO error handling
        return self.services[kind]

    def unregister_service(self, kind: str, ip: object) -> bool:
        if kind not in self.services:
            return False  # TODO error handling?
        while ip in self.services[kind]:
            self.services[kind].remove(ip)
        return True


class AccountingBillingService(object):
    """This class manages users."""

    def __init__(self):
        self.users = []
        self.invoices = []
        self.transactions = []  # für abgeschlossene Parkvorgänge

    def register_user(self, email, password):
        match = [x for x in self.users if x.email == email]
        if match:
            return False  # TODO error handling und so

        u = User(email, password)
        self.users.append(u)

    def login_user(self, email, password):
        user = [x for x in self.users if x.email == email and x.password == password]
        if not user:
            return False
        return True

    def add_transaction(self):
        # TODO
        pass

    def get_user_master_data(self, email):
        user = [x for x in self.users if x.email == email]
        if not user:
            return False  # TODO hier müssen wir uns geeignetes überlegen

        return user  # TODO vorher schon serialisieren ?

    def get_user_transaction_data(self, email):
        user = [x for x in self.users if x.email == email]
        if not user:
            return False  # TODO hier müssen wir uns geeignetes überlegen
        invoices = [x for x in self.invoices if x.user.email == email]
        transactions = [x for x in self.transactions if x.user.email == email]
        return None  # TODO wie sieht eine Transaktion aus? Wie werden die Daten zurückgegeben?


class AuthService(object):
    id = 0

    def __init__(self, svc_repo):
        self.tokens_issued = []
        # 0:0>4X bedeutet: 0. Index, fülle mit 0en auf, rechtbündig, 4 Stellen, Hexadezimal
        self.token_prefix = "{0:0>4X}".format(id)
        id += 1
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
