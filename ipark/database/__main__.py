import redis
import MySQLdb as mydb
import MySQLdb.cursors
import pickle

r = redis.StrictRedis(host='132.252.152.57')
r.execute_command("AUTH GS~FsB3~&c7T")


# r.flushall()
# r.delete('parkinglots')

# fill redis if not exist



def find_near_parking_lots(rds: redis.StrictRedis, lon: float, lat: float, radius: int) -> list:
    lots = r.execute_command('GEORADIUS', 'parkinglots', str(lon), str(lat), str(radius), 'km')
    return [pickle.loads(l) for l in lots]


lots = find_near_parking_lots(r, 51.4, 7.03, 6)
print(lots)
print(len(lots))
