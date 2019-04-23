# TiendaNube Sample Shipping App

Welcome, aboard! This is the TiendaNube's sample shipping application implementation using TiendaNube API's shipping features.

This project is made with Python 3.3+, but the examples demonstrated here are almost the same as in any other programming language.

## Requirements

- Python 3.3+
- MySQL Server
- A valid TiendaNube application

## Installation

First of all, you must clone this project into your own computer / server:
```
$ git clone git@github.com:TiendaNube/sample-shipping-app.git
$ cd sample-shipping-app
```

After cloning, we highly recommend you to setup a virtualenv:
```
$ python3 -m venv .venv
$ source .venv/bin/activate
```

Now, you should install the application dependencies and create your own environment file, using the following commands:
```
$ pip install -r requirements.txt
$ cp .env.sample .env && vim .env
```

After installing the application dependencies, you must setup your database with the [SQL file](resources/db.sql) provided in this repo.

## Usage

After completing the setup guide, you should be able to run the application in your environment, using the following command:
```
$ GUNICORN_CMD_ARGS="--workers=1" gunicorn run:app
```

## Explanation

This app is a webapp made with Flask's Python framework, and it provides two entry points:

### App Installation

This [route](https://github.com/TiendaNube/sample-shipping-app/blob/master/app/main.py#L46) is mainly responsible to get the authorization code supplied during the authentication (installation) process against a TiendaNube store. This route gets the authorization code (aka `code`) from the URL's query string, and then, call the TiendaNube client that will validate this code against the API and as a result of this validation, will obtain the authenticated store's ID (aka `user_id`) and its `access_token`, that will be used to consume the API from this point.

### Shipping Options

This [route](https://github.com/TiendaNube/sample-shipping-app/blob/master/app/main.py#L77) is mainly responsible to return shipping rates to a TiendaNube store during the purchase process (product page, cart, checkout, etc). This route get from the JSON body the information about the cart, like the store's ID, the products in the cart, the origin and destination addresses, and so on. With this information, the application will consume the Correios web-service to retrieve the available shipping rates. Right after obtain the shipping rates, it will convert the correios rates format to the Shipping Option format expected by the TiendaNube API. 

