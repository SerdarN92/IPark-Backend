import pickle

import MySQLdb.cursors

from model.DatabaseObject import DatabaseObject

"""Object Representation of a Parking Lot"""

class FullException(BaseException):
    """Exception if full Parking Lot is requested for reservation"""
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
        self.information = None
        self.flags = None
        self.api_path = None
        self.api_password = None

        self._free_spots = None

        if self.lot_id is not None:
            lot_data = DatabaseObject.r.hget('parkinglotsbyid', self.lot_id)
            DatabaseObject.assign_dict(self, pickle.loads(lot_data))

    def get_free_parking_spots(self) -> dict:
        """get free parking spots grouped by type"""
        assert self.lot_id is not None
        if self._free_spots is None:
            types = (int(t) for t in DatabaseObject.r.smembers('lot:' + str(self.lot_id) + ':spottypes'))
            self._free_spots = {t: DatabaseObject.r.scard('lot:' + str(self.lot_id) + ':freespots:' + str(t))
                                for t in types}  # type: dict
        return self._free_spots

    def reserve_free_parkingspot(self, spottype: int = 0) -> int:
        """reserve random free parking spot of a specific Parking Lot"""
        assert self.lot_id is not None

        spot_id = DatabaseObject.r.spop('lot:' + str(self.lot_id) + ':freespots:' + str(spottype))
        if spot_id is None:
            raise FullException()
        DatabaseObject.r.sadd('lot:' + str(self.lot_id) + ':occupiedspots:' + str(spottype), spot_id)
        return int(spot_id)

    def removeReservation(self, spot_id: int) -> bool:
        """cancel Reservation"""
        spot = ParkingSpot(spot_id)
        return bool(DatabaseObject.r.smove(b'lot:' + str(self.lot_id).encode() + b':occupiedspots:' + spot.flags,
                                           b'lot:' + str(self.lot_id).encode() + b':freespots:' + spot.flags,
                                           str(spot_id)))

    def get_data_dict(self):
        """get raw representation of object"""
        data = {k: getattr(self, k) for k in
                ['lot_id', 'name', 'total_spots', 'longitude', 'latitude',
                 'tax', 'max_tax', 'reservation_tax',
                 'information', 'flags']}
        if self.get_free_parking_spots():
            data['free_spots'] = [self.get_free_parking_spots().get(x, 0)
                                  for x in range(max(self.get_free_parking_spots()) + 1)]
        return data

    @staticmethod
    def import_parkinglots():
        """initialize static parking lot data in redis"""
        r = DatabaseObject.r
        r.delete('parkinglots')

        with DatabaseObject.my.cursor() as cur:  # type: MySQLdb.cursors.DictCursor
            from services.PollingService import PollingClient
            pollclient = PollingClient()

            cur.execute('SELECT * FROM parking_lots UNION SELECT * FROM parking_lots_dummy')
            rows = cur.fetchall()

            # add lots to geo set and lot_id map
            geoadd_command = ['GEOADD', 'parkinglots']
            hmset_command = ['HMSET', 'parkinglotsbyid']
            for row in rows:  # type: dict
                geoadd_command.extend([str(row['longitude']), str(row['latitude']), pickle.dumps(row)])
                hmset_command.extend([row['lot_id'], pickle.dumps(row)])

                if row['total_spots'] > 0:  # and row['api_path'] is not None:
                    pollclient.delayed_poll_lot(row['lot_id'])

            r.execute_command(*geoadd_command)
            r.execute_command(*hmset_command)
            print("Geodata added")

            cur.execute('SELECT spot_id, lot_id, `number`, flags, coap_ip FROM parking_spots ORDER BY lot_id ASC')
            while True:
                rows = cur.fetchmany(1000)
                if len(rows) < 1:
                    break

                # spot types per lot
                lot_types = {}  # type: dict(set)

                # add all spots as free
                for row in rows:
                    if int(row['lot_id']) not in lot_types:
                        lot_types[int(row['lot_id'])] = set()
                    lot_types[int(row['lot_id'])].add(int(row['flags']))

                    r.sadd('lot:' + str(row['lot_id']) + ':freespots:' + str(row['flags']), row['spot_id'])
                    r.hmset('spot:' + str(row['spot_id']), {k: v for k, v in row.items() if k
                                                            in ['lot_id', 'number', 'flags', 'coap_ip']})

                for l, t in lot_types.items():
                    r.sadd('lot:' + str(l) + ':spottypes', *t)

            DatabaseObject.my.commit()


class ParkingSpot:
    """This class represents a single spot to park a car on. This always belongs to exactly one ParkingLot."""

    def __init__(self, spot_id: int):
        super(ParkingSpot, self).__init__()
        self.spot_id = spot_id

        # ID, Nummer des Parkplatzes
        self.lot_id, self.number, self.flags, self.coap_ip \
            = DatabaseObject.r.hmget('spot:' + str(self.spot_id), ('lot_id', 'number', 'flags', 'coap_ip'))
        assert self.lot_id is not None
        assert self.flags is not None

    def is_busy(self):
        """get busy state of parking spot"""
        return not bool(DatabaseObject.r.sismember('lot:' + str(self.lot_id) + ':freespots:' + str(self.flags)))
