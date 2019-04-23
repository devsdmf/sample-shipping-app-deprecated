# -*- coding: utf-8 -*-
from dotenv import load_dotenv
import os

# loading dot file
load_dotenv()

# general app information
APP_NAME = 'sample-shipping-app'

# database settings
DB_HOST = os.getenv('DB_HOST','localhost')
DB_USER = os.getenv('DB_USER','root')
DB_PASS = os.getenv('DB_PASS')
DB_NAME = os.getenv('DB_NAME','sample_shipping_app')

# tiendanube api settings
TIENDANUBE_API_URL = os.getenv('TIENDANUBE_API_URL')
TIENDANUBE_AUTHORIZATION_URL = os.getenv('TIENDANUBE_AUTHORIZATION_URL')
TIENDANUBE_APP_ID = os.getenv('TIENDANUBE_APP_ID')
TIENDANUBE_APP_SECRET = os.getenv('TIENDANUBE_APP_SECRET')

# shipping carrier settings
CARRIER_NAME = 'Correios'
CARRIER_CALLBACK_URL = os.getenv('SERVICE_URL','http://localhost:5000') + '/nuvemshop/options'
CARRIER_SUPPORTS = ['ship','pickup']

OPTION_PAC_CODE = 'pac'
OPTION_PAC_NAME = 'PAC'
OPTION_PAC_SERVICE = '04510'

OPTION_SEDEX_CODE = 'sedex'
OPTION_SEDEX_NAME = 'Sedex'
OPTION_SEDEX_SERVICE = '04014'

# shipping option settings
OPTION_CURRENCY = 'BRL'
OPTION_TYPE = 'ship'
OPTION_TIMEZONE = 'America/Sao_Paulo'

