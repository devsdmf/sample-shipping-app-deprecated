# -*- coding: utf-8 -*-
from mysql.connector.connection import MySQLConnection
from mysql.connector import Error

""" StoreToken Aggregate """
class StoreToken(object):

    store = None
    access_token = None

    def __init__(self, store, access_token):
        self.store = store
        self.access_token = access_token

    def is_valid(self):
        return True if self.store is not None and self.access_token is not None else False

""" StoreTokenRepository """
class StoreTokenRepository(object):

    __conn = None

    def __init__(self, connection):
        if isinstance(connection, MySQLConnection):
            self.__conn = connection
            self.__conn.ping(reconnect=True, attempts=3)
        else:
            raise StoreTokenException('Attempting to create store token instance without a database cursor')

    """ Save a given StoreToken object into the database """
    def save_token(self, store_token):
        if not isinstance(store_token, StoreToken) or not store_token.is_valid():
            raise StoreTokenException('An error occurred at trying to save store token, storeToken parameter is not a valid instance of storeToken')

        try:
            cursor = self.__conn.cursor()
            cursor.execute("INSERT INTO `stores` (`store_id`,`access_token`) VALUES (%s, %s)", (str(store_token.store), store_token.access_token))
            self.__conn.commit()

            if cursor.rowcount > 0:
                return True
            else:
                raise StoreTokenException('An error occurred at try to save access token for store {} in database. No exception was raised by mysql library'.format(store_token.store))
        except Error as e:
            raise StoreTokenException('An error occurred at try to save access token for store {} in database. An exception with message "{}" was caught'.format(store_token.store,e))

    """ Get the StoreToken of a given store from the database """
    def get_token(self, store_id):
        if store_id is None:
            raise StoreTokenException('An error occurred at try to get access token for store, store parameter is None')
        
        try:
            cursor = self.__conn.cursor()
            cursor.execute("SELECT `store_id`, `access_token` FROM `stores` WHERE `store_id`=%s ORDER BY `id` DESC", (str(store_id)))

            if cursor.rowcount > 0:
                (store, access_token) = cursor.fetchone()
                return StoreToken(store,access_token)
            else:
                return False
        except Error as e:
            raise StoreTokenException('An error occurred at try to get access token for store {} from database. An exception with message "{}" was caught'.format(store_id,e))

class StoreTokenException(Exception):
    pass

