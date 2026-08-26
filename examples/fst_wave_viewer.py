#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-2-Clause
# Copyright (c) 2026 ikwzm

import sys
import runpy
import argparse

from PySide6.QtCore    import Qt
from PySide6.QtCore    import QAbstractTableModel, QModelIndex
from PySide6.QtCore    import QRect, QTimer, Signal, QPoint
from PySide6.QtGui     import QPainter, QPen, QColor, QPalette, QAction
from PySide6.QtWidgets import (
    QApplication,
    QTableView,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QScrollBar,
    QHeaderView,
    QLabel,
    QMenu,
)
from fst_wave_view_model import FST_Wave_View_Model

APPLICATION_INFO = {
    "Version"           : "0.5.1",
    "Author"            : "Ichiro Kawazome",
    "Author_Email"      : "ichiro_k@ca2-so-net.ne.jp",
    "License"           : "BSD 2-Clause",
    "Description"       : "FST Waveform Viewer",
}

DEFAULT_VALUES = {
    "header_height"     :  24,
    "signal_height"     :  24,
    "footer_height"     :  20,
    "signal_name_width" : 300,
    "signal_value_width": 300,
    "scrollbar_width"   :  24,
    "display_row_count" :  25,
}

class WaveformSignals(QWidget):
    "View_List クラスで指定されている各信号の名称、値、波形を表示するエリア"
    " このエリアは次の４つのエリアを横に並べている"
    "   * SignalNameColumn     : 信号の名称を表示するエリア"
    "   * SignalValueColumn    : 信号の値を表示するエリア"
    "   * SignalWaveformColumn : 信号の波形を表示するエリア"
    "   * SignalScrollBar      : 信号を選択するためのスクロールバー"
    def __init__(self, view_list, parent=None):
        super().__init__(parent)
        self.parent                 = parent
        self.view_list              = view_list
        self.time_controller        = self.parent.time_controller
        self.signal_row_height      = self.view_list.get_option("signal_height",
                                                                self.parent.signal_row_height)
        self.signal_name_width      = self.parent.signal_name_width
        self.signal_value_width     = self.parent.signal_value_width
        self.signal_scrollbar_width = self.parent.signal_scrollbar_width
        self.visible_row_count      = self.parent.visible_row_count

        self.signal_name_column     = self.SignalNameColumn(self)
        self.signal_value_column    = self.SignalValueColumn(self)
        self.signal_waveform_column = self.SignalWaveformColumn(self)
        self.signal_scrollbar       = self.SignalScrollBar(self)

        self.signal_name_column.setFixedWidth(self.signal_name_width)
        self.signal_value_column.setFixedWidth(self.signal_value_width)
        self.signal_scrollbar.setFixedWidth(self.signal_scrollbar_width)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self.signal_name_column)
        layout.addWidget(self.signal_value_column)
        layout.addWidget(self.signal_waveform_column, 1)
        layout.addWidget(self.signal_scrollbar)

        self.signal_name_column.view_list_changed.connect(self._view_list_changed)
        self.signal_scrollbar.valueChanged.connect(self._signal_scrollbar_value_changed)

        # 注) すぐに self.signal_name_column の描画領域(viewport)の設定が行われるとは限ら
        # ないので、ここで self.update_visible_row_count() を実行するのではなく、
        # 現在実行中の処理がすべて終了してから self.update_visible_row_count() を実行する.
        # これは self.resizeEvent() の実行中でも同様
        # self.update_visible_row_count()
        QTimer.singleShot(0, self.update_visible_row_count)

    def update_signal_scrollbar(self):
        self.signal_scrollbar.update_scroll_range()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(0, self.update_visible_row_count)

    def _view_list_changed(self):
        self.update_visible_row_count()
        self.signal_name_column.refresh()
        self.signal_value_column.refresh()
        self.signal_waveform_column.refresh()

    def _signal_scrollbar_value_changed(self, value):
        self.set_row_scroll_value(value)

    def update_visible_row_count(self):
        height    = self.signal_name_column.viewport().height()
        row_count = height // self.signal_row_height
        self.signal_name_column.set_visible_row_count(row_count)
        self.signal_value_column.set_visible_row_count(row_count)
        self.signal_waveform_column.set_visible_row_count(row_count)
        self.signal_scrollbar.set_visible_row_count(row_count)

    def set_row_scroll_value(self, value):
        self.signal_name_column.set_row_scroll_value(value)
        self.signal_value_column.set_row_scroll_value(value)
        self.signal_waveform_column.set_row_scroll_value(value)

    def set_time_range(self, start_time, end_time):
        self.signal_name_column.set_time_range(start_time, end_time)
        self.signal_value_column.set_time_range(start_time, end_time)
        self.signal_waveform_column.set_time_range(start_time, end_time)
        
    def set_current_time(self, current_time):
        self.signal_value_column.set_current_time(current_time)
        self.signal_waveform_column.set_current_time(current_time)

    def scroll_rows(self, delta):
        scrollbar = self.signal_scrollbar
        value     = scrollbar.value() + delta
        value     = max(scrollbar.minimum(), min(scrollbar.maximum(), value))
        scrollbar.setValue(value)

    class SignalNameColumn(QTableView):
        "View_List クラスで指定されている各信号の名称を表示するクラス"
        
        view_list_changed = Signal()

        def __init__(self, parent=None):
            super().__init__(parent)
            self.parent       = parent
            self.view_list    = self.parent.view_list
            self.row_height   = self.parent.signal_row_height
            self.table_model  = self.SignalNameModel(self)
            self.setModel(self.table_model)

            self.setSelectionBehavior(QTableView.SelectRows)
            self.setSelectionMode(QTableView.SingleSelection)

            h_header = self.horizontalHeader()
            h_header.setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch)
            h_header.setVisible(False)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            
            v_header = self.verticalHeader()
            v_header.setVisible(False)
            v_header.setSectionResizeMode(QHeaderView.Fixed)
            v_header.setDefaultSectionSize(self.row_height)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        def mouseDoubleClickEvent(self, event):
            index = self.indexAt(event.position().toPoint())

            if index.isValid():
                row  = index.row()
                item = self.view_list.row_to_item(row)

                if self.view_list.item_is_group(item):
                    self.view_list.toggle_group(item)

                    self.table_model.refresh()

                    new_row = self.view_list.item_to_row(item)
                    if new_row is not None:
                        new_index = self.table_model.index(
                            new_row,
                            self.SignalNameModel.SIGNAL_COLUMN
                        )
                        self.scrollTo(new_index)

                    self.view_list_changed.emit()
                    event.accept()
                    return

            super().mouseDoubleClickEvent(event)

        def wheelEvent(self, event):
            delta_y = event.angleDelta().y()
            if   delta_y > 0:
                self.parent.scroll_rows(-1)
            elif delta_y < 0:
                self.parent.scroll_rows( 1)
            event.accept()

        def refresh(self):
            self.view_list.rebuild()
            self.table_model.refresh()

        def set_visible_row_count(self, value):
            pass

        def set_time_range(self, start_time, end_time):
            pass
        
        def set_row_scroll_value(self, value):
            scrollbar = self.verticalScrollBar()
            if scrollbar.value() != value:
                scrollbar.setValue(value)

        class SignalNameModel(QAbstractTableModel):
            SIGNAL_COLUMN = 0
            COLUMN_COUNT  = 1

            def __init__(self, parent=None):
                super().__init__(parent)
                self.view_list = parent.view_list

            def columnCount(self, parent=QModelIndex()):
                return self.COLUMN_COUNT

            def rowCount(self, parent=QModelIndex()):
                return self.view_list.row_count()

            def flags(self, index):
                return Qt.ItemIsSelectable | Qt.ItemIsEnabled
            
            def data(self, index, role=Qt.DisplayRole):
                if not index.isValid():
                    return None

                item = self.view_list.row_to_item(index.row())
                if item is None:
                    return None

                if role == Qt.DisplayRole:
                    if index.column() == self.SIGNAL_COLUMN:
                        if self.view_list.item_is_group(item):
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
                        color = item.signal_name_background_color
                        if color is not None:
                            return QColor(color)
            
                if role == Qt.ForegroundRole:
                    if index.column() == self.SIGNAL_COLUMN:
                        color = item.signal_name_color
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

    class SignalValueColumn(QTableView):
        "View_List クラスで指定されている各信号の値を表示するクラス"

        def __init__(self, parent=None):
            super().__init__(parent)
            self.parent          = parent
            self.view_list       = self.parent.view_list
            self.time_controller = self.parent.time_controller
            self.row_height      = self.parent.signal_row_height
            self.table_model     = self.SignalValueModel(self)
            self.setModel(self.table_model)

            self.setSelectionBehavior(QTableView.SelectRows)
            self.setSelectionMode(QTableView.SingleSelection)

            h_header = self.horizontalHeader()
            h_header.setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch)
            h_header.setVisible(False)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            
            v_header = self.verticalHeader()
            v_header.setVisible(False)
            v_header.setSectionResizeMode(QHeaderView.Fixed)
            v_header.setDefaultSectionSize(self.row_height)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        def refresh(self):
            self.table_model.refresh()

        def set_visible_row_count(self, value):
            pass

        def set_time_range(self, start_time, end_time):
            pass

        def set_row_scroll_value(self, value):
            scrollbar = self.verticalScrollBar()
            if scrollbar.value() != value:
                scrollbar.setValue(value)

        def set_current_time(self, current_time):
            self.table_model.set_current_time(current_time)
        
        def wheelEvent(self, event):
            delta_y = event.angleDelta().y()
            if   delta_y > 0:
                self.parent.scroll_rows(-1)
            elif delta_y < 0:
                self.parent.scroll_rows( 1)
            event.accept()

        class SignalValueModel(QAbstractTableModel):
            VALUE_COLUMN  = 0
            COLUMN_COUNT  = 1

            def __init__(self, parent=None):
                super().__init__(parent)
                self.view_list       = parent.view_list
                self.time_controller = parent.time_controller
                self.current_time    = self.time_controller.current_time

            def columnCount(self, parent=QModelIndex()):
                return self.COLUMN_COUNT

            def rowCount(self, parent=QModelIndex()):
                return self.view_list.row_count()

            def flags(self, index):
                return Qt.ItemIsSelectable | Qt.ItemIsEnabled
            
            def data(self, index, role=Qt.DisplayRole):
                if not index.isValid():
                    return None

                item = self.view_list.row_to_item(index.row())
                if item is None:
                    return None

                if role == Qt.DisplayRole:
                    if index.column() == self.VALUE_COLUMN:
                        if self.view_list.item_is_signal(item):
                            return self._get_value(item)
                        else:
                            return ""

                if role == Qt.BackgroundRole:
                    if index.column() == self.VALUE_COLUMN:
                        color = item.signal_value_background_color
                        if color is not None:
                            return QColor(color)
            
                if role == Qt.ForegroundRole:
                    if index.column() == self.VALUE_COLUMN:
                        color = item.signal_value_color
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
                if self.current_time != current_time:
                    self.current_time = current_time
                    self.refresh()

    class SignalWaveformColumn(QWidget):
        "View_List クラスで指定されている各信号の波形をするクラス"
        " このアプリケーションのメイン部分"
        def __init__(self, parent=None):
            super().__init__(parent)
            self.parent             = parent
            self.view_list          = self.parent.view_list
            self.time_controller    = self.parent.time_controller
            self.start_time         = self.time_controller.start_time
            self.end_time           = self.time_controller.end_time
            self.visible_row_count  = self.parent.visible_row_count
            self.row_scroll_value   = 0
            self.background_color   = self.view_list.background_color

        def refresh(self):
            self.update()

        def set_time_range(self, start_time, end_time):
            if start_time == self.start_time and end_time == self.end_time:
                return
            self.start_time = start_time
            self.end_time   = end_time
            self.update()

        def set_current_time(self, current_time):
            pass

        def set_visible_row_count(self, value):
            if self.visible_row_count == value:
                return
            self.visible_row_count = value
            self.update()

        def set_row_scroll_value(self, value):
            if self.row_scroll_value == value:
                return
            self.row_scroll_value = value
            self.update()

        def time_to_x(self, time):
            start_time = self.time_controller.start_time
            end_time   = self.time_controller.end_time
            if end_time == start_time:
                return 0
            return int((time - start_time) * self.width() / (end_time - start_time))

        def x_to_time(self, x):
            start_time = self.time_controller.start_time
            end_time   = self.time_controller.end_time
            if self.width() <= 0:
                return start_time
            x = max(0, min(self.width(), x))
            ratio = x / self.width()
            return int(start_time + ratio * (end_time - start_time))
        
        def paintEvent(self, event):
            painter      = QPainter(self)
            start_time   = self.time_controller.start_time
            end_time     = self.time_controller.end_time

            painter.fillRect(self.rect(), self.background_color)
            if end_time <= start_time:
                return
            
            width        = self.width()
            height       = self.height()
            row_height   = self.parent.signal_row_height
            first_row    = self.row_scroll_value
            row_count    = self.view_list.row_count()
            edge_slope   = self.view_list.model.get_option("edge_slope", 0)
            visible_rows = self.visible_row_count

            def draw_background():
                for i in range(visible_rows):
                    row   = first_row + i
                    if row >= row_count:
                        break
                    y     = i * row_height
                    rect  = QRect(0, y, width, row_height)
                    item  = self.view_list.row_to_item(row)
                    color = item.wave_background_color
                    if color is not None:
                        painter.fillRect(rect, QColor(color))

            def draw_group(group, y):
                top    = y + 5
                bottom = y + row_height - 5
                height = bottom - top
                rect   = QRect(0, top, width, height)
                color  = group.wave_group_color
                if color is not None:
                    painter.fillRect(rect, QColor(color))
                
            def draw_signal(signal, y):
                top    = y + 5
                bottom = y + row_height - 5
                height = bottom - top

                edge_slope_width     = edge_slope
                edge_slope_threshold = edge_slope_width*3
                edge_slope_enabled   = (edge_slope_width != 0)

                def draw_signal_value(signal, value, left, width):
                    value_text   = str(signal.format_value(value))
                    painter.setPen(QPen(QColor(signal.wave_value_color)))
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
                    nonlocal edge_slope_enabled
                    width = right - left
                    pen   = QPen(QColor(signal.wave_signal_color))
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
                    if curr_value != prev_value and edge_slope_enabled and width > edge_slope_threshold:
                        draw_left  = left + edge_slope_width
                        painter.drawLine(left     , prev_level, draw_left, curr_level)
                        painter.drawLine(draw_left, curr_level, right    , curr_level)
                    else:
                        painter.drawLine(left     , prev_level, left     , curr_level)
                        painter.drawLine(left     , curr_level, right    , curr_level)
                        edge_slope_enabled = ((edge_slope_width == 0) and (width > edge_slope_threshold))
                        
                def draw_signal_bus(signal, curr_value, prev_value, left, right):
                    width            = right - left
                    background_color = signal.wave_background_color
                    signal_pen       = QPen(QColor(signal.wave_signal_color))
                    if curr_value != prev_value and edge_slope_enabled and width > edge_slope_threshold:
                        draw_left  = left  + edge_slope_width
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
                    item  = self.view_list.row_to_item(row)
                    if self.view_list.item_is_group(item):
                        draw_group(item, y)
                        continue
                    if self.view_list.item_is_signal(item):
                        draw_signal(item, y)
                        continue
                    if self.view_list.item_is_clock(item):
                        draw_signal(item, y)
                        continue

            def draw_simple_grid(tick_count):
                time_range = end_time - start_time
                tick_step  = time_range / tick_count
                pen = QPen(Qt.gray)
                pen.setStyle(Qt.DashLine)
                pen.setWidth(1)
                painter.setPen(pen)
                for i in range(tick_count + 1):
                    time = start_time + i * tick_step
                    x = self.time_to_x(time)
                    painter.drawLine(x, 0, x, height)

            def draw_clock_grid(clock):
                pen = QPen(Qt.gray)
                pen.setStyle(Qt.DashLine)
                pen.setWidth(1)
                painter.setPen(pen)
                prev_x = 0
                for time in clock.get_edges(start_time, end_time):
                    if time > end_time:
                        break
                    curr_x = self.time_to_x(time)
                    if curr_x - prev_x > 10:
                        painter.drawLine(curr_x, 0, curr_x, height)
                        prev_x = curr_x

            def draw_grid():
                if self.view_list.clock is not None:
                    draw_clock_grid(self.view_list.clock)
                else:
                    draw_simple_grid(10)

            draw_background()
            draw_grid()
            draw_foreground()

    class SignalScrollBar(QScrollBar):
        "View_List クラスで指定されている信号群から表示する信号を選択するためのスクロールバー"
        def __init__(self, parent=None):
            super().__init__(Qt.Vertical, parent)
            self.parent            = parent
            self.view_list         = self.parent.view_list
            self.visible_row_count = 0

        def set_visible_row_count(self, value):
            self.visible_row_count = value
            self.update_scroll_range()

        def update_scroll_range(self):
            total_rows = self.view_list.row_count()
            maximum    = max(0, total_rows - self.visible_row_count)
            self.setMinimum(0)
            self.setMaximum(maximum)
            self.setPageStep(self.visible_row_count)
            self.setSingleStep(1)

class WaveformArea(QWidget):
    "アプリケーションウィンドウの波形表示部"
    " このエリアは次の３つのエリアを重ねている"
    "   * WaveformSignals : View_List クラスで指定されている各信号の名称、値、波形を表示するエリア"
    "   * MarkerWidget    : マーカーを描画するための Widget"
    "   * CursorWidget    : カーソルを描画するための Widget"
    def __init__(self, view_model, parent=None):
        super().__init__(parent)
        self.parent                 = parent
        self.view_model             = view_model
        self.time_controller        = self.parent.time_controller
        self.signal_name_width      = self.parent.signal_name_width
        self.signal_value_width     = self.parent.signal_value_width
        self.signal_scrollbar_width = self.parent.signal_scrollbar_width
        self.visible_row_count      = self.parent.visible_row_count
        self.signal_row_height      = self.parent.signal_row_height
        self.waveform_list          = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        for view_list in self.view_model.view_lists():
            waveform = WaveformSignals(view_list, self)
            self.waveform_list.append(waveform)
            layout.addWidget(waveform, 0)

        self.marker_widget = self.MarkerWidget(self)
        self.marker_widget.show()
        self.marker_widget.raise_()
        self.cursor_widget = self.CursorWidget(self)
        self.cursor_widget.show()
        self.cursor_widget.raise_()
        QTimer.singleShot(0, self.update_cursor_geometry)

    def update_cursor_geometry(self):
        if not self.waveform_list:
            self.cursor_widget.hide()
            return
        first_waveform = (self.waveform_list[ 0].signal_waveform_column)
        last_waveform  = (self.waveform_list[-1].signal_waveform_column)
        top_left       = first_waveform.mapTo(self, QPoint(0,0))
        bottom_right   = last_waveform.mapTo( self, QPoint(last_waveform.width(),last_waveform.height()))
        rect           = QRect(top_left, bottom_right)
        self.marker_widget.setGeometry(rect)
        self.marker_widget.raise_()
        self.marker_widget.show()
        self.cursor_widget.setGeometry(rect)
        self.cursor_widget.raise_()
        self.cursor_widget.show()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_cursor_geometry()

    def set_time_range(self, start_time, end_time):
        for view_list in self.waveform_list:
            view_list.set_time_range(start_time, end_time)
        self.marker_widget.set_time_range(start_time, end_time)
        self.cursor_widget.set_time_range(start_time, end_time)

    def set_current_time(self, current_time):
        for view_list in self.waveform_list:
            view_list.set_current_time(current_time)
        self.marker_widget.set_current_time(current_time)
        self.cursor_widget.set_current_time(current_time)

    class MarkerWidget(QWidget):
        "マーカーを描画するための Widget"
        " current_time で指定された時間の所にマーカー(縦線)を描く"
        def __init__(self, parent=None):
            super().__init__(parent)
            self.parent          = parent
            self.view_model      = self.parent.view_model
            self.time_controller = self.parent.time_controller
            self.start_time      = self.parent.time_controller.start_time
            self.end_time        = self.parent.time_controller.end_time
            self.current_time    = None
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setMouseTracking(False)

            self.color = self.view_model.get_color("marker")
            self.pen   = QPen(QColor(self.color))
            self.pen.setWidth(1)

        def set_time_range(self, start_time, end_time):
            if start_time == self.start_time and end_time == self.end_time:
                return
            self.start_time = start_time
            self.end_time   = end_time
            self.update()
        
        def set_current_time(self, current_time):
            if current_time == self.current_time:
                return
            self.current_time = current_time
            self.update()

        def time_to_x(self, time):
            if self.end_time == self.start_time:
                return 0
            return int((time - self.start_time) * self.width() / (self.end_time - self.start_time))

        def paintEvent(self, event):
            if self.current_time is None:
                return
            if self.current_time < self.start_time:
                return
            if self.current_time > self.end_time:
                return
            current_x = self.time_to_x(self.current_time)
            painter = QPainter(self)
            painter.setPen(self.pen)
            painter.drawLine(
               current_x, 0,
               current_x, self.height()
            )
        
    class CursorWidget(QWidget):
        "カーソルを描画するための Widget"
        " マウスの左右移動でカーソル(縦線)を左右に移動"
        " マウスの上下スクロールで表示する信号をスクロール"
        " マウスの左クリックで current_time を指定"
        " マウスの右クリックでメニューポップアップ(表示している時間範囲を変更)"
        def __init__(self, parent=None):
            super().__init__(parent)
            self.parent          = parent
            self.view_model      = self.parent.view_model
            self.time_controller = self.parent.time_controller
            self.start_time      = self.parent.time_controller.start_time
            self.end_time        = self.parent.time_controller.end_time
            self.marker_time     = None
            self.cursor_x        = None
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setMouseTracking(True)

            self.color = self.view_model.get_color("cursor")
            self.pen   = QPen(QColor(self.color))
            self.pen.setWidth(1)

            self.menu               = QMenu(self)
            self.center_action      = QAction("Center on Cursor"       , self.menu)
            self.goto_marker_action = QAction("Go to Marker"           , self.menu)
            self.zoom_marker_action = QAction("Zoom Marker-Cursor"     , self.menu)
            self.zoom_in_action     = QAction("Zoom to 200% at Cursor" , self.menu)
            self.zoom_out_action    = QAction("Zoom to 50%  at Cursor" , self.menu)
            self.zoom_all_action    = QAction("Zoom All"               , self.menu)
            self.menu.addAction(self.center_action)
            self.menu.addAction(self.goto_marker_action)
            self.menu.addSeparator()
            self.menu.addAction(self.zoom_marker_action)
            self.menu.addAction(self.zoom_in_action)
            self.menu.addAction(self.zoom_out_action)
            self.menu.addAction(self.zoom_all_action)

        def set_time_range(self, start_time, end_time):
            if start_time == self.start_time and end_time == self.end_time:
                return
            self.start_time = start_time
            self.end_time   = end_time
            self.update()
        
        def set_current_time(self, current_time):
            if current_time == self.marker_time:
                return
            self.marker_time = current_time

        def set_cursor_x(self, x):
            if x == self.cursor_x:
                return
            self.cursor_x = x
            self.update()

        def time_to_x(self, time):
            if self.end_time == self.start_time:
                return 0
            return int((time - self.start_time) * self.width() / (self.end_time - self.start_time))

        def paintEvent(self, event):
            if self.cursor_x is None:
                return
            painter = QPainter(self)
            painter.setPen(self.pen)
            painter.drawLine(
                self.cursor_x, 0,
                self.cursor_x, self.height()
            )

        def mouseMoveEvent(self, event):
            x = int(event.position().x())
            self.set_cursor_x(x)

        def mousePressEvent(self, event):
            if event.button() == Qt.LeftButton:
                self.change_current_time_event(event)
                event.accept()
                return
            if event.button() == Qt.RightButton:
                self.show_menu_event(event)
                event.accept()
                return
            event.ignore()

        def wheelEvent(self, event):
            waveform = self.get_waveform_at(event.position())
            if waveform is None:
                event.ignore()
                return
            delta_y = event.angleDelta().y()
            if   delta_y > 0:
                waveform.scroll_rows(-1)
            elif delta_y < 0:
                waveform.scroll_rows( 1)
            event.accept()

        def get_waveform_at(self, pos):
            area_pos = self.mapToParent(pos.toPoint())
            for waveform in self.parent.waveform_list:
                column   = waveform.signal_waveform_column
                top_left = column.mapTo(self.parent, QPoint(0, 0))
                rect     = QRect(top_left, column.size())
                if rect.contains(area_pos):
                    return waveform
            return None

        def change_current_time_event(self, event):
            pos = event.position().toPoint()
            waveform = self.get_waveform_at(event.position())
            if waveform is None:
                return
            global_pos      = self.mapToGlobal(pos)
            waveform_column = waveform.signal_waveform_column
            waveform_pos    = waveform_column.mapFromGlobal(global_pos)
            current_time    = waveform_column.x_to_time(waveform_pos.x())
            self.time_controller.change_current_time(current_time)

        def show_menu_event(self, event):
            pos = event.position().toPoint()
            waveform = self.get_waveform_at(event.position())
            if waveform is None:
                return
            global_pos      = self.mapToGlobal(pos)
            waveform_column = waveform.signal_waveform_column
            waveform_pos    = waveform_column.mapFromGlobal(global_pos)
            cursor_time     = waveform_column.x_to_time(waveform_pos.x())
            action          = self.menu.exec(self.mapToGlobal(pos))
            if   action == self.center_action:
                self.goto_center(cursor_time)
            elif action == self.goto_marker_action:
                self.goto_marker(cursor_time)
            elif action == self.zoom_marker_action:
                self.zoom_marker(cursor_time)
            elif action == self.zoom_in_action:
                self.zoom_in(cursor_time)
            elif action == self.zoom_out_action:
                self.zoom_out(cursor_time)
            elif action == self.zoom_all_action:
                self.zoom_all(cursor_time)

        def goto_center(self, cursor_time):
            self.center_on_time(cursor_time)

        def goto_marker(self, cursor_time):
            if self.marker_time is None:
                return
            self.center_on_time(self.marker_time)

        def zoom_marker(self, cursor_time):
            if self.marker_time is None:
                return
            if cursor_time < self.marker_time:
                new_start_time = cursor_time
                new_end_time   = self.marker_time
            else:
                new_start_time = self.marker_time
                new_end_time   = cursor_time
            self.time_controller.change_time_range(new_start_time, new_end_time)

        def zoom_in(self, center_time):
            time_range = self.end_time - self.start_time
            if time_range <= 1:
                return
            new_range  = max(1, time_range // 2)
            self.center_on_time(center_time, new_range)

        def zoom_out(self, center_time):
            time_range = self.end_time - self.start_time
            new_range  = time_range * 2
            self.center_on_time(center_time, new_range)

        def zoom_all(self, center_time):
            new_start_time = self.time_controller.total_start_time
            new_end_time   = self.time_controller.total_end_time
            self.time_controller.change_time_range(new_start_time, new_end_time)

        def center_on_time(self, center_time, time_range=None):
            if time_range is None:
                time_range = self.end_time - self.start_time
            new_start_time = int(center_time - time_range // 2)
            new_end_time   = int(center_time + time_range // 2)
            self.time_controller.change_time_range(new_start_time, new_end_time)
            self.set_cursor_x(self.time_to_x(center_time))


class HeaderArea(QWidget):
    "アプリケーションウィンドウのヘッダ部"
    " このエリアは次の３つのエリアを横に並べている"
    "   * QLabel('Signal Name')  : 'Signal Name' ラベル"
    "   * QLabel('Signal Value') : 'Signal Value' ラベル"
    "   * TimeRuler              : 現在表示している時間範囲を表示する Widget"
    def __init__(self, view_model, parent=None):
        super().__init__(parent)
        self.parent                 = parent
        self.view_model             = view_model
        self.time_controller        = self.parent.time_controller
        self.signal_name_width      = self.parent.signal_name_width
        self.signal_value_width     = self.parent.signal_value_width
        self.signal_scrollbar_width = self.parent.signal_scrollbar_width
        self.height                 = self.view_model.get_option("header_height",
                                      DEFAULT_VALUES["header_height"])
        self.signal_name_column     = QLabel("Signal Name", self)
        self.signal_value_column    = QLabel("Value", self)
        self.time_ruler             = self.TimeRuler(self)
        self.padding_space          = QLabel("", self)

        self.signal_name_column.setFixedWidth(self.signal_name_width)
        self.signal_name_column.setFixedHeight(self.height)
        self.signal_name_column.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.signal_value_column.setFixedWidth(self.signal_value_width)
        self.signal_value_column.setFixedHeight(self.height)
        self.signal_value_column.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.time_ruler.setFixedHeight(self.height)

        background_color = self.view_model.get_color("header", "background", "black")
        foreground_color = self.view_model.get_color("header", "foreground", "white")
        for column in (self.signal_name_column, self.signal_value_column):
            column.setAutoFillBackground(True)
            palette = column.palette()
            palette.setColor(QPalette.ColorRole.Window    , QColor(background_color))
            palette.setColor(QPalette.ColorRole.WindowText, QColor(foreground_color))
            column.setPalette(palette)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self.signal_name_column)
        layout.addWidget(self.signal_value_column)
        layout.addWidget(self.time_ruler, 1)

    def set_time_range(self, start_time, end_time):
        self.time_ruler.set_time_range(start_time, end_time)
    
    def set_current_time(self, current_time):
        pass

    class TimeRuler(QWidget):
        "現在表示している時間範囲を表示する Widget"
        def __init__(self, parent=None):
            super().__init__(parent)
            self.parent             = parent
            self.view_model         = self.parent.view_model
            self.time_controller    = self.parent.time_controller
            self.time_quantum       = self.time_controller.time_quantum
            self.start_time         = self.time_controller.start_time
            self.end_time           = self.time_controller.end_time
            self.right_margin_width = self.parent.signal_scrollbar_width
            self.background_color   = self.view_model.get_color("time_ruler", "background", "black")
            self.line_color         = self.view_model.get_color("time_ruler", "line"      , "gray" )
            self.text_color         = self.view_model.get_color("time_ruler", "text"      , "white")
            self.PERIOD_TIME_LIST   = [self.view_model.parse_time("1000 s"),
                                       self.view_model.parse_time("100 s"),
                                       self.view_model.parse_time("10 s"),
                                       self.view_model.parse_time("1 s"),
                                       self.view_model.parse_time("100 ms"),
                                       self.view_model.parse_time("10 ms"),
                                       self.view_model.parse_time("1 ms"),
                                       self.view_model.parse_time("100 us"),
                                       self.view_model.parse_time("10 us"),
                                       self.view_model.parse_time("1 us"),
                                       self.view_model.parse_time("100 ns"),
                                       self.view_model.parse_time("10 ns"),
                                       self.view_model.parse_time("1 ns"),
                                     ]
        def calc_period_time(self, start_time, end_time):
            time_range = end_time - start_time
            for period_time in self.PERIOD_TIME_LIST:
                if (time_range // period_time) >= 1:
                    return period_time
            return self.PERIOD_TIME_LIST[-1]

        def set_time_range(self, start_time, end_time):
            if start_time == self.start_time and end_time == self.end_time:
                return
            self.start_time = start_time
            self.end_time   = end_time
            self.update()

        def time_to_x(self, time):
            width = self.width() - self.right_margin_width
            if self.end_time == self.start_time:
                return 0
            return int((time - self.start_time) * width / (self.end_time - self.start_time))

        def paintEvent(self, event):
            painter = QPainter(self)
            painter.fillRect(self.rect(), QColor(self.background_color))
            height = self.height()
            start_time  = self.start_time
            end_time    = self.end_time
            period_time = self.calc_period_time(start_time, end_time)
            step_time   = period_time // 10
            first_time  = ((start_time                ) // period_time) * period_time
            last_time   = ((end_time + period_time - 1) // period_time) * period_time
            prev_x      = None

            for base_time in range(first_time, last_time, period_time):
                for i in range(10):
                    time   = base_time + i * step_time
                    curr_x = self.time_to_x(time)
                    if prev_x is None:
                        time_width = 0
                    else:
                        time_width = curr_x - prev_x
                    if time >= self.start_time and time <= self.end_time:
                        text = str(self.view_model.format_timestamp(time))
                        painter.setPen(QPen(QColor(self.text_color)))
                        fm = painter.fontMetrics()
                        text_width = fm.horizontalAdvance(text)
                        if i == 0 or text_width <= time_width:
                            painter.drawText(curr_x - text_width // 2, 15, text)
                        painter.setPen(QPen(QColor(self.line_color)))
                        painter.drawLine(curr_x, height - 8, curr_x, height)
                    prev_x = curr_x

class FooterArea(QWidget):
    "アプリケーションウィンドウのフッター部"
    " このエリアは次の４つのエリアを横に並べている"
    "   * SignalNameScrollBar  : Signal Name  用のスクロールバー(但し現在は未実装)"
    "   * SignalValueScrollBar : Signal Value 用のスクロールバー(但し現在は未実装)"
    "   * TimeRangeScrollBar   : 表示する時間範囲を変更するためのスクロールバー"
    "   * QLabel('')           : SignalScrollBar の幅分をパディングするためのダミー Widget"
    def __init__(self, view_model, parent=None):
        super().__init__(parent)
        self.parent                 = parent
        self.view_model             = view_model
        self.time_controller        = self.parent.time_controller
        self.signal_name_width      = self.parent.signal_name_width
        self.signal_value_width     = self.parent.signal_value_width
        self.signal_scrollbar_width = self.parent.signal_scrollbar_width
        self.height                 = self.view_model.get_option("footer_height",
                                      DEFAULT_VALUES["footer_height"])
        self.signal_name_scrollbar  = self.SignalNameScrollBar(self)
        self.signal_value_scrollbar = self.SignalValueScrollBar(self)
        self.time_range_scrollbar   = self.TimeRangeScrollBar(self)
        self.padding_space          = QLabel("", self)

        self.signal_name_scrollbar.setFixedWidth(self.signal_name_width)
        self.signal_name_scrollbar.setFixedHeight(self.height)

        self.signal_value_scrollbar.setFixedWidth(self.signal_value_width)
        self.signal_value_scrollbar.setFixedHeight(self.height)

        self.time_range_scrollbar.setFixedHeight(self.height)

        self.padding_space.setFixedWidth(self.signal_scrollbar_width)
        self.padding_space.setFixedHeight(self.height)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self.signal_name_scrollbar)
        layout.addWidget(self.signal_value_scrollbar)
        layout.addWidget(self.time_range_scrollbar, 1)
        layout.addWidget(self.padding_space)

    def set_time_range(self, start_time, end_time):
        self.time_range_scrollbar.set_time_range(start_time, end_time)

    def change_time_range(self, start_time, end_time):
        self.time_controller.change_time_range(start_time, end_time)

    def set_current_time(self, current_time):
        pass

    class SignalNameScrollBar(QScrollBar):
        "Signal Name  用のスクロールバー(但し現在は未実装)"
        def __init__(self, parent=None):
            super().__init__(Qt.Horizontal, parent)
            self.parent          = parent
            self.view_model      = self.parent.view_model
            self.time_controller = self.parent.time_controller
            
    class SignalValueScrollBar(QScrollBar):
        "Signal Value 用のスクロールバー(但し現在は未実装)"
        def __init__(self, parent=None):
            super().__init__(Qt.Horizontal, parent)
            self.parent          = parent
            self.view_model      = self.parent.view_model
            self.time_controller = self.parent.time_controller
            
    class TimeRangeScrollBar(QScrollBar):
        "表示する時間範囲を変更するためのスクロールバー"
        def __init__(self, parent=None):
            super().__init__(Qt.Horizontal, parent)
            self.parent           = parent
            self.view_model       = self.parent.view_model
            self.time_controller  = self.parent.time_controller
            self.time_quantum     = self.time_controller.time_quantum
            self.start_time       = None
            self.end_time         = None
            self.valueChanged.connect(self.on_value_changed)
            start_time = self.time_controller.start_time
            end_time   = self.time_controller.end_time
            self.set_time_range(start_time, end_time)

        def set_time_range(self, start_time, end_time):
            if start_time == self.start_time and end_time == self.end_time:
                return
            self.start_time   = start_time
            self.end_time     = end_time
            total_start_time  = (self.time_controller.total_start_time) // self.time_quantum
            total_end_time    = (self.time_controller.total_end_time  ) // self.time_quantum
            total_time_range  = total_end_time - total_start_time
            view_start_time   = (self.start_time) // self.time_quantum
            view_end_time     = (self.end_time  ) // self.time_quantum
            view_time_range   = view_end_time - view_start_time
            self.blockSignals(True)
            self.setMinimum(total_start_time)
            self.setMaximum(total_end_time - view_time_range)
            self.setPageStep(view_time_range)
            self.setValue(view_start_time)
            self.blockSignals(False)
            
        def on_value_changed(self, value):
            time_range = self.end_time - self.start_time
            start_time = value * self.time_quantum
            end_time   = start_time + time_range
            self.time_controller.change_time_range(start_time, end_time)

class WaveformWindow(QMainWindow):
    "アプリケーションウィンドウ"
    " アプリケーションウィンドウは次の３つのエリアを縦に並べている"
    "   * HeaderArea   : ヘッダ部   - QLabel('Signal Name'),QLabel('Signal value'),TimeRuler"
    "   * WaveformArea : 波形表示部 - WaveformSignals, MarkerWidget, CursorWidget"
    "   * FooterArea   : フッタ部   - SignalNameScrollBar, SignalValueScrollBar, TimeRangeScrollBar"
    " 他に表示する時間範囲を管理するための TimeController クラスも内包している"
    def __init__(self, view_model, parent=None):
        super().__init__(parent)
        self.view_model      = view_model
        self.time_controller = self.TimeController(self)

        self.setWindowTitle("FST Wave Viewer")
        self.resize(1200, 700)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.signal_name_width      = self.view_model.get_option("signal_name_width" ,
                                      DEFAULT_VALUES["signal_name_width"])
        self.signal_value_width     = self.view_model.get_option("signal_value_width",
                                      DEFAULT_VALUES["signal_value_width"])
        self.signal_row_height      = self.view_model.get_option("signal_height"     ,
                                      DEFAULT_VALUES["signal_height"])
        self.signal_scrollbar_width = DEFAULT_VALUES["scrollbar_width"]
        self.visible_row_count      = self.view_model.get_option("display_rows"      ,
                                      DEFAULT_VALUES["display_row_count"])

        self.header_area            = HeaderArea(self.view_model,self)
        self.signal_waveform_area   = WaveformArea(self.view_model,self)
        self.footer_area            = FooterArea(self.view_model,self)

        layout.addWidget(self.header_area         , 0)
        layout.addWidget(self.signal_waveform_area, 0)
        layout.addWidget(self.footer_area         , 0)

    def set_time_range(self, start_time, end_time):
        self.start_time = start_time
        self.end_time   = end_time
        self.signal_waveform_area.set_time_range(self.start_time, self.end_time)
        self.header_area.set_time_range(self.start_time, self.end_time)
        self.footer_area.set_time_range(self.start_time, self.end_time)

    def set_current_time(self, current_time):
        self.current_time = current_time
        self.signal_waveform_area.set_current_time(self.current_time)
        self.header_area.set_current_time(self.current_time)
        self.footer_area.set_current_time(self.current_time)
        
    class TimeController:
        def __init__(self, parent=None):
            self.parent                 = parent
            self.view_model             = self.parent.view_model
            self.time_quantum           = self.view_model.time_quantum
            self.start_time             = self.align_time(   self.view_model.start_time)
            self.end_time               = self.align_time_up(self.view_model.end_time  )
            self.total_start_time       = self.align_time(   self.view_model.start_time)
            self.total_end_time         = self.align_time_up(self.view_model.end_time  )
            self.current_time           = self.view_model.current_time
            self.change_time_range_busy = False

        def align_time(self, time):
            quantum = self.time_quantum
            return int((time // quantum) * quantum)

        def align_time_up(self, time):
            quantum = self.time_quantum
            return int(((time + quantum - 1) // quantum) * quantum)
        
        def change_time_range(self, start_time, end_time):
            # print("change_time_range(): start")
            if self.change_time_range_busy:
                return

            total_start_time = self.total_start_time
            total_end_time   = self.total_end_time
            time_range = end_time - start_time
            if time_range <= 0:
                # print("change_time_range(): invalid time range")
                return

            self.change_time_range_busy = True
            try:
                if   start_time < total_start_time:
                    start_time = total_start_time
                    end_time   = start_time + time_range
                elif end_time   > total_end_time:
                    end_time   = total_end_time
                    start_time = end_time   - time_range
                start_time = self.align_time(   max(total_start_time, start_time))
                end_time   = self.align_time_up(min(total_end_time  , end_time  ))
                self.start_time = start_time
                self.end_time   = end_time
                # print("change_time_range(): set_time_range() start")
                self.parent.set_time_range(start_time, end_time)
                # print("change_time_range(): set_time_range() done")
                QTimer.singleShot(0, self.change_time_range_finished)
            except Exception:
                self.change_time_range_busy = False
                raise
    
        def change_time_range_finished(self):
            # print("change_time_range_finished")
            self.change_time_range_busy = False

        def change_current_time(self, current_time):
            self.current_time = current_time
            self.parent.set_current_time(current_time)
        
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
    parser = argparse.ArgumentParser(description=APPLICATION_INFO["Description"])
    parser.add_argument("file_name"         , metavar="FILE" , help="Input FST file" )
    parser.add_argument("-C", "--config"    , metavar="FILE" , help="Configuration File")
    parser.add_argument("-S", "--start-time", metavar="TIME", default=None,
                        help="Start Time (default: Simulation timestamp at the beginning of the FST data)")
    parser.add_argument("-E", "--end-time"  , metavar="TIME", default=None,
                        help="End Time (default: Simulation time at the end of the FST data)")

    args = parser.parse_args()

    file_name   = args.file_name
    config_file = args.config

    viewer = load_config(config_file, file_name)

    if args.start_time is not None:
        start_time = viewer.parse_time(args.start_time)
        viewer.set_start_time(start_time)

    if args.end_time is not None:
        end_time   = viewer.parse_time(args.end_time)
        viewer.set_end_time(end_time)

    viewer.rebuild()
    viewer.load_wave()

    app = QApplication(sys.argv)

    window = WaveformWindow(viewer)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
