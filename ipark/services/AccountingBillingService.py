from model.DomainClasses import User


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