import code

from services.AccountingBillingService import AccountingBillingService
from services.AuthService import AuthService
from services.ServiceRepository import ServiceRepository

repo = ServiceRepository()
repo.register_service("A&B", AccountingBillingService())
repo.register_service("Auth", AuthService(repo))

code.interact(banner="This shell is used as demonstration only. \n"
                     "You have exactly one variable by now, which is repo, a ServiceRepository.\n", local=locals())
