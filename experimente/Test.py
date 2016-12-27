from Services import ServiceRepository, AccountingBillingService, AuthService
import code
repo = ServiceRepository()
repo.register_service("A&B", AccountingBillingService())
repo.register_service("Auth", AuthService())

code.interact(banner="This shell is used as demonstration only. \n"
                     "You have exactly one variable by now, which is repo, a ServiceRepository.\n", local=locals())
