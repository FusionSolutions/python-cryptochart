# Builtin modules
import curses
from time import sleep, time
from typing import Dict, List, Any, TYPE_CHECKING
from threading import Lock
from dataclasses import dataclass
# Third party modules
# Local modules
from .chart import COLORS, writeChart
# Program
@dataclass
class YX:
	y:int
	x:int
	
class TickerDiff:
	val:float
	perc:float
	color:str
	sign:str
	def __init__(self, currVal:float, prevVal:float) -> None:
		self.val = abs(currVal - prevVal)
		self.perc = abs((1-currVal / prevVal) * 100)
		self.color = "GREEN" if currVal > prevVal else "RED"
		self.sign = "+" if currVal >= prevVal else "-"
	if TYPE_CHECKING:
		__dict__:Dict[str, Any] = {}
	else:
		@property
		def __dict__(self) -> Dict[str, Any]:
			return {
				"val":self.val,
				"perc":self.perc,
				"color":self.color,
				"sign":self.sign,
			}

class MainModule:
	prices:List[float]
	priceCaches:List[float]
	lastTimestamp:float
	tickerCounter:int
	pricesLock:Lock
	terminalSize:YX
	screen:Any
	currency:str
	def __init__(self, currency:str="btc") -> None:
		self.terminalSize  = YX(0, 0)
		self.pricesLock    = Lock()
		self.lastTimestamp = 0
		self.tickerCounter = 0
		self.prices        = []
		self.priceCaches   = []
	def _write(self, text:str, color:str="WHITE") -> None:
		self.screen.addstr(text, curses.color_pair(COLORS[color]))
	def _writeN(self, text:str, length:int, color:str="WHITE") -> None:
		self.screen.addnstr(text, length, curses.color_pair(COLORS[color]))
	def _fetchHistory(self) -> None: ...
	def _fetchThreadLoop(self) -> None: ...
	def _start(self) -> None: ...
	def _close(self) -> None: ...
	def _loop(self, screen:Any) -> None:
		try:
			try:
				curses.use_default_colors()
				for i in range(curses.COLORS):
					curses.init_pair(i+1, i, -1)
				screen.attron( curses.color_pair(COLORS["WHITE"]) )
				curses.curs_set(0)
			except:
				pass
			screen.timeout(0)
			screen.clear()
			screen.addstr("Loading prices...")
			screen.refresh()
			self.screen = screen
			doRefresh = False
			lastData = 0.0, 0
			lastTS = 0
			while True:
				sleep(0.1)
				c = self.screen.getch()
				if c == ord('q'):
					break
				doRefresh = False
				tmpTerminalSize = YX(*screen.getmaxyx())
				if tmpTerminalSize != self.terminalSize:
					self.terminalSize = tmpTerminalSize
					doRefresh = True
				if self.terminalSize.x <= 30 or self.terminalSize.y <= 15:
					screen.clear()
					self._writeN("No place to print", 17, "RED")
					screen.refresh()
					continue
				with self.pricesLock:
					if time()-self.lastTimestamp > 60:
						if self.tickerCounter%5 == 0:
							self.prices.clear()
							self._fetchHistory()
							self.prices.append(self.prices[-1])
						else:
							if not self.priceCaches:
								self.prices.append(self.prices[-1])
							else:
								self.prices.append(sum(self.priceCaches) / len(self.priceCaches))
								self.priceCaches.clear()
						self.tickerCounter += 1
						self.lastTimestamp = int(time() // 60 * 60)
						doRefresh = True
					elif self.priceCaches:
						pcs = sum(self.priceCaches)
						pcl = len(self.priceCaches)
						if lastData != (pcs, pcl):
							self.prices[-1] = pcs / pcl
							self.priceCaches.clear()
							lastData = pcs, pcl
							doRefresh = True
				if lastTS != int(time()%60):
					lastTS = int(time()%60)
					doRefresh = True
				if not doRefresh:
					continue
				screen.clear()
				# Parsing cache
				screen.move(0, 0)
				self._write("BTC price: ")
				self._write("{:.2F}".format(self.prices[-1]), "RED" if self.prices[-1] < self.prices[-2] else "GREEN")
				self._write(" USD | ")
				self._write("{}".format(60-int(time()-self.lastTimestamp)), "YELLOW")
				self._write(" seconds left for the next tick. [{} tickers in cache]\n".format(len(self.prices)))
				self._write("Changes: ")
				for i, (d, tDiff) in enumerate([
					("1 min:   ", TickerDiff(self.prices[-1], self.prices[-2])),
					("15 min:  ", TickerDiff(self.prices[-1], self.prices[-16])),
					("30 min:  ", TickerDiff(self.prices[-1], self.prices[-31])),
					("1 hour:  ", TickerDiff(self.prices[-1], self.prices[-61])),
					("12 hour: ", TickerDiff(self.prices[-1], self.prices[-721])),
				]):
					if i > 0:
						d = " | " + d
					text = "{sign}{val:.2F} ({sign}{perc:.2F}%)".format(**tDiff.__dict__)
					cy, cx = screen.getyx()
					if len(text)+len(d) >= (self.terminalSize.x-cx):
						self._write("\n")
						d = "         "+d[3:]
					self._write(d)
					self._write(text, tDiff.color)
				cy, cx = screen.getyx()
				writeChart(
					screen,
					xStart=0,
					xEnd=self.terminalSize.x,
					yStart=cy+2,
					yEnd=self.terminalSize.y-1,
					data=self.prices,
					tickerMargin=0.1,
				)
				screen.refresh()
		except KeyboardInterrupt:
			return
		finally:
			self._close()
			curses.endwin()
	def start(self) -> None:
		self._start()
		curses.wrapper(self._loop)
