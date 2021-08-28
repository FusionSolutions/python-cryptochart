# Builtin modules
import curses
from typing import Union, List, Any
# Third party modules
# Local modules
# Program
COLORS = {
	"WHITE":0,
	"BLUE":5,
	"CYAN":7,
	"GREEN":3,
	"MAGENTA":6,
	"RED":2,
	"SILVER":8,
	"YELLOW":4,
	"DARKSILVER":9,
}

def writeChart(screen:Any, xStart:int, xEnd:int, yStart:int, yEnd:int, data:List[Union[float, int]], tickerMargin:float=0.1,
labelFormat:str=" {:8.2f} ", symbols:List[str]=["┼", "┤", "├", "│", "─", "╰", "╭", "╮", "╯"]) -> None:
	def scale(val:float) -> int:
		return max(round((maxVal-val) / stepVal)-1, 0)
	assert yEnd > yStart
	assert xEnd > xStart
	rows = yEnd - yStart
	# Converting data to float
	chartData:List[float] = [ float(val) for val in data ]
	# Calculating label length
	labelLength = len(labelFormat.format(chartData[0]))
	# Calculating everything else
	chartXStart = xStart + labelLength
	chartXEnd = xEnd - labelLength -1
	chartYStart = yStart
	# chartYEnd = yEnd
	assert chartXEnd > chartXStart
	chartColumns = chartXEnd - chartXStart
	chartData = chartData[-chartColumns:]
	# Apply chart margin except when the last item is lower/higher as the calculated margin
	maxVal = max(chartData[:-1])
	minVal = min(chartData[:-1])
	marginVal = (maxVal - minVal) * tickerMargin
	maxVal += marginVal
	minVal -= marginVal
	if maxVal < chartData[-1]:
		maxVal = chartData[-1] + marginVal
	if minVal > chartData[-1]:
		minVal = chartData[-1] - marginVal
	stepVal = (maxVal - minVal) / rows
	# Drawing labels
	for y in range(rows):
		label = labelFormat.format( maxVal-(y+1)*stepVal )
		colorLeft = "WHITE"
		colorRight = "WHITE"
		scaleFirst = scale(chartData[0])
		scaleLast = scale(chartData[-1])
		bestPrice = scale(max(chartData))
		worstPrice = scale(min(chartData))
		if bestPrice != worstPrice and bestPrice == y:
			colorLeft = "GREEN"
		elif bestPrice != worstPrice and worstPrice == y:
			colorLeft = "RED"
		elif scaleFirst == y:
			colorLeft = "CYAN"
		if bestPrice != worstPrice and bestPrice == y:
			colorRight = "GREEN"
		elif bestPrice != worstPrice and worstPrice == y:
			colorRight = "RED"
		elif scaleLast == y:
			colorRight = "CYAN"
		screen.addstr(
			yStart + y,
			xStart,
			label,
			curses.color_pair(COLORS[colorLeft]),
		)
		screen.addstr(
			yStart + y,
			xEnd - labelLength,
			label,
			curses.color_pair(COLORS[colorRight]),
		)
		#
		screen.addstr(
			yStart + y,
			xStart + labelLength,
			symbols[0 if scaleFirst==y else 1],
			curses.color_pair(COLORS["WHITE"]),
		)
		screen.addstr(
			yStart + y,
			xEnd - labelLength - 1,
			symbols[0 if scaleLast==y else 2],
			curses.color_pair(COLORS["WHITE"]),
		)
	# Drawing separator
	for x in range(30, chartColumns, 30):
		for y in range(rows):
			screen.addstr(
				chartYStart + y,
				chartXEnd - x,
				symbols[3],
				curses.color_pair(COLORS["DARKSILVER"]),
			)
	# Drawing lines
	isRising = True
	for x in range(0, len(chartData) - 1):
		d0 = chartData[x]
		d1 = chartData[x + 1]
		y0 = scale(d0)
		y1 = scale(d1)
		if y0 == y1:
			screen.addstr(
				chartYStart + y0,
				chartXStart + x + 1,
				symbols[4],
				curses.color_pair(COLORS["GREEN" if isRising else "RED"]),
			)
			continue
		isRising = y0 > y1
		screen.addstr(
			chartYStart + y1,
			chartXStart + x + 1,
			symbols[5] if y0 < y1 else symbols[6],
			curses.color_pair(COLORS["GREEN" if isRising else "RED"]),
		)
		screen.addstr(
			chartYStart + y0,
			chartXStart + x + 1,
			symbols[7] if y0 < y1 else symbols[8],
			curses.color_pair(COLORS["GREEN" if isRising else "RED"]),
		)
		start = min(y0, y1) + 1
		end = max(y0, y1)
		for y in range(start, end):
			screen.addstr(
				chartYStart + y,
				chartXStart + x + 1,
				symbols[3],
				curses.color_pair(COLORS["GREEN" if isRising else "RED"]),
			)
