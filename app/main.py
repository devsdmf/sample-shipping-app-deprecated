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
    # getting current request body
    req = request.get_json()

    # creating a correios package
    package = reduce(item_to_package_item,req.get('items'),BoxPackage())

    # initializing correios client
    correios = Correios()

    # getting correios rates
    result = correios.get_shipping_rates(
        origin = req.get('origin').get('postal_code'),
        destination = req.get('destination').get('postal_code'),
        package = package,
        services = [config.OPTION_PAC_SERVICE, config.OPTION_SEDEX_SERVICE]
    )

    # checking if there is any error
    if not result.has_errors():
        # parsing correios service rate to the shipping option format
        rates = list(map(lambda s: service_to_shipping_option(s), result.services))

        return json.jsonify({'rates': rates})
    else:
        for service in result.services:
            code = service.code
            error = service.error_code
            message = service.error_message
            logger.warn('The service {} returned the error {} with message: '.format(code,error,message))
        return abort(400)

if __name__ == '__main__':
    app.run()

