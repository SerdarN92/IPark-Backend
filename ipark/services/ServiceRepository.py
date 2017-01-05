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