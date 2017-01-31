from communication.Service import Service
from communication.Client import Client
from model.ParkingLot import ParkingLot
from model.DomainClasses import Reservation
from AccountingBillingService import AccountingAndBillingService
import requests
from flask import json
from model.User import User


class PollingService(Service):
    def __init__(self):
        self.poller = PollingClient()
        super().__init__("Polling")

    def poll_lot(self, lot_id):
        lot = ParkingLot(lot_id)
        full_url = lot.api_path + "/events"
        response = requests.get(full_url)  # todo certificate
        if response.status_code != 200:
            return
        events = response.json()
        # [{"index":2,"startTime":77774128,"stopTime":77774375,"ID":57,"spotid":16843009}]
        for event in events:
            res_id = event["ID"]
            email = Reservation.get_email_from_resid(res_id)
            if not email:
                continue
            user = User(email, readonly=True)
            reservation = AccountingAndBillingService.get_user_reservation_for_id(user, id)
            if not reservation:
                continue

            # todo check if the reservation is running
            pass


class PollingClient(Client):
    def __init__(self):
        super().__init__("Polling")

    def poll_lot(self, lot_id):
        self.delayed_call("poll_lot", lot_id)
