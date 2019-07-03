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
from app.util.correios import item_to_package_item, rate_to_shipping_option

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
        logger.info('Successfully authenticated against Tiendanube API, the store ID is {} and the access token is {}'.format(store_id,access_token))

        # saving store access token to database
        st = StoreToken(store_id,access_token)
        repo = StoreTokenRepository(conn)
        repo.save_token(st)
        logger.info('Successfully persisted store_id and access token to the database')

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
    logger.info("Options got requested with the following body")
    logger.info(request.get_data(as_text=True))
    req = request.get_json()

    # initializing correios client
    correios = Correios()
    available_services = [config.OPTION_PAC_SERVICE, config.OPTION_SEDEX_SERVICE]

    # getting cart specs for shipping costs calculation
    origin = req.get('origin').get('postal_code')
    destination = req.get('destination').get('postal_code')
    items = req.get('items')

    # getting base shipping costs
    # creating a correios package
    package = reduce(item_to_package_item,items,BoxPackage())
    logger.info('CORREIOS PACKAGE')
    logger.info(package.api_format())

    # requesting rates from webservice
    rates = correios.get_shipping_rates(origin=origin, destination=destination, package=package, services=available_services)

    # checking for errors
    if rates.has_errors():
        # logging errors and returning result early
        for service in rates.services:
            code = service.code
            error = service.error_code
            message = service.error_message
            logger.warn('The service {} returned the error {} with message: {}'.format(code,error,message))
        return abort(400)

    # checking for free shipping items in cart
    free_shipping_items_qty = reduce(lambda c, i: c + 1 if i.get('free_shipping') else 0, items, 0)
    free_shipping_cart = free_shipping_items_qty == len(items)

    if free_shipping_items_qty > 0 and not free_shipping_cart:
        # performing another shipping costs calculation in order to get the consumer prices
        non_free_shipping_items = [item for item in items if item.get('free_shipping') is not True]
        non_free_shipping_package = reduce(item_to_package_item,non_free_shipping_items,BoxPackage())

        # requesting rates from webservice
        non_free_shipping_rates = correios.get_shipping_rates(
            origin=origin,
            destination=destination,
            package=non_free_shipping_package,
            services=available_services
        )

        if non_free_shipping_rates.has_errors():
            for service in non_free_shipping_rates.services:
                code = service.code
                error = service.error_code
                message = service.error_message
                logger.warn('The service {} returned the error {} with message: {}'.format(code,error,message))
            non_free_shipping_rates = rates
    else:
        non_free_shipping_rates = rates

    # parsing service rates to the shipping option format
    options = list(map(lambda s: rate_to_shipping_option(s, free_shipping_cart), zip(rates.services,non_free_shipping_rates.services)))

    return json.jsonify({'rates': options})

if __name__ == '__main__':
    app.run()

