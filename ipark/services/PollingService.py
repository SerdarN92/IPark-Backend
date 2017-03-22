import requests

from communication.Client import Client
from communication.Service import Service
from model.DomainClasses import Reservation
from model.ParkingLot import ParkingLot
from model.User import User
from services.AccountingBillingService import AccountingAndBillingService, AccountingAndBillingClient

"""Service for polling data from IoT Gateway (deprecated)"""

class PollingService(Service):
    def __init__(self):
        self.poller = PollingClient()
        self.accounting = AccountingAndBillingClient()
        super().__init__("Polling")

    def poll_lot(self, lot_id):
        lot = ParkingLot(lot_id)
        if lot.api_path is None:
            return

        try:
            response = requests.get(lot.api_path + "/events", cert='assets/alice2.pem', verify=False)  # todo verify
            if response.status_code != 200:
                return  # todo Exception?

            try:
                events = response.json()
            except ValueError:
                return {"status": False, "message": "IoT Error"}  # todo discuss: müssen wir hier antworten? ne oder?
            ids = []
            for event in events:
                res_id = event["ID"]
                if res_id in ids:
                    continue  # Duplikat
                self.accounting.end_parking(event)
                ids.append(res_id)
                email = Reservation.get_email_from_resid(res_id)
                if not email:
                    continue  # todo ?
                user = User(email, readonly=True)
                reservation = AccountingAndBillingService.get_user_reservation_for_id(user, res_id)
                if not reservation or reservation.parking_end is not None:
                    continue  # keine oder beendete Reservierung
                duration = event["stopTime"] - event["startTime"]
                self.accounting.end_parking(res_id, duration)
        finally:
            self.poller.delayed_poll_lot(lot_id)


class PollingClient(Client):
    def __init__(self):
        super().__init__("Polling")

    def poll_lot(self, lot_id):
        self.call("poll_lot", lot_id)

    def delayed_poll_lot(self, lot_id, delay=120000):
        self.delayed_call("poll_lot", delay, lot_id)
