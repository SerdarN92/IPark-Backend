import redis
import MySQLdb as mydb
import MySQLdb.cursors
import pickle

r = redis.StrictRedis(host='132.252.152.57')
r.execute_command("AUTH GS~FsB3~&c7T")

# r.flushall()
# r.delete('parkinglots')

# fill redis if not exist
if not r.exists('parkinglots'):
    with mydb.connect('132.252.152.57', 'root', 'GS~FsB3~&c7T', 'ipark',
                      cursorclass=mydb.cursors.DictCursor) as cur:  # type: MySQLdb.cursors.DictCursor

        cur.execute('SELECT * FROM parking_lots')
        rows = cur.fetchall()

        geoadd_command = ['GEOADD', 'parkinglots']
        for row in rows:  # type: dict
            geoadd_command.extend([str(row['longitude']), str(row['latitude']), pickle.dumps(row)])
        r.execute_command(*geoadd_command)


def find_near_parking_lots(rds: redis.StrictRedis, lon: float, lat: float, radius: int) -> list:
    lots = r.execute_command('GEORADIUS', 'parkinglots', str(lon), str(lat), str(radius), 'km')
    return [pickle.loads(l) for l in lots]


lots = find_near_parking_lots(r, 51.4, 7.03, 6)
print(lots)
print(len(lots))
