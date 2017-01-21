import re

import MySQLdb

from model.DatabaseObject import DatabaseObject, LockedException
from model.DomainClasses import Reservation, PaymentMethod

from model.User import User, NotFoundException

r = DatabaseObject.r
my = DatabaseObject.my


def redis_scan_generator(rds, match="*", regex: re._pattern_type = None):
    count = 10
    cursor = 0
    while True:
        cursor, keys = rds.scan(cursor, match, count)

        if len(keys) == 0:
            count = min(1000, count << 2)
        elif len(keys) > 3:
            count = max(10, count >> 2)

        if regex is not None:
            yield from (k.decode() for k in keys if regex.match(k.decode()))
        else:
            yield from (k.decode() for k in keys)

        if cursor == 0:
            break


def get_insert_update_statement(table: str, columns: list, data: dict) -> str:
    data = [data[k] for k in columns]
    return "INSERT INTO " + table + "(`" + ("`, `".join(columns)) + "`) " \
           + "VALUES (" + (", ".join(["%s"] * len(columns))) + ") " \
           + "ON DUPLICATE KEY UPDATE " + (", ".join(["`" + c + "` = %s" for c in columns])), data * 2


def get_update_statement(table: str, columns: list, data: dict, id_field: str, id_value) -> tuple:
    data = [data[k] for k in columns]
    return "UPDATE " + table + " SET " + (", ".join(["`" + c + "` = %s" for c in columns])) \
           + " WHERE `" + id_field + "` = %s", tuple(data) + (id_value,)


def flush_redis_to_mysql():
    # USER
    user_gen = redis_scan_generator(r, 'user:*', re.compile("^user:[^:]*$", re.IGNORECASE))

    for user_key in user_gen:  # type: str
        try:
            email = user_key.rsplit(':', 1)[1]
            print(email)
            user = User(email)

            with DatabaseObject.my.cursor() as cur:
                try:
                    print('UPDATING USER', email)
                    if cur.execute(*get_update_statement('users', User.database_fields, user.get_data_dict(),
                                                         'user_id', user.user_id)) != 1:
                        # User data unchanged or non-existent user_id
                        user._modified = 0
                        r.delete(user_key, user_key + ":locked")
                except MySQLdb.IntegrityError:
                    # unknown constraint error
                    user._modified = 0
                    r.delete(user_key, user_key + ":locked")
                DatabaseObject.my.commit()

        except NotFoundException as ex:
            print("Deleting invalid User: ", user_key)
            r.delete(user_key)
        except LockedException as ex:
            continue

    # RESERVATIONS
    reservations_gen = redis_scan_generator(r, 'user:reservations:*',
                                            re.compile("^user:reservations:[0-9]*$", re.IGNORECASE))

    for reservation_key in reservations_gen:  # type: str
        try:
            user_id = reservation_key.rsplit(':', 1)[1]
            try:
                reservations = DatabaseObject.load_and_lock_data(reservation_key,
                                                                 'select 1', None, lambda x: AssertionError())
            except:
                continue

            for res in reservations:  # type: Reservation
                print("SAVING RESERVATION", res.user_id, res.spot_id)
                with DatabaseObject.my.cursor() as cur:
                    try:
                        if cur.execute(*get_insert_update_statement('reservations', Reservation.database_fields,
                                                                    res.get_data_dict())) != 1:
                            # data unchanged or non-existent user_id
                            res._modified = 0
                    except MySQLdb.IntegrityError:
                        # unknown constraint error
                        res._modified = 0
                    DatabaseObject.my.commit()

            r.delete(reservation_key, reservation_key + ":locked")
        except LockedException as ex:
            continue

    # PAYMENT_METHODS
    payments_gen = redis_scan_generator(r, 'user:payment_methods:*',
                                        re.compile("^user:payment_methods:[0-9]*$", re.IGNORECASE))

    for payments_key in payments_gen:  # type: str
        try:
            user_id = payments_key.rsplit(':', 1)[1]
            try:
                payments = DatabaseObject.load_and_lock_data(payments_key,
                                                             'select 1', None, lambda x: AssertionError())
            except:
                continue

            for pay in payments:  # type: PaymentMethod
                print("SAVING PAYMENT_METHOD", pay.payment_provider)
                with DatabaseObject.my.cursor() as cur:
                    try:
                        if cur.execute(*get_insert_update_statement('payment_methods', PaymentMethod.database_fields,
                                                                    pay.get_data_dict())) != 1:
                            # data unchanged or non-existent user_id
                            pay._modified = 0
                    except MySQLdb.IntegrityError:
                        # unknown constraint error
                        pay._modified = 0
                    DatabaseObject.my.commit()

            r.delete(payments_key, payments_key + ":locked")
        except LockedException as ex:
            continue


if __name__ == '__main__':
    flush_redis_to_mysql()
    # print(list(k for k in r.keys() if not any(k.decode().startswith(p) for p in
    #                                          ['lot', 'spot', 'parkinglots', 'parkinglotsbyid'])))
