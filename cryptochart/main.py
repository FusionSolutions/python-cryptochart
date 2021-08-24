# Builtin modules
import curses
from time import sleep, time
from threading import Thread, Event, Lock
from typing import Dict, List, Any, TYPE_CHECKING
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
	closeEvent:Event
	pricesLock:Lock
	terminalSize:YX
	screen:Any
	currency:str
	thr:Thread
	def __init__(self, currency:str="btc") -> None:
		self.terminalSize  = YX(0, 0)
		self.closeEvent    = Event()
		self.pricesLock    = Lock()
		self.lastTimestamp = 0
		self.prices        = []
		self.priceCaches   = []
	def _write(self, text:str, color:str="WHITE") -> None:
		self.screen.addstr(text, curses.color_pair(COLORS[color]))
	def _writeN(self, text:str, length:int, color:str="WHITE") -> None:
		self.screen.addnstr(text, length, curses.color_pair(COLORS[color]))
	def _fetchFirst(self) -> None: ...
	def _fetchThreadLoop(self) -> None: ...
	def _loop(self, screen:Any) -> None:
		try:
			try:
				curses.start_color()
				curses.use_default_colors()
				for i in range(curses.COLORS):
					curses.init_pair(i+1, i, -1)
				screen.attron( curses.color_pair(COLORS["WHITE"]) )
				curses.curs_set(0)
			except:
				curses.initscr()
			screen.timeout(0)
			screen.clear()
			screen.addstr("Loading prices...")
			screen.refresh()
			self.screen = screen
			while True:
				sleep(1)
				screen.clear()
				tmpTerminalSize = YX(*screen.getmaxyx())
				if tmpTerminalSize != self.terminalSize:
					self.terminalSize = tmpTerminalSize
				if self.terminalSize.x <= 30 or self.terminalSize.y <= 15:
					self._writeN("No place to print", 17, "RED")
					screen.refresh()
					continue
				with self.pricesLock:
					if time()-self.lastTimestamp > 60:
						if not self.priceCaches:
							self.prices.append(self.prices[-1])
						else:
							self.prices.append(sum(self.priceCaches) / len(self.priceCaches))
							self.priceCaches.clear()
						self.lastTimestamp = int(time() // 60 * 60)
					else:
						if self.priceCaches:
							self.prices[-1] = sum(self.priceCaches) / len(self.priceCaches)
							self.priceCaches.clear()
				# Parsing cache
				screen.move(0, 0)
				self._write("BTC price: ")
				self._write("{:.2F}".format(self.prices[-1]), "RED" if self.prices[-1] < self.prices[-2] else "GREEN")
				self._write(" USD ")
				self._write("{}".format(60-int(time()-self.lastTimestamp)), "YELLOW")
				self._write(" seconds left for the next tick. [{} tickers in cache]\n".format(len(self.prices)))
				self._write("Changes: ")
				for i, tDiff in enumerate([
					TickerDiff(self.prices[-1], self.prices[-2]),
					TickerDiff(self.prices[-1], self.prices[-16]),
					TickerDiff(self.prices[-1], self.prices[-31]),
					TickerDiff(self.prices[-1], self.prices[-61]),
				]):
					if i > 0:
						self._write(" : ")
					self._write("{sign}{val:.2F} ({sign}{perc:.2F}%)".format(**tDiff.__dict__), tDiff.color)
				self._write(" (1min:15min:30min:1hour)")
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
			self.closeEvent.set()
			self.thr.join(5)
			curses.endwin()
	def start(self) -> None:
		self._fetchFirst()
		self.thr = Thread(target=self._fetchThreadLoop, daemon=True)
		self.thr.start()
		curses.wrapper(self._loop)
