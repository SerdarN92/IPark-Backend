from communication.Service import Service
from communication.Client import Client
from model.ParkingLot import ParkingLot
import requests
from flask import json


class PollingService(Service):
    def __init__(self):
        self.poller = PollingClient()
        super().__init__("Polling")

    def poll_lot(self, lot_id):
        lot = ParkingLot(lot_id)
        full_url = lot.api_path + "/events"
        response = requests.get(full_url)
        json_to_parse = response.content.decode().split('\r\n\r\n', 1)[1]
        events = json.loads(json_to_parse)
        # [{"index":2,"startTime":77774128,"stopTime":77774375,"ID":57,"spotid":16843009}]
        for event in events:
            # todo fetch reservation
            # todo fetch user
            # todo check if the reservation is running
            pass


class PollingClient(Client):
    def __init__(self):
        super().__init__("Polling")

    def poll_lot(self, lot_id):
        self.delayed_call("poll_lot", lot_id)
