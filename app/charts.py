"""
charts.py
Small, dependency-free charts drawn with QPainter, styled with the
colours in theme.py. No extra pip installs needed.

    SeverityBarChart  - horizontal bars, one per severity level
    LineChart         - one or more lines over a shared x-axis

Both are "dumb" widgets: they only draw whatever data you give them
through set_data(). They never fetch data themselves.
"""

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QSizePolicy, QWidget

from app import theme


# ---------------------------------------------------------------------------
# Severity bar chart
# ---------------------------------------------------------------------------
class SeverityBarChart(QWidget):
    """Horizontal bars, e.g. Critical 5 / High 9 / Medium 12 / Low 8."""

    ROW_HEIGHT = 44
    LABEL_WIDTH = 80
    COUNT_WIDTH = 84     # room for e.g. "12  (35%)" right of the bar
    BAR_HEIGHT = 14

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = {}
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_data(self, data: dict):
        """data: {"Critical": 5, "High": 9, ...} — drawn in the order given."""
        self._data = dict(data)
        self.setFixedHeight(max(1, len(self._data)) * self.ROW_HEIGHT)
        self.update()  # ask Qt to repaint

    def paintEvent(self, event):
        if not self._data:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        total = sum(self._data.values()) or 1
        biggest = max(self._data.values()) or 1
        bar_left = self.LABEL_WIDTH
        bar_width = max(10, self.width() - self.LABEL_WIDTH - self.COUNT_WIDTH - 12)

        for row, (label, count) in enumerate(self._data.items()):
            top = row * self.ROW_HEIGHT
            centre_y = top + self.ROW_HEIGHT / 2
            colour = QColor(theme.SEVERITY_COLOURS.get(label, theme.ACCENT_INFO))

            # label on the left
            painter.setPen(QColor(theme.TEXT_PRIMARY))
            painter.drawText(QRectF(0, top, self.LABEL_WIDTH, self.ROW_HEIGHT),
                             Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, label)

            # grey track, then the coloured bar on top of it
            bar_top = centre_y - self.BAR_HEIGHT / 2
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(theme.BG_DARK))
            painter.drawRoundedRect(QRectF(bar_left, bar_top, bar_width, self.BAR_HEIGHT), 4, 4)

            filled = bar_width * count / biggest
            if count > 0:
                painter.setBrush(colour)
                painter.drawRoundedRect(QRectF(bar_left, bar_top, max(filled, 6), self.BAR_HEIGHT), 4, 4)

            # count + percentage on the right
            percent = round(100 * count / total)
            painter.setPen(QColor(theme.TEXT_PRIMARY))
            painter.drawText(QRectF(self.width() - self.COUNT_WIDTH, top, self.COUNT_WIDTH, self.ROW_HEIGHT),
                             Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                             f"{count}  ({percent}%)")
        painter.end()


# ---------------------------------------------------------------------------
# Line chart
# ---------------------------------------------------------------------------
class LineChart(QWidget):
    """One or more lines sharing the same x-axis labels."""

    MARGIN_LEFT = 36
    MARGIN_RIGHT = 22    # room for the last x-axis label
    MARGIN_TOP = 34      # room for the legend
    MARGIN_BOTTOM = 26   # room for x-axis labels
    GRID_LINES = 4

    # colour for each line, in order
    LINE_COLOURS = [theme.ACCENT_INFO, theme.ACCENT_WARN, theme.ACCENT, theme.ACCENT_DANGER]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._labels = []
        self._series = {}
        self.setMinimumHeight(240)

    def set_data(self, labels: list, series: dict):
        """labels: ["W1", "W2", ...]; series: {"Scans": [..], "Findings": [..]}"""
        self._labels = list(labels)
        self._series = dict(series)
        self.update()

    @staticmethod
    def _nice_max(value):
        """Round the top of the y-axis up to a tidy number (4, 8, 10, 20...)."""
        for step in (4, 8, 10, 20, 40, 50, 100, 200, 500, 1000):
            if value <= step:
                return step
        return value

    def paintEvent(self, event):
        if not self._labels or not self._series:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        plot = QRectF(self.MARGIN_LEFT, self.MARGIN_TOP,
                      self.width() - self.MARGIN_LEFT - self.MARGIN_RIGHT,
                      self.height() - self.MARGIN_TOP - self.MARGIN_BOTTOM)
        y_max = self._nice_max(max((max(v) for v in self._series.values() if v), default=1))
        point_count = len(self._labels)

        def x_at(i):
            if point_count == 1:
                return plot.center().x()
            return plot.left() + plot.width() * i / (point_count - 1)

        def y_at(value):
            return plot.bottom() - plot.height() * value / y_max

        # --- grid lines + y-axis numbers ---
        muted = QColor(theme.TEXT_MUTED)
        for i in range(self.GRID_LINES + 1):
            value = y_max * i / self.GRID_LINES
            y = y_at(value)
            painter.setPen(QPen(QColor(theme.BORDER), 1))
            painter.drawLine(QPointF(plot.left(), y), QPointF(plot.right(), y))
            painter.setPen(muted)
            painter.drawText(QRectF(0, y - 8, self.MARGIN_LEFT - 8, 16),
                             Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                             f"{value:g}")

        # --- x-axis labels ---
        for i, label in enumerate(self._labels):
            painter.drawText(QRectF(x_at(i) - 30, plot.bottom() + 6, 60, 16),
                             Qt.AlignmentFlag.AlignCenter, label)

        # --- the lines themselves ---
        for index, (name, values) in enumerate(self._series.items()):
            colour = QColor(self.LINE_COLOURS[index % len(self.LINE_COLOURS)])
            path = QPainterPath()
            for i, value in enumerate(values):
                point = QPointF(x_at(i), y_at(value))
                path.moveTo(point) if i == 0 else path.lineTo(point)
            painter.setPen(QPen(colour, 2.5))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)

            # dots on each data point
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(colour)
            for i, value in enumerate(values):
                painter.drawEllipse(QPointF(x_at(i), y_at(value)), 3.5, 3.5)

        # --- legend (top-right) ---
        x = plot.right()
        for index, name in reversed(list(enumerate(self._series))):
            colour = QColor(self.LINE_COLOURS[index % len(self.LINE_COLOURS)])
            text_width = painter.fontMetrics().horizontalAdvance(name)
            x -= text_width
            painter.setPen(QColor(theme.TEXT_PRIMARY))
            painter.drawText(QRectF(x, 4, text_width, 18), Qt.AlignmentFlag.AlignVCenter, name)
            x -= 16
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(colour)
            painter.drawRoundedRect(QRectF(x, 8, 10, 10), 2, 2)
            x -= 18
        painter.end()