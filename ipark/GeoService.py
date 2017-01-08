from communication.Service import Service
from communication.Client import Client
from model.DatabaseObject import DatabaseObject
import pickle

from model.ParkingLot import ParkingLot


class GeoService(Service):
    def __init__(self):
        super().__init__("GeoService")

    def find_near_parking_lots(self, lon: float, lat: float, radius: int):
        lots = DatabaseObject.r.execute_command('GEORADIUS', 'parkinglots', str(lon), str(lat), str(radius), 'km')
        return [DatabaseObject.assign_dict(ParkingLot(), pickle.loads(l)) for l in lots]


class GeoClient(Client):
    def __init__(self):
        super().__init__("GeoService")

    def find_near_parking_lots(self, lon, lat, radius):
        return self.call("find_near_parking_lots", lon, lat, radius)
