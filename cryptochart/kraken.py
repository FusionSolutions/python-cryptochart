# Builtin modules
import json
from time import time
from urllib import request
from threading import Thread, Event
from typing import Any
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
	thr:Thread
	closeEvent:Event
	def __init__(self, currency:str="btc") -> None:
		if currency not in CURRENCIES:
			raise Exception("Currency {} not supported".format(currency))
		self.currency   = currency
		self.closeEvent = Event()
		super().__init__()
	def _fetchHistory(self) -> None:
		resCtx = request.Request(url='https://api.kraken.com/0/public/OHLC?pair={}&since={}'.format(
			CURRENCIES[self.currency]["ticker"],
			int(time()-61440),
		))
		res = json.load(request.urlopen(resCtx))
		for data in res["result"][CURRENCIES[self.currency]["ticker"]]:
			self.prices.append(float(data[1]))
		self.lastTimestamp = int(res["result"]["last"] // 60 * 60)
	def _fetchThreadLoop(self) -> None:
		ws:Any = None
		while not self.closeEvent.is_set():
			if ws is None:
				ws = create_connection("wss://ws.kraken.com/")
				ws.send(json.dumps({
					"event": "subscribe",
					"pair": [
						CURRENCIES[self.currency]["pair"],
					],
					"subscription": {
						"name": "spread",
					}
				}))
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
			if self.tickerCounter%15 == 0:
				ws = None
		ws.close()
	def _start(self) -> None:
		self._fetchHistory()
		self.thr = Thread(target=self._fetchThreadLoop, daemon=True)
		self.thr.start()
	def _close(self) -> None:
		self.closeEvent.set()
		self.thr.join(5)
