import pickle

from communication.Client import Client
from communication.Service import Service
from model.DatabaseObject import DatabaseObject
from model.ParkingLot import ParkingLot


class GeoService(Service):
    MAX_RESULTS_REDIS = 300
    MAX_RADIUS = 50

    def __init__(self):
        super().__init__("GeoService")

    def find_near_parking_lots(self, lon: float, lat: float, radius: int, max_results: int, lot_filter):
        radius = min(max(radius, 0), GeoService.MAX_RADIUS)
        lots = DatabaseObject.r.execute_command('GEORADIUS', 'parkinglots', str(lon), str(lat), str(radius), 'km',
                                                'COUNT', GeoService.MAX_RESULTS_REDIS)  # type: list[ParkingLot]
        lots = (DatabaseObject.assign_dict(ParkingLot(), pickle.loads(l)) for l in lots)
        lots = (l for l in lots if lot_filter(l))

        lots = sorted(lots, key=lambda x: sum(x.get_free_parking_spots().values()),
                          reverse=True)[0:max_results]  # type: ParkingLot

        return lots

    def get_lot(self, lot_id):
        try:
            return ParkingLot(lot_id)
        except:
            return None


class GeoClient(Client):
    MAX_RESULTS = 50

    def __init__(self):
        super().__init__("GeoService")

    def find_near_parking_lots(self, lon, lat, radius, max_results: int = None, lot_filter=lambda lot: True):
        if max_results is None or max_results < 0:
            max_results = GeoClient.MAX_RESULTS
        return self.call("find_near_parking_lots", lon, lat, radius, max_results, lot_filter)

    def get_lot(self, lot_id):
        return self.call("get_lot", lot_id)
