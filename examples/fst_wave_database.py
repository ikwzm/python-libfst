#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-2-Clause
# Copyright (c) 2026 ikwzm

from bisect import bisect_right

class FST_Wave_DataBase:

    class Wave_Signal:

        def __init__(self, handle):
            self.handle     = handle
            self.ref_count  = 1
            self.start_time = None
            self.end_time   = None
            self.time_list  = []
            self.value_list = []

        def clear(self):
            self.ref_count  = 0
            self.start_time = None
            self.end_time   = None
            self.time_list.clear()
            self.value_list.clear()

        def inc_ref_count(self):
            self.ref_count += 1
            return self.ref_count

        def dec_ref_count(self):
            if self.ref_count > 0:
                self.ref_count -= 1
            return self.ref_count
        
        def append(self, time, value):
            self.time_list.append(time)
            self.value_list.append(value)

            if self.start_time is None:
                self.start_time = time

            self.end_time = time

        def is_loaded(self, start_time, end_time):
            if self.start_time is None:
                return False
            return ((start_time >= self.start_time) and (end_time <= self.end_time))
        
        def get(self, start_time, end_time):
            if not self.time_list:
                return []

            # lo_pos  : start_time 以下の最後の変化位置
            lo_pos = bisect_right(self.time_list, start_time)
            if lo_pos > 0:
                lo_pos = lo_pos -1
            else:
                lo_pos = 0
            
            # hi_pos : end_time より大きい最初の位置
            hi_pos = bisect_right(self.time_list, end_time  ) 

            # start_time 〜 end_time の変化を示すイタレータを返す
            return (
                (self.time_list[i], self.value_list[i])
                for i in range(lo_pos, hi_pos)
            )

    def __init__(self, fst_reader):
        self.fst_reader   = fst_reader
        self.wave_signals = {}

    def register_handle(self, handle):
        wave_signal = self.wave_signals.get(handle)
        if wave_signal is None:
            self.wave_signals[handle] = self.Wave_Signal(handle)
        else:
            self.wave_signals[handle].inc_ref_count()

    def unregister_handle(self, handle):
        wave_signal = self.wave_signals.get(handle)
        if wave_signal is None:
            return
        ref_count = wave_signal.dec_ref_count()
        if ref_count == 0:
            del self.wave_signals[handle]

    def clear_wave_signals(self, wave_signals=None):
        if wave_signals is None:
            wave_signals = self.wave_signals

        for wave_signal in wave_signals.values():
            wave_signal.clear()

    def load_wave_signals(self, start_time, end_time, wave_signals=None):
        if wave_signals is None:
            wave_signals = self.wave_signals

        require_load = {}
        for handle, wave_signal in wave_signals.items():
            if wave_signal.is_loaded(start_time, end_time):
                continue
            require_load[handle] = wave_signal

        if not require_load:
            return

        self.fst_reader.clear_facility_process_mask_all()
        for handle, wave_signal in require_load.items():
            wave_signal.clear()
            self.fst_reader.set_facility_process_mask(handle)

        self.fst_reader.set_limit_time_range(start_time, end_time)

        for time, handle, value in self.fst_reader.blocks():
            wave_signal = require_load.get(handle)
            if wave_signal is not None:
                wave_signal.append(time, value)

    def get(self, handle, start_time, end_time):
        wave_signal = self.wave_signals.get(handle)

        if wave_signal is None:
            return []

        if not wave_signal.is_loaded(start_time, end_time):
            self.load_wave_signals(start_time, end_time, {handle: wave_signal})
            
        return wave_signal.get(start_time, end_time)

