# -*- coding: utf-8 -*-
import requests
import json
from app.services.logger import Logger

""" TiendaNube API Client """
class TiendaNube(object):
    PRODUCTION_API_URL = 'https://api.tiendanube.com/v1/'
    PRODUCTION_AUTHORIZATION_URL = 'https://www.tiendanube.com/apps/authorize/token'

    _API_URL = None
    _AUTHORIZATION_URL = None
    _APP_ID = None
    _APP_SECRET = None
    _ACCESS_TOKEN = None
    _STORE_ID = None

    _logger = None

    """
    TiendaNube Constructor.

    This is the constructor of the TiendaNube client class. To start a TiendaNube instance, you will need at least the app_id 
    and app_secret obtained in the partners admin.

    Also, you can specify a given access token and store ID to consume the API endpoints.

    The api_url and authorization_url parameters are optional, if nothing is supplied, it will use the default production values.
    """
    def __init__(self, app_id, app_secret, access_token=None, store_id=None, api_url=None, authorization_url=None):
        self._logger = Logger(self.__class__.__name__)
        self._logger.info('TiendaNube instance was initiated with app_id %s and app_secret %s' % (app_id, app_secret))
        
        # setting up api urls
        self._API_URL = (self.PRODUCTION_API_URL if api_url is None else api_url) + '{}/{}'
        self._AUTHORIZATION_URL = self.PRODUCTION_AUTHORIZATION_URL if authorization_url is None else authorization_url

        # setting up application credentials
        self._APP_ID = app_id
        self._APP_SECRET = app_secret

        # setting up client credentials
        self._ACCESS_TOKEN = access_token
        self._STORE_ID = store_id

    """ Set an access token to the current instance """
    def set_access_token(self, accessToken):
        self._ACCESS_TOKEN = accessToken

    """ Set a store ID to the current instance """
    def set_store_id(self, store_id):
        self._STORE_ID = store_id

    """
    Authorize a store with a given authorization code. This method is responsible to validate the authorization code against
    the Tienda Nube API, and also, obtain an access token and the authenticated user (store) ID, that will be used to consume
    the API endpoints later.
    """
    def authorize_with_code(self, authorization_code):
        payload = {
            'client_id': self._APP_ID,
            'client_secret': self._APP_SECRET,
            'grant_type': 'authorization_code',
            'code': authorization_code
        }

        r = requests.post(self._AUTHORIZATION_URL,data=payload)

        if r.status_code == requests.codes.ok:
            try:
                j = r.json()
                return j.get('access_token'), j.get('user_id')
            except ValueError:
                raise TiendaNubeException('Attempt to authorize code against TiendaNube API caused an unexpected error. Response got a {} status code and "{}" body'.format(r.status_code,r.text))
        else:
            raise TiendaNubeException('Attempt to authorize code against TiendaNube API caused an unexpected error. Response got a {} status code and "{}" body'.format(r.status_code,r.text))

    """
    Get the current store information
    """
    def get_store(self):
        if not self.__is_ready():
            raise TiendaNubeException("An error occurred. Current TiendaNube instance does not have any valid access token and store ID")
        r = requests.get(self.__get_url('store'), headers=self.__get_headers())
        if r.status_code == requests.codes.ok:
            return r.json()
        else:
            raise TiendaNubeException('An error occurred at try to fetch store {} information. Request got a response with {} status code and "{}" body'.format(self._STORE_ID,r.status_code,r.text))

    """
    Create a new shipping carrier in the current store through the API
    """
    def create_shipping_carrier(self, name, callback_url, supports):
        if not self.__is_ready():
            raise TiendaNubeException("An error occurred. Current TiendaNube instance does not have any valid access token and store ID")

        payload = {'name': name, 'callback_url': callback_url, 'types': ','.join(supports)}
        r = requests.post(self.__get_url('shipping_carriers'), json=payload, headers=self.__get_headers())

        if r.status_code == requests.codes.created:
            j = r.json()
            self._logger.info('A shipping carrier with id %d was created' % (j.get('id')))
            return j
        else:
            raise TiendaNubeException('An error occurre at try to create shipping carrier. Request got a response with {} code and "{}" body'.format(r.status_code,r.text))

    """
    Delete a given shipping carrier from the current store
    """
    def delete_shipping_carrier(self, carrier_id):
        if not self.__is_ready():
            raise TiendaNubeException("An error occurred. Current TiendaNube instance does not have any valid access token and store ID")

        r = requests.delete(self.__get_url('shipping_carriers/{}'.format(carrier_id)), headers=self.__get_headers())
        
        if r.status_code == requests.codes.ok:
            return True
        else:
            raise TiendaNubeException('An error occurred at try to delete shipping carrier [{}]. Request got a response with {} status code and "{}" body'.format(carrier_id,r.status_code,r.text))

    """
    Create a shipping carrier option for a given shipping carrier in the current store
    """
    def create_shipping_carrier_option(self, carrier_id, code, name, additional_days = 0, additional_cost = 0.0, allow_free_shipping = False):
        if not self.__is_ready():
            raise TiendaNubeException("An error occurred. Current TiendaNube instance does not have any valid access token and store ID")

        payload = {'code': code, 'name': name, 'additional_days': additional_days, 'additional_cost': additional_cost, 'allow_free_shipping': allow_free_shipping}
        r = requests.post(self.__get_url('shipping_carriers/{}/options'.format(carrier_id)), json=payload, headers=self.__get_headers())

        if r.status_code == requests.codes.created:
            j = r.json()
            self._logger.info('A shipping carrier option with id %d and code %s was created' % (j.get('id'), code))
            return j
        else:
            raise TiendaNubeException('An error occurred at try to create shipping carrier option. Request result in a {} status code with a "{}" body'.format(r.status_code,r.text))

    """
    Delete a given shipping carrier option from a shipping carrier in the current store
    """
    def delete_shipping_carrier_option(self, carrier_id, option_id):
        if not self.__is_ready():
            raise TiendaNubeException("An error occurred. Current TiendaNube instance does not have any valid access token and store ID")

        r = requests.delete(self.__get_url('shipping_carriers/{}/options/{}'.format(carrier_id, option_id)), headers=self.__get_headers())

        if r.status_code == requests.codes.ok:
            return True
        else:
            raise TiendaNubeException('An error occurred at try to delete shipping carrier option [{}]. Request got a response with {} status code and "{}" body'.format(option_id,r.status_code,r.text))

    """ Check if the current instance is ready to consume the API"""
    def __is_ready(self):
        return True if self._ACCESS_TOKEN is not None and self._STORE_ID is not None else False

    """ Get the default headers for every API call"""
    def __get_headers(self):
        if not self.__is_ready():
            return None
        return {'Content-Type': 'application/json', 'Authentication': 'bearer %s' % (self._ACCESS_TOKEN)}

    """ Generate the API URL that will be called in a request """
    def __get_url(self, endpoint):
        return self._API_URL.format(self._STORE_ID,endpoint)

class TiendaNubeException(Exception):
    pass

