import sys
from .kraken import KrakenChart
inputs = list(sys.argv)
inputs.pop(0)
currency = "btc"
if inputs:
	currency = inputs.pop(0).lower() or "btc"
KrakenChart(currency).start()