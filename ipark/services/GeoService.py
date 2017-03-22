import pickle

from communication.Client import Client
from communication.Service import Service
from model.DatabaseObject import DatabaseObject
from model.ParkingLot import ParkingLot

"""Service for Geo Data"""

class GeoService(Service):
    """Service for Geo Data"""
    MAX_RESULTS_REDIS = 300
    MAX_RADIUS = 50

    def __init__(self):
        super().__init__("GeoService")

    @staticmethod
    def lot_filter(lot: ParkingLot, lot_type: int) -> bool:
        """check if Lot has free spots of type"""
        if lot_type is None:
            return True
        return lot.get_free_parking_spots().get(lot_type, 0) > 0

    def find_near_parking_lots(self, lon: float, lat: float, radius: int, max_results: int, lot_type: int):
        """find nearby parking lot"""
        radius = min(max(radius, 0), GeoService.MAX_RADIUS)
        lots = DatabaseObject.r.execute_command('GEORADIUS', 'parkinglots', str(lon), str(lat), str(radius), 'km',
                                                'COUNT', GeoService.MAX_RESULTS_REDIS)  # type: list[ParkingLot]
        lots = (DatabaseObject.assign_dict(ParkingLot(), pickle.loads(l)) for l in lots)
        lots = (l for l in lots if self.lot_filter(l, lot_type))

        lots = sorted(lots, key=lambda x: sum(x.get_free_parking_spots().values()),
                      reverse=True)[0:max_results]  # type: ParkingLot

        return lots

    def get_lot(self, lot_id):
        """Get Lot by ID"""
        try:
            return ParkingLot(lot_id)
        except:
            return None


class GeoClient(Client):
    MAX_RESULTS = 50

    """Client for Geo Data Service"""

    def __init__(self):
        super().__init__("GeoService")

    def find_near_parking_lots(self, lon, lat, radius, max_results: int = None, lot_type=None):
        if max_results is None or max_results < 0:
            max_results = GeoClient.MAX_RESULTS
        return self.call("find_near_parking_lots", lon, lat, radius, max_results, lot_type)

    def get_lot(self, lot_id):
        return self.call("get_lot", lot_id)
