# Builtin modules
import json
from time import time
from urllib import request
# Third party modules
from websocket import create_connection # type: ignore
# Local modules
from .main import MainModule
# Program
CURRENCIES = {
	"btc":{
		"ticker":"XXBTZUSD",
		"pair":"XBT/USD",
	},
	"eth":{
		"ticker":"XETHZUSD",
		"pair":"ETH/USD",
	},
}

class KrakenChart(MainModule):
	def __init__(self, currency:str="btc") -> None:
		if currency not in CURRENCIES:
			raise Exception("Currency {} not supported".format(currency))
		self.currency = currency
		super().__init__()
	def _fetchFirst(self) -> None:
		resCtx = request.Request(url='https://api.kraken.com/0/public/OHLC?pair={}&since={}'.format(
			CURRENCIES[self.currency]["ticker"],
			int(time()-61440),
		))
		res = json.load(request.urlopen(resCtx))
		for data in res["result"][CURRENCIES[self.currency]["ticker"]]:
			self.prices.append(float(data[1]))
		self.lastTimestamp = int(res["result"]["last"] // 60 * 60)
	def _fetchThreadLoop(self) -> None:
		ws = create_connection("wss://ws.kraken.com/")
		ws.send(json.dumps({
			"event": "subscribe",
			"pair": [
				CURRENCIES[self.currency]["pair"],
			],
			"subscription": {
				"name": "spread",
			}
			# "subscription": {
			# 	"interval": 1,
			# 	"name": "ohlc",
			# }
		}))
		while not self.closeEvent.is_set():
			rawResult =  ws.recv()
			try:
				res = json.loads(rawResult)
				with self.pricesLock:
					self.priceCaches.append(float(res[1][0]))
			except:
				continue
			"""
			{'connectionID': 15419748703498491903, 'event': 'systemStatus', 'status': 'online', 'version': '1.8.7'}
			"""
		ws.close()
