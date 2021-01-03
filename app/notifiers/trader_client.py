"""Notify another app via webhook
"""

import structlog
import requests
import time
import hmac
import hashlib
import json

from notifiers.utils import NotifierUtils

class TraderNotifier(NotifierUtils):
    """Class for handling webhook notifications
    """

    def __init__(self, exchange, key, secret):
        self.logger = structlog.get_logger()
        self.exchange = exchange
        self.key = key
        self.secret = secret


    def notify(self, message):
        """Trade on exchange.

        Args:
            message (str): hot for buy, cold for sell.
        """
        direction=message.split()[0]
        market=message.split()[1]

        if direction == "hot":
            getattr(self, self.exchange)('BUY', market)
        elif direction == "cold":
            currency = market.split('/')[1]
            getattr(self, self.exchange)('SELL', market)


    def create_bittrex_signature(self, epoch_time, url, method, payload):
        payload_hash = hashlib.sha512(payload.encode('utf-8')).hexdigest()
        presign = epoch_time + url + method + payload_hash
        signature = hmac.new(bytes(self.secret, 'UTF-8'),
                             presign.encode(),
                             hashlib.sha512).hexdigest()
        return payload_hash, signature


    def get_bittrex_balance(self, epoch_time, currency):
        url = "https://api.bittrex.com/v3/balances/" + currency
        payload = "{}"
        payload_hash, signature = self.create_bittrex_signature(epoch_time, url, 'GET', payload)
        headers = {
            'Api-Key': self.key,
            'Api-Timestamp': epoch_time ,
            'Api-Content-Hash': payload_hash,
            'Api-Signature': signature
        }
        response = requests.request("GET", url, headers=headers, data=payload)
        return json.loads(response.content)["available"]


    def get_bittrex_rate(self, epoch_time, market):
        url = "https://api.bittrex.com/v3/markets/" + market + "/ticker"
        payload = "{}"
        payload_hash, signature = self.create_bittrex_signature(epoch_time, url, 'GET', payload)
        headers = {
            'Api-Key': self.key,
            'Api-Timestamp': epoch_time ,
            'Api-Content-Hash': payload_hash,
            'Api-Signature': signature
        }
        response = requests.request("GET", url, headers=headers, data=payload)
        return json.loads(response.content)["lastTradeRate"]


    def order_bittrex(self, epoch_time, direction, currency, quantity):
        url = "https://api.bittrex.com/v3/orders"
        payload=("{\"marketSymbol\": \"" + self.market + "\"," +
                 "\"direction\": \"" + direction + "\"," +
                 "\"type\": \"MARKET\"," +
                 "\"quantity\": " + quantity + "\"," +
                 "\"timeInForce\": \"GOOD_TIL_CANCELLED\"}")
        payload_hash, signature = self.create_bittrex_signature(epoch_time, url, 'POST', payload)
        headers = {
            'Api-Key': self.key,
            'Api-Timestamp': epoch_time ,
            'Api-Content-Hash': payload_hash,
            'Api-Signature': signature,
            'Content-Type': 'application/json'
        }
        print(payload)
        response = requests.request("POST", url, headers=headers, data=payload)
        return json.loads(response.content)


    def bittrex(self, direction, market):
        self.market = market.replace('/', '-')
        prim_currency = market.split('/')[0]
        sec_currency = market.split('/')[1]
        epoch_time = str(int(time.time()*1000))
        prim_balance = self.get_bittrex_balance(epoch_time, prim_currency)  # eth
        sec_balance = self.get_bittrex_balance(epoch_time, sec_currency)    # usdt

        if direction == "SELL":
            order = self.order_bittrex(epoch_time, direction, prim_currency, prim_balance)
            print(order)
        elif direction == "BUY":
            rate = self.get_bittrex_rate(epoch_time, self.market)
            quantity = str(int(float(sec_balance)/float(rate)*10000)/10000)     # calculate 4 decimals
            print(quantity)
            order = self.order_bittrex(epoch_time, direction, prim_currency, quantity)
            print(order)


