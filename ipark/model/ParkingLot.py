from model.DatabaseObject import DatabaseObject
import pickle

import MySQLdb.cursors


class FullException(BaseException):
    def __init__(self):
        super(FullException, self).__init__()


class ParkingLot:
    """This class represents a geographical location in which the system manages a set of parking spots."""

    def __init__(self, lot_id=None):
        super(ParkingLot, self).__init__()

        self.lot_id = lot_id  # ID des Parkplatzes / Parkhauses (vllt UUID?)
        self.name = None
        self.total_spots = None
        self.longitude = None
        self.latitude = None
        self.tax = None
        self.max_tax = None
        self.reservation_tax = None

        if self.lot_id is not None:
            lot_data = DatabaseObject.r.hget('parkinglotsbyid', self.lot_id)
            DatabaseObject.assign_dict(self, pickle.loads(lot_data))

    def getFreeParkingSpots(self) -> int:
        assert self.lot_id is not None
        return DatabaseObject.r.scard('lot:' + str(self.lot_id) + ':freespots')

    def reserve_free_parkingspot(self) -> int:
        assert self.lot_id is not None

        spot_id = DatabaseObject.r.spop('lot:' + str(self.lot_id) + ':freespots')
        if spot_id is None:
            raise FullException()
        DatabaseObject.r.sadd('lot:' + str(self.lot_id) + ':occupiedspots', spot_id)
        return int(spot_id)

    def removeReservation(self, spot_id: int) -> bool:
        return bool(DatabaseObject.r.smove('lot:' + str(self.lot_id) + ':occupiedspots',
                                           'lot:' + str(self.lot_id) + ':freespots',
                                           str(spot_id)))

    def get_data_dict(self):
        return {k: getattr(self, k) for k in
                ['lot_id', 'name', 'total_spots', 'longitude', 'latitude', 'tax', 'max_tax', 'reservation_tax']}

    @staticmethod
    def import_parkinglots():
        r = DatabaseObject.r
        r.delete('parkinglots')

        with DatabaseObject.my.cursor() as cur:  # type: MySQLdb.cursors.DictCursor
            cur.execute('SELECT * FROM parking_lots')
            rows = cur.fetchall()

            # add lots to geo set and lot_id map
            geoadd_command = ['GEOADD', 'parkinglots']
            hmset_command = ['HMSET', 'parkinglotsbyid']
            for row in rows:  # type: dict
                geoadd_command.extend([str(row['longitude']), str(row['latitude']), pickle.dumps(row)])
                hmset_command.extend([row['lot_id'], pickle.dumps(row)])

            r.execute_command(*geoadd_command)
            r.execute_command(*hmset_command)
            print("Geodata added")

            cur.execute('SELECT spot_id, lot_id, `number` FROM parking_spots ORDER By lot_id ASC')
            while True:
                rows = cur.fetchmany(1000)
                if len(rows) < 1:
                    break

                # add all spots as free
                for row in rows:
                    r.sadd('lot:' + str(row['lot_id']) + ':freespots', row['spot_id'])
                    r.hmset('spot:' + str(row['spot_id']), {k: v for k, v in row.items() if k in ['lot_id', 'number']})

            DatabaseObject.my.commit()


class ParkingSpot:
    """This class represents a single spot to park a car on. This always belongs to exactly one ParkingLot."""

    def __init__(self, spot_id: int):
        super(ParkingSpot, self).__init__()
        self.spot_id = spot_id

        # ID, Nummer des Parkplatzes
        self.lot_id, self.number = DatabaseObject.r.hmget('spot:' + str(self.spot_id), ('lot_id', 'number'))
        assert self.lot_id is not None

    def is_busy(self):
        return not bool(DatabaseObject.r.sismember('lot:' + str(self.lot_id) + ':freespots'))
