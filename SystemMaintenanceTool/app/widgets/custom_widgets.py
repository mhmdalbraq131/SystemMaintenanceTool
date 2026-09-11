"""Custom widgets for System Maintenance Tool Professional.

- CardWidget: Styled card container
- ProgressRing: Circular progress gauge
- SidebarButton: Navigation button with icon
- MetricCard: Small metric display card
- GaugeWidget: Analog-style gauge
"""

from __future__ import annotations

import math

from PySide6.QtCore import Qt, QSize, QRectF, QTimer, Property, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QConicalGradient, QRadialGradient, QPainterPath, QBrush
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy, QProgressBar, QApplication,
)

from app.core.theme import (
    BG_CARD, BG_CARD_HOVER, BORDER_DEFAULT, BORDER_LIGHT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_ACCENT,
    ACCENT_PRIMARY, ACCENT_CYAN, ACCENT_GREEN, ACCENT_ORANGE, ACCENT_RED,
    STATUS_HEALTHY, STATUS_WARNING, STATUS_CRITICAL,
    CARD_RADIUS, BUTTON_RADIUS, SPACING_SM, SPACING_MD, SPACING_LG,
    ICON_SIZE_SM, ICON_SIZE_MD,
)


# ── Card Widget ──────────────────────────────────────────────────────────

class CardWidget(QFrame):
    """A styled card container with optional title."""

    def __init__(self, title: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("CardWidget")
        self._title = title
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)
        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {TEXT_ACCENT};")
            layout.addWidget(title_label)

    def get_layout(self) -> QVBoxLayout:
        return self.layout()


# ── Progress Ring ─────────────────────────────────────────────────────────

class ProgressRing(QWidget):
    """Circular progress indicator with percentage text."""

    def __init__(
        self,
        size: int = 120,
        line_width: int = 10,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._size = size
        self._line_width = line_width
        self._value = 0.0
        self._max = 100.0
        self._color = ACCENT_PRIMARY
        self._label = ""
        self._sub_label = ""
        self.setFixedSize(size, size)

    def set_value(self, val: float) -> None:
        self._value = max(0, min(val, self._max))
        self.update()

    def set_color(self, color: str) -> None:
        self._color = color
        self.update()

    def set_label(self, text: str) -> None:
        self._label = text
        self.update()

    def set_sub_label(self, text: str) -> None:
        self._sub_label = text
        self.update()

    def _auto_color(self) -> str:
        pct = (self._value / self._max) * 100 if self._max else 0
        if pct < 50:
            return STATUS_HEALTHY
        elif pct < 80:
            return STATUS_WARNING
        else:
            return STATUS_CRITICAL

    def paintEvent(self, event) -> None:  # type: ignore
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(
            self._line_width / 2,
            self._line_width / 2,
            self._size - self._line_width,
            self._size - self._line_width,
        )

        # Background arc
        pen_bg = QPen(QColor(BG_CARD))
        pen_bg.setWidth(self._line_width)
        pen_bg.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_bg)
        painter.drawArc(rect, 90 * 16, 360 * 16)

        # Foreground arc
        pct = self._value / self._max if self._max else 0
        span = int(pct * 360 * 16)
        color = QColor(self._color if self._color != "auto" else self._auto_color())
        pen_fg = QPen(color)
        pen_fg.setWidth(self._line_width)
        pen_fg.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_fg)
        painter.drawArc(rect, 90 * 16, -span)

        # Center text
        painter.setPen(QColor(TEXT_PRIMARY))
        font_pct = QFont("Segoe UI", max(int(self._size / 5), 10), QFont.Bold)
        painter.setFont(font_pct)
        painter.drawText(rect, Qt.AlignCenter, f"{self._value:.0f}%")

        # Label below percentage
        if self._label:
            painter.setPen(QColor(TEXT_SECONDARY))
            font_label = QFont("Segoe UI", max(int(self._size / 10), 8))
            painter.setFont(font_label)
            label_rect = QRectF(rect.x(), rect.y() + rect.height() * 0.55, rect.width(), rect.height() * 0.45)
            painter.drawText(label_rect, Qt.AlignCenter, self._label)

        if self._sub_label:
            painter.setPen(QColor(TEXT_MUTED))
            font_sub = QFont("Segoe UI", max(int(self._size / 12), 7))
            painter.setFont(font_sub)
            sub_rect = QRectF(rect.x(), rect.y() + rect.height() * 0.75, rect.width(), rect.height() * 0.25)
            painter.drawText(sub_rect, Qt.AlignCenter, self._sub_label)

        painter.end()


# ── Metric Card ──────────────────────────────────────────────────────────

class MetricCard(CardWidget):
    """Small card showing a single metric with label and value."""

    def __init__(
        self,
        title: str = "",
        value: str = "0",
        unit: str = "",
        color: str = TEXT_PRIMARY,
        parent: QWidget | None = None,
    ):
        super().__init__(parent=parent)
        self.setObjectName("CardWidget")
        self.setMaximumHeight(100)
        layout = self.get_layout()

        self._title_lbl = QLabel(title)
        self._title_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        layout.addWidget(self._title_lbl)

        self._value_lbl = QLabel(value)
        self._value_lbl.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: bold;")
        layout.addWidget(self._value_lbl)

        if unit:
            unit_lbl = QLabel(unit)
            unit_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
            layout.addWidget(unit_lbl)

    def set_value(self, text: str) -> None:
        self._value_lbl.setText(text)

    def set_color(self, color: str) -> None:
        self._value_lbl.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: bold;")


# ── Sidebar Button ────────────────────────────────────────────────────────

class SidebarButton(QPushButton):
    """Navigation button for the sidebar with icon support."""

    checked_changed = Signal(bool)

    def __init__(
        self,
        text: str = "",
        icon_char: str = "",
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setObjectName("SidebarButton")
        self.setText(f"  {icon_char}  {text}" if icon_char else f"  {text}")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(40)
        self._checked = False
        self.clicked.connect(self._on_click)

    def _on_click(self) -> None:
        self._checked = True
        self.setProperty("checked", "true")
        self.style().unpolish(self)
        self.style().polish(self)
        self.checked_changed.emit(True)

    def set_checked(self, checked: bool) -> None:
        self._checked = checked
        self.setProperty("checked", "true" if checked else "false")
        self.style().unpolish(self)
        self.style().polish(self)

    def is_checked(self) -> bool:
        return self._checked


# ── Sparkline Chart ───────────────────────────────────────────────────────

class SparklineWidget(QWidget):
    """Mini line chart showing last N data points."""

    def __init__(self, points: int = 60, height: int = 60, parent: QWidget | None = None):
        super().__init__(parent)
        self._points: list[float] = []
        self._max_points = points
        self._color = ACCENT_PRIMARY
        self.setFixedHeight(height)
        self.setMinimumWidth(200)

    def set_color(self, color: str) -> None:
        self._color = color

    def add_point(self, val: float) -> None:
        self._points.append(val)
        if len(self._points) > self._max_points:
            self._points.pop(0)
        self.update()

    def clear_points(self) -> None:
        self._points.clear()
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore
        if not self._points:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        padding = 4

        vals = self._points
        mn = 0
        mx = max(max(vals), 1)

        # Draw area fill
        path = QPainterPath()
        step_x = (w - 2 * padding) / max(self._max_points - 1, 1)

        points_list = []
        for i, v in enumerate(vals):
            x = padding + i * step_x
            y = h - padding - (v / mx) * (h - 2 * padding)
            points_list.append((x, y))

        if points_list:
            path.moveTo(points_list[0][0], points_list[0][1])
            for x, y in points_list[1:]:
                path.lineTo(x, y)

            # Area
            fill_path = QPainterPath(path)
            fill_path.lineTo(points_list[-1][0], h - padding)
            fill_path.lineTo(points_list[0][0], h - padding)
            fill_path.closeSubpath()

            color = QColor(self._color)
            fill_color = QColor(self._color + "33")
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(fill_color))
            painter.drawPath(fill_path)

            # Line
            pen = QPen(color, 2)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)

        painter.end()


# ── Status Badge ──────────────────────────────────────────────────────────

class StatusBadge(QLabel):
    """Colored status indicator label."""

    def __init__(self, text: str = "", status: str = "healthy", parent: QWidget | None = None):
        super().__init__(parent)
        self._status = status
        self.setText(text)
        self._apply_style()

    def set_status(self, status: str) -> None:
        self._status = status
        self._apply_style()

    def _apply_style(self) -> None:
        colors = {
            "healthy": (STATUS_HEALTHY, STATUS_HEALTHY + "22"),
            "warning": (STATUS_WARNING, STATUS_WARNING + "22"),
            "critical": (STATUS_CRITICAL, STATUS_CRITICAL + "22"),
            "unknown": (STATUS_UNKNOWN, STATUS_UNKNOWN + "22"),
        }
        fg, bg = colors.get(self._status, colors["unknown"])
        self.setStyleSheet(
            f"color: {fg}; background: {bg}; "
            f"padding: 3px 10px; border-radius: 10px; font-weight: bold; font-size: 12px;"
        )
