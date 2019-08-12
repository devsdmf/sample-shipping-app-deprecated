# -*- coding: utf-8 -*-
from flask import Flask, request, redirect, json

import mysql.connector
from correios import Correios
from correios.package import BoxPackage
from functools import reduce

from app import config
from app.models.store_token import StoreToken, StoreTokenRepository, StoreTokenException
from app.services.tiendanube import TiendaNube, TiendaNubeException
from app.services.logger import Logger
from app.util.correios import item_to_package_item, service_to_shipping_option

from datetime import datetime, timedelta
from pytz import timezone

# initializing app instance
app = Flask(config.APP_NAME)

# initializing logger
logger = Logger(config.APP_NAME)

# initializing database connection
conn = mysql.connector.connect(
    host=config.DB_HOST, 
    user=config.DB_USER, 
    passwd=config.DB_PASS,
    database=config.DB_NAME
)
conn.ping(reconnect=True, attempts=3)

logger.info('Checking database connection... ')
if conn.is_connected():
    logger.info('Success!')
else:
    logger.error('Failed to connect to database!')
    exit()

# initializing tiendanube client
tn = TiendaNube(app_id=config.TIENDANUBE_APP_ID,app_secret=config.TIENDANUBE_APP_SECRET,api_url=config.TIENDANUBE_API_URL,authorization_url=config.TIENDANUBE_AUTHORIZATION_URL)

# default route
@app.route('/')
def hello():
    return 'Hello World!'

# installation route -> this route will be called during the authentication process (installation) of the app in a given store
@app.route('/nuvemshop/install')
def install():
    try:
        # authenticating against tiendanube api
        access_token, store_id = tn.authorize_with_code(request.args.get('code'))

        # saving store access token to database
        st = StoreToken(store_id,access_token)
        repo = StoreTokenRepository(conn)
        repo.save_token(st)

        # setting up tn instance
        tn.set_access_token(st.access_token)
        tn.set_store_id(st.store)

        # creating the shipping carrier
        carrier = tn.create_shipping_carrier(name = config.CARRIER_NAME,callback_url = config.CARRIER_CALLBACK_URL,supports = config.CARRIER_SUPPORTS)

        # creating shipping carrier options
        pac_option = tn.create_shipping_carrier_option(carrier.get('id'), code=config.OPTION_PAC_CODE, name=config.OPTION_PAC_NAME)
        sedex_option = tn.create_shipping_carrier_option(carrier.get('id'), code=config.OPTION_SEDEX_CODE, name=config.OPTION_SEDEX_NAME)
        store = tn.get_store()
        return redirect('https://' + store.get('original_domain') + '/admin/shipping')
    except StoreTokenException as e:
        logger.error('An error occurred at try to save store access token to the database. An exception with message "{}" was caught'.format(str(e)))
        return "Hello! An error occurred at try to authenticate you against Tienda Nube API. Please, contact the administrator."
    except TiendaNubeException as e:
        logger.error('An error occurred at try to setup nuvemshop application for store {}. Exception with message "{}" was caught'.format(st.store,str(e)))
        return "An error occurred at try to setup application in your store. Please, contact the administrator."

# shipping options route -> this route will be called during a purchase process (product page, cart, checkout, etc...)
@app.route('/nuvemshop/options', methods=["POST"])
def options():
    # helper function to generate a pickup option 
    def create_pickup_option_for(name, code, price, price_merchant, min_eta, max_eta):
        return {
            'name': 'Pickup Point - {}'.format(name),
            'code': code,
            'price': float(price),
            'price_merchant': float(price_merchant),
            'type': 'pickup',
            'currency': config.OPTION_CURRENCY,
            'min_delivery_date': min_eta.isoformat(timespec='seconds'),
            'max_delivery_date': max_eta.isoformat(timespec='seconds'),
            'phone_required': False,
            'id_required': False,
            'accepts_cod': True,
            'address': {
                'address': 'Sample Street',
                'number': 123,
                'floor': None,
                'locality': 'Sample District',
                'city': 'Sample City',
                'province': 'São Paulo',
                'country': 'BR',
                'zipcode': '04547130',
                'latitude': None,
                'longitude': None,
            },
            'hours': [
                {
                    'day': 1,
                    'start': '0900',
                    'end': '1800'
                },{
                    'day': 2,
                    'start': '0900',
                    'end': '1800'
                },{
                    'day': 3,
                    'start': '0900',
                    'end': '1800'
                },{
                    'day': 4,
                    'start': '0900',
                    'end': '1800'
                },{
                    'day': 5,
                    'start': '0900',
                    'end': '1800'
                }
            ],
            'availability': True,
            'reference': code
        }

    # generating mock pickup points
    tz = timezone(config.OPTION_TIMEZONE)
    now = datetime.now(tz)
    min_eta = now + timedelta(2)
    max_eta = now + timedelta(4)

    options = []
    options.append(create_pickup_option_for('#1',1,100.00,100.00,min_eta,max_eta))
    options.append(create_pickup_option_for('#2',1,100.00,100.00,min_eta,max_eta))
    options.append(create_pickup_option_for('#3',1,100.00,100.00,now + timedelta(5), now + timedelta(7)))
    options.append(create_pickup_option_for('#4',2,150.00,150.00,min_eta,max_eta))

    return json.jsonify({'rates': options})

if __name__ == '__main__':
    app.run()

