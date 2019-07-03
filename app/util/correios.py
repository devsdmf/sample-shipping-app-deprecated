# -*- coding: utf-8 -*-
from correios import Correios
from app import config
from datetime import datetime, timedelta
from pytz import timezone

# map from service code to label
service_code_to_label = {}
service_code_to_label[config.OPTION_PAC_SERVICE] = config.OPTION_PAC_NAME
service_code_to_label[config.OPTION_SEDEX_SERVICE] = config.OPTION_SEDEX_NAME

# map from service code to code
service_code_to_code = {}
service_code_to_code[config.OPTION_PAC_SERVICE] = config.OPTION_PAC_CODE
service_code_to_code[config.OPTION_SEDEX_SERVICE] = config.OPTION_SEDEX_CODE

# reduce a request item to a package item
def item_to_package_item(package, item):
    dimensions = item.get('dimensions')
    quantity = item.get('quantity')
    for n in range(quantity):
        package.add_item(float(dimensions.get('height')),float(dimensions.get('width')),float(dimensions.get('depth')), int(item.get('grams')) / 1000)
    return package

# convert a correios result service to the shipping option format
def rate_to_shipping_option(rates, free_shipping_cart = False):
    merchant_rate, consumer_rate = rates
    print('PRICE MERCHANT => {}'.format(merchant_rate.price))
    print('PRICE CONSUMER => {}'.format(consumer_rate.price))
    name = 'CorreiosApp - {}'.format(service_code_to_label.get(merchant_rate.code, 'Unknown Option'))
    code = service_code_to_code.get(merchant_rate.code,'unknown')
    tz = timezone(config.OPTION_TIMEZONE)
    eta = datetime.now(tz) + timedelta(merchant_rate.days)
    return {
        'name': name,
        'code': code,
        'price': float(consumer_rate.price) if not free_shipping_cart else 0.0,
        'price_merchant': float(merchant_rate.price),
        'type': config.OPTION_TYPE,
        'currency': config.OPTION_CURRENCY,
        'min_delivery_date': eta.isoformat(timespec='seconds'),
        'max_delivery_date': eta.isoformat(timespec='seconds')
    }

