from communication.Service import Service
from communication.Client import Client
from model.DatabaseObject import DatabaseObject
import pickle

from model.ParkingLot import ParkingLot


class GeoService(Service):
    MAX_RESULT_COUNT = 300

    def __init__(self):
        super().__init__("GeoService")

    def find_near_parking_lots(self, lon: float, lat: float, radius: int, max_results: int):
        lots = DatabaseObject.r.execute_command('GEORADIUS', 'parkinglots', str(lon), str(lat), str(radius), 'km',
                                                'COUNT', GeoService.MAX_RESULT_COUNT)  # type: list[ParkingLot]
        lots = [DatabaseObject.assign_dict(ParkingLot(), pickle.loads(l)) for l in lots]

        if len(lots) > max_results:
            lots = sorted(lots, key=lambda x: x.getFreeParkingSpots(), reverse=True)[0:max_results]  # type: ParkingLot

        return lots


class GeoClient(Client):
    def __init__(self):
        super().__init__("GeoService")

    def find_near_parking_lots(self, lon, lat, radius, max_results: int = 30):
        return self.call("find_near_parking_lots", lon, lat, radius, max_results)
