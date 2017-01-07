import redis
import MySQLdb as mydb
import MySQLdb.cursors

r = redis.StrictRedis(host='132.252.152.57')
r.execute_command("AUTH GS~FsB3~&c7T")

# r.flushall()

# fill redis if not exist
if not r.exists('parkinglots'):
    with mydb.connect('132.252.152.57', 'root', 'GS~FsB3~&c7T', 'ipark',
                      cursorclass=mydb.cursors.DictCursor) as cur:  # type: MySQLdb.cursors.DictCursor

        cur.execute('SELECT * FROM parking_lots NATURAL LEFT JOIN parking_lot_status')

        rows = cur.fetchall()
        geoadd_command = ['GEOADD', 'parkinglots']
        for row in rows:  # type:dict
            geoadd_command.extend([str(row['longitude']), str(row['latitude']), str(row['lot_id'])])
            r.hmset('lot:' + str(row['lot_id']), row)
        r.execute_command(*geoadd_command)


def find_near_parking_lots(rds: redis.StrictRedis, lon: float, lat: float, radius: int) -> list:
    resp = rds.execute_command('GEORADIUS', 'parkinglots', lon, lat, radius, 'km')  # type: list[bytes]
    lots = [rds.hgetall('lot:' + b.decode()) for b in resp]
    return lots


lots = find_near_parking_lots(r, 51.4, 7, 6)
print(lots)
print(len(lots))
