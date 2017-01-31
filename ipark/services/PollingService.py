import requests

from communication.Client import Client
from communication.Service import Service
from model.DomainClasses import Reservation
from model.ParkingLot import ParkingLot
from model.User import User
from services.AccountingBillingService import AccountingAndBillingService, AccountingAndBillingClient


class PollingService(Service):
    def __init__(self):
        self.poller = PollingClient()
        self.accounting = AccountingAndBillingClient()
        super().__init__("Polling")

    def poll_lot(self, lot_id):
        lot = ParkingLot(lot_id)
        response = requests.get(lot.api_path + "/events")  # todo certificate
        if response.status_code != 200:
            return  # todo Exception?
        try:
            events = response.json()
        except ValueError:
            return {"status": False, "message": "IoT Error"}  # todo discuss: müssen wir hier antworten? ne oder?
        ids = []
        # [{"index":2,"startTime":77774128,"stopTime":77774375,"ID":57,"spotid":16843009}]
        for event in events:
            res_id = event["ID"]
            if res_id in ids:
                continue  # Duplikat
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
        self.poller.delayed_poll_lot(lot_id)


class PollingClient(Client):
    def __init__(self):
        super().__init__("Polling")

    def poll_lot(self, lot_id):
        self.call("poll_lot", lot_id)

    def delayed_poll_lot(self, lot_id):
        self.delayed_call("poll_lot", lot_id)
