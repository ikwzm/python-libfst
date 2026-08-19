#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-2-Clause
# Copyright (c) 2026 ikwzm

import sys
import runpy

from PySide6.QtCore    import Qt
from PySide6.QtCore    import QAbstractTableModel, QModelIndex
from PySide6.QtCore    import QRect, QSize, QTimer, Signal
from PySide6.QtGui     import QPainter, QPen, QBrush, QFontMetrics, QColor
from PySide6.QtWidgets import (
    QApplication,
    QTableView,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QScrollBar,
    QHeaderView,
)
from fst_wave_view_model import FST_Wave_View_Model

DEFAULT_HEADER_HEIGHT      = 24
DEFAULT_SIGNAL_HEIGHT      = 24
DEFAULT_FOOTER_HEIGHT      = 20
DEFAULT_SIGNAL_NAME_WIDTH  = 300
DEFAULT_SIGNAL_VALUE_WIDTH = 300

class SignalNameColumn(QTableView):

    class SignalNameModel(QAbstractTableModel):
        SIGNAL_COLUMN = 0
        COLUMN_COUNT  = 1

        def __init__(self, view_model, parent=None):
            super().__init__(parent)
            self.view_model   = view_model
            self.current_time = self.view_model.current_time

        def columnCount(self, parent=QModelIndex()):
            return self.COLUMN_COUNT

        def rowCount(self, parent=QModelIndex()):
            return self.view_model.row_count()

        def flags(self, index):
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
            
        def data(self, index, role=Qt.DisplayRole):
            if not index.isValid():
                return None

            item = self.view_model.row_to_item(index.row())
            if item is None:
                return None

            if role == Qt.DisplayRole:
                if index.column() == self.SIGNAL_COLUMN:
                    if self.view_model.item_is_group(item):
                        if item.expanded:
                            mark = "\u25bc"
                        else:
                            mark = "\u25b6"
                    else:
                            mark = "\u3000"
                    indent = " " * ((item.depth-1)*2)
                    return indent + mark + " " + item.display_name

            if role == Qt.BackgroundRole:
                if index.column() == self.SIGNAL_COLUMN:
                    color = item.get_background_color("name")
                    if color is not None:
                        return QColor(color)
            
            if role == Qt.ForegroundRole:
                if index.column() == self.SIGNAL_COLUMN:
                    color = item.get_foreground_color("name")
                    if color is not None:
                        return QColor(color)
            
            return None

        def headerData(self, section, orientation, role=Qt.DisplayRole):
            if orientation != Qt.Horizontal:
                return None
            if role != Qt.DisplayRole:
                return None
            if section == self.SIGNAL_COLUMN:
                return "Signal Name"
            return None

        def refresh(self):
            self.beginResetModel()
            self.endResetModel()

        def set_current_time(self, current_time):
            self.current_time = current_time;
            
    view_model_changed = Signal()

    def __init__(self, view_model, parent=None):
        super().__init__(parent)
        self.view_model   = view_model
        self.table_model  = self.SignalNameModel(view_model, self)
        self.current_time = self.view_model.current_time
        self.setModel(self.table_model)

        header_height = self.view_model.get_option("header_height"     , DEFAULT_HEADER_HEIGHT)
        signal_height = self.view_model.get_option("signal_height"     , DEFAULT_SIGNAL_HEIGHT)
        footer_height = self.view_model.get_option("footer_height"     , DEFAULT_FOOTER_HEIGHT)
        name_width    = self.view_model.get_option("signal_name_width" , DEFAULT_SIGNAL_NAME_WIDTH)

        header = self.horizontalHeader()
        header.setStretchLastSection(False)
        header.setFixedHeight(header_height)
        header.setSectionResizeMode(self.SignalNameModel.SIGNAL_COLUMN, QHeaderView.Fixed)
        header.resizeSection(self.SignalNameModel.SIGNAL_COLUMN, name_width)

        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.verticalHeader().setDefaultSectionSize(signal_height)
        self.verticalHeader().setVisible(False)
        self.horizontalScrollBar().setFixedHeight(footer_height)

        self.setStyleSheet(
            "QTableView           {background-color: black; color: white;}"
        )

    def mouseDoubleClickEvent(self, event):
        index = self.indexAt(event.position().toPoint())

        if index.isValid():
            row  = index.row()
            item = self.view_model.row_to_item(row)

            if self.view_model.item_is_group(item):
                self.view_model.toggle_group(item)

                self.table_model.refresh()

                new_row = self.view_model.item_to_row(item)
                if new_row is not None:
                    new_index = self.table_model.index(
                        new_row,
                        self.SignalNameModel.SIGNAL_COLUMN
                    )
                    self.scrollTo(new_index)

                self.view_model_changed.emit()
                event.accept()
                return

        super().mouseDoubleClickEvent(event)

    def wheelEvent(self, event):
        window = self.window()
        if hasattr(window, "wheel_scroll"):
            window.wheel_scroll(event)
            return
        super().wheelEvent(event)

    def refresh(self):
        self.view_model.rebuild()
        self.table_model.refresh()

    def set_row_scroll_value(self, value):
        scrollbar = self.verticalScrollBar()
        if scrollbar.value() != value:
            scrollbar.setValue(value)

    def set_current_time(self, current_time):
        self.current_time = current_time;
        self.table_model.set_current_time(current_time)

class SignalValueColumn(QTableView):

    class SignalValueModel(QAbstractTableModel):
        VALUE_COLUMN  = 0
        COLUMN_COUNT  = 1

        def __init__(self, view_model, parent=None):
            super().__init__(parent)
            self.view_model   = view_model
            self.current_time = self.view_model.current_time

        def columnCount(self, parent=QModelIndex()):
            return self.COLUMN_COUNT

        def rowCount(self, parent=QModelIndex()):
            return self.view_model.row_count()

        def flags(self, index):
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
            
        def data(self, index, role=Qt.DisplayRole):
            if not index.isValid():
                return None

            item = self.view_model.row_to_item(index.row())
            if item is None:
                return None

            if role == Qt.DisplayRole:
                if index.column() == self.VALUE_COLUMN:
                    if self.view_model.item_is_signal(item):
                        return self._get_value(item)
                    else:
                        return ""

            if role == Qt.BackgroundRole:
                if index.column() == self.VALUE_COLUMN:
                    color = item.get_background_color("value")
                    if color is not None:
                        return QColor(color)
            
            if role == Qt.ForegroundRole:
                if index.column() == self.VALUE_COLUMN:
                    color = item.get_foreground_color("value")
                    if color is not None:
                        return QColor(color)
            
            return None

        def headerData(self, section, orientation, role=Qt.DisplayRole):
            if orientation != Qt.Horizontal:
                return None
            if role != Qt.DisplayRole:
                return None
            if section == self.VALUE_COLUMN:
                return "Value"
            return None

        def _get_value(self, signal):
            wave = signal.get_wave(self.current_time, self.current_time)
            try:
                return signal.format_value(next(wave)[1])
            except StopIteration:
                return ""

        def refresh(self):
            self.beginResetModel()
            self.endResetModel()

        def set_current_time(self, current_time):
            self.current_time = current_time;
            self.refresh()

    def __init__(self, view_model, parent=None):
        super().__init__(parent)
        self.view_model  = view_model
        self.table_model = self.SignalValueModel(view_model, self)
        self.setModel(self.table_model)

        header_height = self.view_model.get_option("header_height"     , DEFAULT_HEADER_HEIGHT)
        signal_height = self.view_model.get_option("signal_height"     , DEFAULT_SIGNAL_HEIGHT)
        footer_height = self.view_model.get_option("footer_height"     , DEFAULT_FOOTER_HEIGHT)
        value_width   = self.view_model.get_option("signal_value_width", DEFAULT_SIGNAL_VALUE_WIDTH)

        header = self.horizontalHeader()
        header.setStretchLastSection(False)
        header.setFixedHeight(header_height)
        header.resizeSection(self.SignalValueModel.VALUE_COLUMN, value_width)

        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.verticalHeader().setDefaultSectionSize(signal_height)
        self.verticalHeader().setVisible(False)
        self.horizontalScrollBar().setFixedHeight(footer_height)

        self.setStyleSheet(
            "QTableView           {background-color: black; color: white;}"
        )

    def wheelEvent(self, event):
        window = self.window()
        if hasattr(window, "wheel_scroll"):
            window.wheel_scroll(event)
            return
        super().wheelEvent(event)

    def refresh(self):
        self.table_model.refresh()

    def set_row_scroll_value(self, value):
        scrollbar = self.verticalScrollBar()
        if scrollbar.value() != value:
            scrollbar.setValue(value)

    def set_current_time(self, current_time):
        self.current_time = current_time;
        self.table_model.set_current_time(current_time)

class WaveformColumn(QWidget):

    time_range_changed = Signal(int, int)

    def __init__(self, view_model, parent=None):
        super().__init__(parent)
        self.view_model           = view_model
        self.start_time           = self.view_model.start_time
        self.end_time             = self.view_model.end_time
        self.total_start_time     = self.view_model.start_time
        self.total_end_time       = self.view_model.end_time
        self.row_height           = self.view_model.get_option("signal_height", DEFAULT_SIGNAL_HEIGHT)
        self.time_ruler_height    = self.view_model.get_option("header_height", DEFAULT_HEADER_HEIGHT)
        self.scrollbar_height     = self.view_model.get_option("footer_height", DEFAULT_FOOTER_HEIGHT)
        self.minimum_signal_width = 1000
        self._updating_scrollbar  = False
        self.setMinimumWidth(300)

        self.time_ruler      = self.TimeRuler(self)
        self.waveform_widget = self.WaveformWidget(self)
        self.time_scrollbar  = QScrollBar(Qt.Horizontal, self)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.time_ruler     , 0)
        self.layout.addWidget(self.waveform_widget, 1)
        self.layout.addWidget(self.time_scrollbar , 0)

        self.time_scrollbar.setFixedHeight(self.scrollbar_height)
        self.time_scrollbar.valueChanged.connect(self._time_scrollbar_changed)
        self._update_scrollbar()

    class CursorWidget(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.x = 0
            self.setAttribute(Qt.WA_TransparentForMouseEvents)
            self.setAttribute(Qt.WA_TranslucentBackground)

        def set_x(self, x):
            self.x = x
            self.update()

        def paintEvent(self, event):
            painter = QPainter(self)
            pen = QPen(QColor("yellow"))
            pen.setWidth(1)
            painter.setPen(pen)
            painter.drawLine(
                self.x, 0,
                self.x, self.height()
            )
            
    class WaveformWidget(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.parent           = parent
            self.view_model       = self.parent.view_model
            self.start_time       = self.parent.start_time
            self.end_time         = self.parent.end_time
            self.row_scroll_value = 0
            self.background_color = self.view_model.get_option("color")["wave"]["background"]

            self.setMouseTracking(True)
            self.cursor_widget    = self.parent.CursorWidget(self)
            self.cursor_widget.setGeometry(self.rect())
            self.cursor_widget.raise_()

        def set_time_range(self, start_time, end_time):
            self.start_time = start_time
            self.end_time   = end_time
            self.update()

        def set_row_scroll_value(self, value):
            if self.row_scroll_value == value:
                return
            self.row_scroll_value = value
            self.update()

        def mouseMoveEvent(self, event):
            x = event.position().x()
            self.cursor_widget.set_x(x)

        def resizeEvent(self, event):
            super().resizeEvent(event)
            self.cursor_widget.setGeometry(self.rect())
            self.cursor_widget.raise_()
            
        def time_to_x(self, time):
            if self.end_time == self.start_time:
                return 0
            return int((time - self.start_time) * self.width() / (self.end_time - self.start_time))

        def x_to_time(self, x):
            if self.width() <= 0:
                return self.start_time
            x = max(0, min(self.width(), x))
            ratio = x / self.width()
            return self.start_time + ratio * (self.end_time - self.start_time)
        
        def paintEvent(self, event):
            painter      = QPainter(self)
            start_time   = self.start_time
            end_time     = self.end_time

            painter.fillRect(self.rect(), self.background_color)
            if end_time <= start_time:
                return
            
            width        = self.width()
            height       = self.height()
            row_height   = self.parent.row_height
            first_row    = self.row_scroll_value
            row_count    = self.view_model.row_count()
            edge_slop    = self.view_model.get_option("edge_slop", 0)
            visible_rows = height // row_height

            def draw_background():
                for i in range(visible_rows):
                    row   = first_row + i
                    if row >= row_count:
                        break
                    y     = i * row_height
                    rect  = QRect(0, y, width, row_height)
                    item  = self.view_model.row_to_item(row)
                    color = item.get_background_color("wave")
                    if color is not None:
                        painter.fillRect(rect, QColor(color))

            def draw_group(group, y):
                top    = y + 5
                bottom = y + row_height - 5
                height = bottom - top
                rect   = QRect(0, top, width, height)
                color  = group.get_color("wave", "group")
                if color is not None:
                    painter.fillRect(rect, QColor(color))
                
            def draw_signal(signal, y):
                top    = y + 5
                bottom = y + row_height - 5
                height = bottom - top

                def draw_signal_value(signal, value, left, width):
                    value_text   = str(signal.format_value(value))
                    value_color  = signal.get_color("wave", "value")
                    painter.setPen(QPen(QColor(value_color)))
                    font_metrics = painter.fontMetrics()
                    value_rect   = font_metrics.tightBoundingRect(value_text)
                    left_margin  = 2
                    right_margin = 2
                    draw_left    = left  + left_margin
                    draw_width   = width - left_margin - right_margin
                    if value_rect.width() < draw_width:
                        draw_rect  = QRect(draw_left, top, draw_width, height)
                        align_flag = Qt.AlignVCenter | Qt.AlignLeft
                        painter.drawText(draw_rect, align_flag, value_text)
                    
                def draw_signal_logic(signal, curr_value, prev_value, left, right):
                    width        = right - left
                    signal_color = signal.get_color("wave", "signal")
                    pen = QPen(QColor(signal_color))
                    painter.setPen(pen)
                    if curr_value in ("1", "h"):
                        curr_level = top
                    else:
                        curr_level = bottom
                    if prev_value is None:
                        prev_level = curr_level
                    elif prev_value in ("1", "h"):
                        prev_level = top
                    else:
                        prev_level = bottom
                    if curr_value != prev_value and edge_slop != 0 and edge_slop < width:
                        left_e = left + edge_slop
                        painter.drawLine(left  , prev_level, left_e, curr_level)
                        painter.drawLine(left_e, curr_level, right , curr_level)
                    else:
                        painter.drawLine(left  , curr_level, right , curr_level)
                        
                def draw_signal_bus(signal, curr_value, prev_value, left, right):
                    width            = right - left
                    background_color = signal.get_color("wave", "background")
                    signal_color     = signal.get_color("wave", "signal")
                    signal_pen       = QPen(QColor(signal_color))
                    if curr_value != prev_value and edge_slop != 0 and edge_slop < width:
                        draw_left  = left  + edge_slop
                        draw_width = right - draw_left
                        draw_rect  = QRect(draw_left, top, draw_width, height)
                        painter.fillRect(draw_rect, QColor(background_color))
                        painter.setPen(signal_pen)
                        painter.drawLine(left, top   , draw_left , bottom)
                        painter.drawLine(left, bottom, draw_left , top   )
                    else:
                        draw_left  = left
                        draw_width = right - left
                        draw_rect  = QRect(draw_left, top, draw_width, height)
                        painter.fillRect(draw_rect, QColor(background_color))
                        painter.setPen(signal_pen)
                    painter.drawLine(draw_left, top   , right, top   )
                    painter.drawLine(draw_left, bottom, right, bottom)
                    draw_signal_value(signal, curr_value, draw_left, draw_width)

                prev_value = None
                curr_value = None
                curr_time  = None
                for next_time, next_value in signal.get_wave(start_time, end_time):
                    if next_time < start_time:
                        prev_value = curr_value
                        curr_value = next_value
                        curr_time  = next_time
                        continue
                    if next_time > end_time:
                        break
                    if curr_time is None:
                        prev_value = curr_value
                        curr_value = next_value
                        curr_time  = next_time
                        continue
                    curr_x = self.time_to_x(curr_time)
                    next_x = self.time_to_x(next_time)
                    if signal.is_logic:
                        draw_signal_logic(signal, curr_value, prev_value, curr_x, next_x)
                    else:
                        draw_signal_bus(  signal, curr_value, prev_value, curr_x, next_x)
                    prev_value = curr_value
                    curr_value = next_value
                    curr_time  = next_time

                if curr_time is not None:
                    curr_x = self.time_to_x(curr_time)
                    next_x = self.time_to_x(end_time)
                    if signal.is_logic:
                        draw_signal_logic(signal, curr_value, prev_value, curr_x, next_x)
                    else:
                        draw_signal_bus(signal, curr_value, prev_value, curr_x, next_x)
                
            def draw_foreground():
                for i in range(visible_rows):
                    row   = first_row + i
                    if row >= row_count:
                        break
                    y     = i * row_height
                    item  = self.view_model.row_to_item(row)
                    if self.view_model.item_is_group(item):
                        draw_group(item, y)
                    if self.view_model.item_is_signal(item):
                        draw_signal(item, y)

            def draw_grid():
                time_range = self.end_time - self.start_time
                tick_count = 10
                tick_step  = time_range / tick_count
                pen = QPen(Qt.gray)
                pen.setStyle(Qt.DashLine)
                pen.setWidth(1)
                painter.setPen(pen)
                
                for i in range(tick_count + 1):
                    time = self.start_time + i * tick_step
                    x = self.time_to_x(time)
                    painter.drawLine(x, 0, x, height)

            draw_background()
            draw_grid()
            draw_foreground()


    class TimeRuler(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.parent           = parent
            self.view_model       = self.parent.view_model
            self.start_time       = self.parent.start_time
            self.end_time         = self.parent.end_time
            self.setMinimumHeight(self.parent.time_ruler_height)
            self.setMaximumHeight(self.parent.time_ruler_height)
            self.setStyleSheet(
                "background-color: black;"
            )

        def set_time_range(self, start_time, end_time):
            self.start_time = start_time
            self.end_time   = end_time
            self.update()

        def paintEvent(self, event):
            painter = QPainter(self)
            painter.fillRect(self.rect(), Qt.black )

            width  = self.width()
            height = self.height()

            painter.setPen(QPen(Qt.gray))
            painter.drawLine(0, height - 1, width, height - 1)

            if self.end_time <= self.start_time:
                return

            time_range = self.end_time - self.start_time

            tick_count = 10
            tick_step = time_range / tick_count

            for i in range(tick_count + 1):
                time = self.start_time + i * tick_step
                x = int((time - self.start_time) / time_range * width)
                painter.setPen(QPen(Qt.gray))
                painter.drawLine(x, height - 8, x, height)

                text = str(self.view_model.format_timestamp(time))
                painter.setPen(QPen(Qt.white))
                fm = painter.fontMetrics()
                text_width = fm.horizontalAdvance(text)
                painter.drawText(x - text_width // 2, 15, text)

    def wheelEvent(self, event):
        window = self.window()
        if hasattr(window, "wheel_scroll"):
            window.wheel_scroll(event)
            return
        super().wheelEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        total_height = self.height()
        available_height = total_height - (self.time_ruler_height + self.scrollbar_height)
        if available_height < self.row_height:
            row_count = 1
        else:
            row_count = available_height // self.row_height
        wave_widget_height    = row_count * self.row_height
        width                 = self.width()
        time_ruler_y_pos      = 0
        waveform_widget_y_pos = time_ruler_y_pos      + self.time_ruler_height
        time_scrollbar_y_pos  = waveform_widget_y_pos + wave_widget_height
        self.time_ruler.setGeometry(     0, time_ruler_y_pos     , width, self.time_ruler_height)
        self.waveform_widget.setGeometry(0, waveform_widget_y_pos, width, wave_widget_height    )
        self.time_scrollbar.setGeometry( 0, time_scrollbar_y_pos , width, self.scrollbar_height )
        
    def set_row_scroll_value(self, value):
        self.waveform_widget.set_row_scroll_value(value)

    def set_time_range(self, start_time, end_time):
        if start_time > end_time:
            start_time, end_time = end_time, start_time
        start_time = max(self.total_start_time, start_time)
        end_time   = min(self.total_end_time  , end_time  )
        if start_time >= end_time:
            return

        changed = (
            self.start_time != start_time or
            self.end_time   != end_time
        )
        self.start_time = start_time
        self.end_time   = end_time

        self._update_scrollbar()
        self.waveform_widget.set_time_range(start_time, end_time)
        self.time_ruler.set_time_range(start_time, end_time)

        if changed:
            self.time_range_changed.emit(
                self.start_time,
                self.end_time
            )

    def set_total_time_range(self, start_time, end_time):
        self.total_start_time = start_time
        self.total_end_time   = end_time

        self.start_time = start_time
        self.end_time   = end_time

        self._update_scrollbar()
        self.waveform_widget.set_time_range(start_time, end_time)
        self.time_ruler.set_time_range(start_time, end_time)

    def time_range(self):
        return self.start_time, self.end_time

    def display_time(self):
        return self.end_time - self.start_time

    def total_time(self):
        return self.total_end_time - self.total_start_time

    def _update_scrollbar(self):
        if self._updating_scrollbar:
            return

        self._updating_scrollbar = True

        try:
            total = self.total_time()
            visible = self.display_time()

            if total <= 0:
                self.time_scrollbar.setEnabled(False)
                return

            if visible >= total:
                self.time_scrollbar.setEnabled(False)
                self.time_scrollbar.setMinimum(0)
                self.time_scrollbar.setMaximum(0)
                self.time_scrollbar.setValue(0)
                return

            self.time_scrollbar.setEnabled(True)

            maximum = total - visible

            self.time_scrollbar.setMinimum(0)
            self.time_scrollbar.setMaximum(maximum)

            value = self.start_time - self.total_start_time

            value = max(0, min(value, maximum))

            self.time_scrollbar.setPageStep(visible)
            self.time_scrollbar.setValue(value)

        finally:
            self._updating_scrollbar = False

    def _time_scrollbar_changed(self, value):
        if self._updating_scrollbar:
            return

        visible = self.display_time()

        start_time = self.total_start_time + value
        end_time   = start_time + visible

        if end_time > self.total_end_time:
            end_time = self.total_end_time
            start_time = end_time - visible

        changed = (
            self.start_time != start_time or
            self.end_time   != end_time
        )

        self.start_time = start_time
        self.end_time   = end_time

        self.waveform_widget.update()

        if changed:
            self.time_range_changed.emit(
                self.start_time,
                self.end_time
            )

    def refresh(self):
        self.waveform_widget.update()

    def row_count(self):
        if not hasattr(self, "view_model"):
            return 0

        return self.view_model.row_count()

class WaveformWindow(QMainWindow):

    def __init__(self, view_model, parent=None):
        super().__init__(parent)

        self.view_model   = view_model
        self.start_time   = self.view_model.start_time
        self.end_time     = self.view_model.end_time
        self.current_time = self.view_model.current_time

        self.setWindowTitle("FST Wave Viewer")
        self.resize(1200, 700)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.name_column  = SignalNameColumn(self.view_model, central_widget)
        self.name_column.setFixedWidth(
            self.view_model.get_option("signal_name_width", DEFAULT_SIGNAL_NAME_WIDTH))
        layout.addWidget(self.name_column , 0)

        self.value_column = SignalValueColumn(self.view_model, central_widget)
        self.value_column.setFixedWidth(
            self.view_model.get_option("signal_value_width", DEFAULT_SIGNAL_VALUE_WIDTH))
        layout.addWidget(self.value_column, 0)

        self.wave_column  = WaveformColumn(self.view_model, central_widget)
        layout.addWidget(self.wave_column , 1)

        self.scrollbar    = QScrollBar(Qt.Vertical, central_widget)
        layout.addWidget(self.scrollbar   , 2)

        self.name_column.view_model_changed.connect(self._view_model_changed)
        self.scrollbar.valueChanged.connect(self._scrollbar_value_changed)

        # 注) すぐに self.name_column の verticalScrollBar() の設定が行われるとは限らないので
        # ここで self._update_vertical_scrollbar() を実行するのではなく、
        # 現在実行中の処理がすべて終了してから self._update_vertical_scrollbar() を実行する.
        # self._update_vertical_scrollbar()
        QTimer.singleShot(0, self._update_vertical_scrollbar)

    def _update_vertical_scrollbar(self):
        signal_scrollbar = self.name_column.verticalScrollBar()
        self.scrollbar.setMinimum(   signal_scrollbar.minimum()   )
        self.scrollbar.setMaximum(   signal_scrollbar.maximum()   )
        self.scrollbar.setPageStep(  signal_scrollbar.pageStep()  )
        self.scrollbar.setSingleStep(signal_scrollbar.singleStep())
        self.scrollbar.setValue(     signal_scrollbar.value()     )

    def _view_model_changed(self):
        self._update_vertical_scrollbar()
        self.name_column.refresh()
        self.value_column.refresh()
        self.wave_column.refresh()

    def _scrollbar_value_changed(self, value):
        self.name_column.set_row_scroll_value(value)
        self.value_column.set_row_scroll_value(value)
        self.wave_column.set_row_scroll_value(value)

    def wheel_scroll(self, event):
        delta = event.angleDelta().y()
        if delta == 0:
            event.ignore()
            return
        steps = delta // 120
        if steps == 0:
            steps = 1 if delta > 0 else -1
        value = self.scrollbar.value() - steps
        value = max(self.scrollbar.minimum(), min(value, self.scrollbar.maximum()))
        self.scrollbar.setValue(value)
        event.accept()

    def resizeEvent(self,event):
        super().resizeEvent(event)
        self._update_vertical_scrollbar()
    
def load_config(config_file, file_name):
    namespace = {
        "FST_Wave_View_Model": FST_Wave_View_Model,
        "file_name"          : file_name          ,
    }

    namespace = runpy.run_path(config_file, init_globals=namespace)

    viewer = namespace["viewer"]

    if viewer is None:
        raise RuntimeError(f"{config_file} does not define 'viewer'")

    return viewer

def main():

    if len(sys.argv) != 3:
        print(
            f"Usage: {sys.argv[0]} "
            f"CONFIG.py FILE.fst"
        )
        return 1

    config_file = sys.argv[1]
    file_name   = sys.argv[2]

    viewer = load_config(config_file, file_name)

    viewer.rebuild()
    viewer.load_wave()

    app = QApplication(sys.argv)

    window = WaveformWindow(viewer)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
