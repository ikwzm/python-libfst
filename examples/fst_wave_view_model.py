#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-2-Clause
# Copyright (c) 2026 ikwzm

from   fst_reader        import FST_Reader
from   fst_wave_database import FST_Wave_DataBase
import re

class FST_Wave_View_Model:

    class View_Item:
        def __init__(self, view_list, parent_group, option=None):
            self.view_list    = view_list
            self.model        = self.view_list.model
            self.parent_group = parent_group
            if parent_group is not None:
                self.option   = self.model.merge_option(option,
                                self.model.merge_option(parent_group.child_option,
                                                        self.DEFAULT_OPTION))
                self.depth    = parent_group.depth + 1
            else:
                self.option   = self.model.merge_option(option, self.DEFAULT_OPTION)
                self.depth    = 0
            self.color_option = self.option["color"]

            # Colors for SignalNameColumn
            self.signal_name_color             = self.get_color("name" , "foreground")
            self.signal_name_background_color  = self.get_color("name" , "background")

            # Colors for SignalValueColumn
            self.signal_value_color            = self.get_color("value", "foreground")
            self.signal_value_background_color = self.get_color("value", "background")

            # Colors for SignalWaveformColumn
            self.wave_group_color              = self.get_color("wave" , "group"     )
            self.wave_signal_color             = self.get_color("wave" , "signal"    )
            self.wave_value_color              = self.get_color("wave" , "value"     )
            self.wave_background_color         = self.get_color("wave" , "background")
            
        def get_color(self, key, prop):
            return self.color_option.get(key,{}).get(prop)

    class View_Signal(View_Item):
        DEFAULT_OPTION = {
            "display_name"    : None ,
            "value_format"    : None ,
        }
        VALUE_FORMAT_RE = re.compile(
            r"^(?P<alternate>\#?)"
            r"(?P<zero>0?)"
            r"(?P<width>\d*)"
            r"(?P<type>[bBoOxXd])"
            r"(?P<suffix>.*)$"
        )
        def __init__(self, view_list, path, node, parent_group, option=None):
            super().__init__(view_list, parent_group, option)
            self.path         = path
            self.node         = node
            self.name         = node["name"]
            self.handle       = node["handle"]
            self.width        = node["width"]
            self.registered   = False
            self.closed       = False
            self.display_name = self.option["display_name"] or self.name
            self.is_logic     = self.width == 1 and not self.name.endswith("]")
            self.value_type   = None
            for attribute in node.get("attributes"):
                attr_type = attribute.get("type")
                sub_type  = attribute.get("subtype")
                if attr_type == "MISC" and sub_type == "SUPVAR":
                    data_type = attribute.get("data_type")
                    if data_type in ("SDT_VHDL_BOOLEAN"          ,
                                     "SDT_VHDL_BIT"              ,
                                     "SDT_VHDL_BIT_VECTOR"       ,
                                     "SDT_VHDL_STD_ULOGIC"       ,
                                     "SDT_VHDL_STD_ULOGIC_VECTOR",
                                     "SDT_VHDL_STD_LOGIC"        ,
                                     "SDT_VHDL_STD_LOGIC_VECTOR" ,
                                     "SDT_VHDL_UNSIGNED"         ,
                                     "SDT_VHDL_SIGNED"           ,
                                     "SDT_VHDL_INTEGER"          ,
                                     "SDT_VHDL_REAL"             ,
                                     "SDT_VHDL_NATURAL"          ,
                                     "SDT_VHDL_POSITIVE"         ,
                                     "SDT_VHDL_CHARACTER"        ,
                                     "SDT_VHDL_STRING"           ):
                        self.value_type = data_type[4:]
                    else:
                        self.value_type = None
                    break
                if attr_type == "ENUM":
                    if sub_type in ("SV_INTEGER" , "SV_UNSIGNED_INTEGER" ,
                                    "SV_BIT"     , "SV_UNSIGNED_BIT"     ,
                                    "SV_LOGIC"   , "SV_UNSIGNED_LOGIC"   ,
                                    "SV_INT"     , "SV_UNSIGNED_INT"     ,
                                    "SV_SHORTINT", "SV_UNSIGNED_SHORTINT",
                                    "SV_LONGINT" , "SV_UNSIGNED_LONGINT" ,
                                    "SV_BYTE"    , "SV_UNSIGNED_BYTE"    ):
                        self.value_type = sub_type
                    else:
                        self.value_type = None
                    break
            self.value_format = self.option["value_format"]
            if self.value_format is None:
                if self.width % 4 == 0:
                    self.value_format = f"#0{self.width // 4}x"
                else:
                    self.value_format = "b"
            match = self.VALUE_FORMAT_RE.fullmatch(self.value_format)
            if match is None:
                raise ValueError(f"Invalid format: {self.value_format!r}")
            self.value_format_alternate = bool(match.group("alternate"))
            self.value_format_zero      = bool(match.group("zero"))
            self.value_format_width     = int(match.group("width")) if match.group("width") else None
            self.value_format_type      = match.group("type")
            self.value_format_suffix    = match.group("suffix")
            if not self.value_format_alternate:
                self.value_format_prefix = ""
            elif self.value_format_type == "b":
                self.value_format_prefix = "0b"
            elif self.value_format_type == "o":
                self.value_format_prefix = "0o"
            elif self.value_format_type == "x":
                self.value_format_prefix = "0x"
            elif self.value_format_type == "X":
                self.value_format_prefix = "0X"
            else:
                self.value_format_prefix = ""

        def close(self):
            if self.closed is True:
                return
            self.closed = True
            self.unregister_database()

        def register_database(self):
            if self.registered is False:
                self.model.database.register_handle(self.handle)
                self.registered = True

        def unregister_database(self):
            if self.registered is True:
                self.model.database.unregister_handle(self.handle)
                self.registered = False

        def get_wave(self, start_time, end_time):
            if self.model.closed is True:
                raise RuntimeError("View_Model is closed")
            self.register_database()
            return self.model.database.get(self.handle, start_time, end_time)

        def format_value(self, value):
            if self.is_logic:
                return value
            if all(c in "01" for c in value):
                return format(int(value,2), self.value_format)

            def _format_4state_bits(value, width):
                result  = []
                padding = (-len(value)) % width
                value   = "0" * padding + value
                for pos in range(0, len(value), width):
                    bits = value[pos:pos + width]
                    if all(c in "01" for c in bits):
                        number = int(bits, 2)
                        result.append(format(number, self.value_format_type))
                    elif "u" in bits or "U" in bits:
                        result.append("U")
                    elif "z" in bits or "Z" in bits:
                        result.append("Z")
                    else:
                        result.append("?")
                return "".join(result)
            
            if   self.value_format_type in ("x", "X"):
                result = _format_4state_bits(value, 4)
            elif self.value_format_type == "o":
                result = _format_4state_bits(value, 3)
            else:
                result = value
            if self.value_format_width is not None and len(result) < self.value_format_width:
                padding = self.value_format_width - len(result)
                if self.value_format_zero:
                    result = "0" * padding + result
                else:
                    result = " " * padding + result
            return self.value_format_prefix + result + self.value_format_suffix
            
    class View_Clock(View_Item):
        DEFAULT_OPTION = {
            "display_name"    : None,
            "display_wave"    : False,
            "rising_edge"     : True
        }
        def __init__(self, view_list, name, parent_group, option=None):
            super().__init__(view_list, parent_group, option)
            self.name         = name
            self.closed       = False
            self.display_name = self.option["display_name"] or self.name
            self.display_wave = self.option["display_wave"]
            self.rising_edge  = self.option["rising_edge"]

        def close(self):
            if self.closed is True:
                return
            self.closed = True

        def register_database(self):
            pass

        def unregister_database(self):
            pass

    class View_Signal_Clock(View_Clock):
        DEFAULT_OPTION = {
            "display_name"    : None ,
            "display_wave"    : False,
            "rising_edge"     : True ,
        }
        def __init__(self, signal, option=None):
            super().__init__(signal.view_list, signal.name, signal.parent_group, option)
            self.signal   = signal
            self.option   = self.model.merge_option(self.signal.option, self.option)
            self.is_logic = signal.is_logic
            
        def register_database(self):
            self.signal.register_database()

        def unregister_database(self):
            self.signal.unregister_database()

        def get_edges(self, start_time, end_time):
            if self.model.closed is True:
                raise RuntimeError("View_Model is closed")
            prev_level = None
            first      = True
            for curr_time, curr_value in self.get_wave(start_time, end_time):
                if curr_value in ("1", "h"):
                    curr_level = 1
                else:
                    curr_level = 0
                if first:
                    first = False
                    prev_level = curr_level
                    continue
                if ((self.rising_edge is True  and prev_level == 0 and curr_level == 1) or
                    (self.rising_edge is False and prev_level == 1 and curr_level == 0)):
                    yield curr_time
                prev_level = curr_level
                
        def get_wave(self, start_time, end_time):
            if self.model.closed is True:
                raise RuntimeError("View_Model is closed")
            return self.signal.get_wave(start_time, end_time)

    class View_Virtual_Clock(View_Clock):
        DEFAULT_OPTION = {
            "display_name"    : None,
            "display_wave"    : False,
            "rising_edge"     : True
        }
        def __init__(self, view_list, name, cycle_time, offset_time, parent_group, option=None):
            super().__init__(view_list, name, parent_group, option)
            self.cycle_time  = cycle_time
            self.offset_time = self.view_list.model.start_time + offset_time
            self.is_logic    = True

        def get_edges(self, start_time, end_time):
            if self.model.closed is True:
                raise RuntimeError("View_Model is closed")
            first_time = (self.offset_time +
                          ((start_time - self.offset_time                      ) // self.cycle_time)
                          * self.cycle_time)
            last_time  = (self.offset_time +
                          ((end_time   - self.offset_time + self.cycle_time - 1) // self.cycle_time)
                           * self.cycle_time)
            for time in range(first_time, last_time, self.cycle_time):
                    yield time

        def get_wave(self, start_time, end_time):
            if self.model.closed is True:
                raise RuntimeError("View_Model is closed")
            half_cycle_time = self.cycle_time // 2
            if self.rising_edge:
                first_half_level  = "1"
                second_half_level = "0"
            else:
                first_half_level  = "0"
                second_half_level = "1"
            for time in self.get_edges(start_time, end_time):
                yield (time                  , first_half_level )
                yield (time + half_cycle_time, second_half_level)
                    

    class View_Group(View_Item):
        DEFAULT_OPTION = {
            "display_name"    : None,
            "expand"          : True
        }
        def __init__(self, view_list, name, parent_group, option=None):
            super().__init__(view_list, parent_group, option)
            self.name         = name
            self.item_list    = []
            self.closed       = False
            self.child_option = self.model.get_inherited_option(self.option)
            self.display_name = self.option["display_name"] or self.name
            self.expanded     = self.option["expand"]

        def close(self):
            if self.closed is True:
                return
            self.closed = True
            self.unregister_database()
            for item in self.item_list:
                item.close()
            self.item_list.clear()

        def _add_signals(self, pattern, tree, option):
            var_list = self.model.reader.find_var_list(pattern, tree=tree, struct_as_var=True)
            for path_name_list, node in var_list:
                path = "::".join(path_name_list)
                if "handle" in node:
                    signal = self.model.View_Signal(self.view_list, path, node, self, option)
                    self.item_list.append(signal)
                else:
                    group_option = self.model.merge_option(option, {"expand": False})
                    group = self.add_group(node["name"], group_option)
                    for child in node.get("contents", []):
                       group._add_signals(pattern="**", tree=child, option=option)
            return self

        def add_signals(self, pattern, option=None):
            if self.closed is True:
                raise RuntimeError("View_Group is closed")
            return self._add_signals(pattern, tree=self.model.reader.tree, option=option)

        def add_signal_clock(self, pattern, option=None):
            if self.closed is True:
                raise RuntimeError("View_Group is closed")
            if self.view_list.clock is not None:
                raise RuntimeError("View_List already contains a clock")
            var_list = self.model.reader.find_var_list(pattern)
            if len(var_list) == 0:
                raise RuntimeError(f'No clock matched the specified pattern: "{pattern}"')
            if len(var_list) >= 2:
                raise RuntimeError(f'Multiple signals matched the specified clock pattern: "{pattern}"')
            path = "::".join(var_list[0][0])
            node = var_list[0][1]
            if "handle" not in node:
                raise RuntimeError(f'The specified pattern does not match a signal: "{pattern}"')
            signal = self.model.View_Signal(self.view_list, path, node, self, option)
            clock  = self.model.View_Signal_Clock(signal, option)
            self.item_list.append(clock)
            self.view_list.clock = clock
            return self
            
        def add_virtual_clock(self, name, cycle_time, offset_time, option=None):
            if self.closed is True:
                raise RuntimeError("View_Group is closed")
            if self.view_list.clock is not None:
                raise RuntimeError("View_List already contains a clock")
            cycle  = self.model.parse_time(cycle_time)
            offset = self.model.parse_time(offset_time)
            clock  = self.model.View_Virtual_Clock(self.view_list, name, cycle, offset, self, option)
            self.item_list.append(clock)
            self.view_list.clock = clock
            return self
            
        def add_group(self, name, option=None):
            if self.closed is True:
                raise RuntimeError("View_Group is closed")
            group = self.model.View_Group(self.view_list, name, self, option)
            self.item_list.append(group)
            return group

        def register_database(self):
            if self.closed is True:
                raise RuntimeError("View_Group is closed")
            for item in self.item_list:
                item.register_database()
                
        def unregister_database(self):
            for item in self.item_list:
                item.unregister_database()
                
        def items(self):
            return self.item_list

    class View_List:
        DEFAULT_OPTION = {
            "display_rows"      : 24 ,
        }
        def __init__(self, model, name, option=None):
            self.model          = model
            self.name           = name
            self.start_time     = self.model.start_time
            self.end_time       = self.model.end_time
            self.current_time   = self.start_time
            self.option         = self.model.merge_option(option, self.DEFAULT_OPTION)
            self.group_option   = self.model.get_inherited_option(self.option)
            self.root_group     = self.model.View_Group(self, "", None, self.group_option)
            self.clock          = None
            self.view_item_list = []
            self.item_row_map   = {}
            
            self.background_color = self.get_color("wave", "background", "black")

        def close(self):
            if self.root_group is None:
                return
            self.root_group.close()
            self.root_group = None
            self.clock      = None
            self.view_item_list.clear()
            self.item_row_map.clear()
                
        def register_database(self):
            if self.root_group is not None:
                self.root_group.register_database()
                
        def unregister_database(self):
            if self.root_group is not None:
                self.root_group.unregister_database()

        def add_group(self, name, option=None):
            if self.root_group is None:
                raise RuntimeError("View_List is closed")
            group_option = self.model.merge_option(option, self.group_option)
            return self.root_group.add_group(name, group_option)

        def add_signal_clock(self, pattern, option=None):
            if self.root_group is None:
                raise RuntimeError("View_List is closed")
            clock_option = self.model.merge_option(option, self.group_option)
            return self.root_group.add_signal_clock(pattern, clock_option)

        def add_virtual_clock(self, name, cycle_time, offset_time, option=None):
            if self.root_group is None:
                raise RuntimeError("View_List is closed")
            clock_option = self.model.merge_option(option, self.group_option)
            return self.root_group.add_virtual_clock(name, cycle_time, offset_time, clock_option)
        
        def rebuild(self):
            self.view_item_list.clear()
            self.item_row_map.clear()
            self._append_group_to_view_item_list(self.root_group)
            for row, item in enumerate(self.view_item_list):
                self.item_row_map[id(item)] = row

        def _append_group_to_view_item_list(self, group):
            for item in group.items():
                if self.item_is_signal(item):
                    self.view_item_list.append(item)
                    continue
                if self.item_is_group(item):
                    self.view_item_list.append(item)
                    if item.expanded:
                        self._append_group_to_view_item_list(item)
                    continue
                if self.item_is_clock(item):
                    if item.display_wave:
                        self.view_item_list.append(item)
                    continue

        def set_group_expand(self, group, expand):
            if group.view_list is not self:
                raise RuntimeError("group does not belong to this View_List")
            if not self.item_is_group(group):
                return
            group.expanded = bool(expand)
            self.rebuild()

        def expand_group(self, group):
            self.set_group_expand(group, True )

        def collapse_group(self, group):
            self.set_group_expand(group, False)
        
        def toggle_group(self, group):
            self.set_group_expand(group, not group.expanded)

        def format_time_scale(self, time_scale):
            return self.model.format_time_scale(time_scale)

        def format_timestamp(self, timestamp, time_scale=None):
            return self.model.format_timestamp(timestamp, time_scale)

        def parse_timestamp(self, value, unit=None, time_scale=None):
            return self.model.parse_timestamp(value, unit, time_scale)

        def view_items(self):
            return self.view_item_list

        def row_count(self):
            return len(self.view_item_list)
        
        def row_to_item(self, row):
            if row < 0 or row >= self.row_count():
                return None
            return self.view_item_list[row]

        def item_to_row(self, item):
            return self.item_row_map.get(id(item))

        def item_is_contains(self, item):
            return id(item) in self.item_row_map

        def item_is_group(self, item):
            return isinstance(item, self.model.View_Group)

        def item_is_signal(self, item):
            return isinstance(item, self.model.View_Signal)
        
        def item_is_clock(self, item):
            return isinstance(item, self.model.View_Clock)
        
        def row_is_group(self, row):
            item = self.row_to_item(row)
            return item is not None and self.item_is_group(item)
        
        def row_is_signal(self, row):
            item = self.row_to_item(row)
            return item is not None and self.item_is_signal(item)
        
        def row_to_parent_group(self, row):
            item = self.row_to_item(row)
            if item is None:
                return None
            return item.parent_group

        def get_option(self, key, default_value=None):
            return self.option.get(key, default_value)
        
        def get_color(self, key, prop=None, default_value=None):
            color = self.get_option("color", {})
            return color.get(key,{}).get(prop, default_value)

    DEFAULT_OPTION = {
        "header_height"      : 24    ,
        "footer_height"      : 24    ,
        "signal_height"      : 24    ,
        "signal_name_width"  : 200   ,
        "signal_value_width" : 200   ,
        "display_rows"       : 24    ,
        "start_time"         : None  ,
        "end_time"           : None  ,
        "time_quantum"       : "1 ns",
        "edge_slope"         : 3     ,
        "color"              : {
              "cursor"    : "yellow",
              "marker"    : "red"   ,
              "header"    : {"background": "black", "foreground"   : "white"},
              "time_ruler": {"background": "black",
                             "line"      : "gray" ,
                             "text"      : "white"},
              "name"      : {"background": "black", "foreground"   : "white"},
              "value"     : {"background": "black", "foreground"   : "white"},
              "wave"      : {"background": "black",
                             "signal" : "#00ff00",
                             "value"  : "white"  ,
                             "group"  : None},
        }
    }
    INHERITABLE_OPTION = {"color": {"name": True, "value": True, "wave": True}}
    
    def __init__(self, file_name, option=None):
        self.file_name      = file_name
        self.reader         = FST_Reader(file_name)
        self.database       = FST_Wave_DataBase(self.reader)
        self.option         = self.merge_option(option, self.DEFAULT_OPTION)
        self.child_option   = self.get_inherited_option(self.option)
        self.reader.read_tree()
        self.start_time     = self.parse_time(self.option["start_time"  ])
        self.end_time       = self.parse_time(self.option["end_time"    ])
        self.time_quantum   = self.parse_time(self.option["time_quantum"])
        if self.start_time is None or self.start_time < self.reader.start_time:
            self.start_time = self.reader.start_time
        if self.end_time   is None or self.end_time   > self.reader.end_time  :
            self.end_time   = self.reader.end_time
        self.current_time   = self.start_time
        self.view_list_list = []
        self.curr_view_list = self.add_view_list("top")
        self.closed         = False

    def set_start_time(self, start_time):
        self.start_time = start_time
        if self.start_time is None or self.start_time < self.reader.start_time:
            self.start_time = self.reader.start_time
        
    def set_end_time(self, end_time):
        self.end_time = end_time
        if self.end_time   is None or self.end_time   > self.reader.end_time  :
            self.end_time   = self.reader.end_time
        
    def parse_time(self, text):
        if text is None:
            return None
        text = text.strip()
        # 数値 + 単位
        m = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Zµ]+)", text)
        if m:
            value = float(m.group(1))
            unit  = m.group(2)
            return self.reader.parse_timestamp(value, unit)
        # 数値のみ
        m = re.fullmatch(r"[0-9]+", text)
        if m:
            return self.reader.parse_timestamp(int(text))

        raise ValueError(f"Invalid time format: {text}")

    def deep_copy(self, obj):
        if isinstance(obj, dict):
            result = {}
            for key,value in obj.items():
                result[key] = self.deep_copy(value)
            return result
        if isinstance(obj, list):
            result = []
            for value in obj:
                result.append(self.deep_copy(value))
            return result
        if isinstance(obj, tuple):
            result = []
            for value in obj:
                result.append(self.deep_copy(value))
            return tuple(result)
        if isinstance(obj, set):
            result = set()
            for value in obj:
                result.add(self.deep_copy(value))
            return result
        return obj
        
    def new_option(self, default_option):
        if default_option is None:
            return {}
        else:
            return self.deep_copy(default_option)

    def merge_option(self, new, base):
        base_option = self.new_option(base)
        if new is None:
            return base_option
        for new_key, new_value in new.items():
            if new_key in base_option:
                if isinstance(new_value, dict) and isinstance(base_option[new_key], dict):
                    base_option[new_key] = self.merge_option(new_value, base_option[new_key])
                else:
                    base_option[new_key] = new_value
            else:
                base_option[new_key] = self.deep_copy(new_value)
        return base_option

    def get_inherited_option(self, option, inheritable_option=None):
        if inheritable_option is None:
            return self.get_inherited_option(option, self.INHERITABLE_OPTION)
        new_option = {}
        for key,value in inheritable_option.items():
            if key not in option:
                continue
            if value is True:
                new_option[key] = self.deep_copy(option[key])
            elif isinstance(value, dict) and isinstance(option[key], dict):
                new_option[key] = self.get_inherited_option(option[key], value)
        return new_option
        
    def add_view_list(self, name, option=None):
        new_option  = self.merge_option(option, self.child_option)
        view_list   = self.View_List(self, name, new_option)
        self.view_list_list.append(view_list)
        return view_list

    def view_lists(self):
        return self.view_list_list

    def refresh(self):
        self.rebuild()
        
    def rebuild(self):
        for view_list in self.view_list_list:
            view_list.rebuild()

    def close(self):
        for view_list in self.view_list_list:
            view_list.close()
        self.reader.close()
        self.view_list_list.clear()
        self.curr_view_list = None
        self.closed         = True

    def load_wave(self, start_time=None, end_time=None):
        if start_time is None:
            start_time = self.start_time

        if end_time is None:
            end_time   = self.end_time

        for view_list in self.view_list_list:
            view_list.register_database()
        
        self.database.load_wave_signals(start_time, end_time)

    def format_time_scale(self, time_scale):
        return self.reader.format_time_scale(time_scale)

    def format_timestamp(self, timestamp, time_scale=None):
        return self.reader.format_timestamp(timestamp, time_scale)

    def parse_timestamp(self, value, unit=None, time_scale=None):
        return self.reader.parse_timestamp(value, unit, time_scale)

    def add_group(self, name, option=None):
        if self.closed is True:
            raise RuntimeError("View_Model is closed")
        return self.curr_view_list.add_group(name, option)

    def add_signal_clock(self, pattern, option=None):
        if self.closed is True:
            raise RuntimeError("View_Model is closed")
        return self.curr_view_list.add_signal_clock(pattern, option)

    def add_virtual_clock(self, name, cycle_time, offset_time, option=None):
        if self.closed is True:
            raise RuntimeError("View_Model is closed")
        return self.curr_view_list.add_virtual_clock(name, cycle_time, offset_time, option)

    def set_group_expand(self, group, expand):
        if self.closed is True:
            raise RuntimeError("View_Model is closed")
        self.curr_view_list.set_group_expand(group, expand)

    def expand_group(self, group):
        if self.closed is True:
            raise RuntimeError("View_Model is closed")
        self.curr_view_list.expand_group(group)

    def collapse_group(self, group):
        if self.closed is True:
            raise RuntimeError("View_Model is closed")
        self.curr_view_list.collapse_group(group)
        
    def toggle_group(self, group):
        if self.closed is True:
            raise RuntimeError("View_Model is closed")
        self.curr_view_list.toggle_group(group)

    def view_items(self):
        if self.closed is True:
            raise RuntimeError("View_Model is closed")
        return self.curr_view_list.view_items()

    def row_count(self):
        if self.closed is True:
            raise RuntimeError("View_Model is closed")
        return self.curr_view_list.row_count()
        
    def row_to_item(self, row):
        if self.closed is True:
            raise RuntimeError("View_Model is closed")
        return self.curr_view_list.row_to_item(row)

    def item_to_row(self, item):
        if self.closed is True:
            raise RuntimeError("View_Model is closed")
        return self.curr_view_list.item_to_row(item)

    def item_is_contains(self, item):
        if self.closed is True:
            raise RuntimeError("View_Model is closed")
        return self.curr_view_list.item_is_contains(item)

    def item_is_group(self, item):
        if self.closed is True:
            raise RuntimeError("View_Model is closed")
        return self.curr_view_list.item_is_group(item)

    def item_is_signal(self, item):
        if self.closed is True:
            raise RuntimeError("View_Model is closed")
        return self.curr_view_list.item_is_signal(item)
        
    def row_is_group(self, row):
        if self.closed is True:
            raise RuntimeError("View_Model is closed")
        item = self.row_to_item(row)
        return item is not None and self.item_is_group(item)
        
    def row_is_signal(self, row):
        if self.closed is True:
            raise RuntimeError("View_Model is closed")
        item = self.row_to_item(row)
        return item is not None and self.item_is_signal(item)
        
    def row_to_parent_group(self, row):
        if self.closed is True:
            raise RuntimeError("View_Model is closed")
        item = self.row_to_item(row)
        if item is None:
            return None
        return item.parent_group

    def get_option(self, key, default_value=None):
        return self.option.get(key, default_value)

    def get_color(self, key, prop=None, default_value=None):
        color = self.get_option("color", {})
        if prop is None:
            return color.get(key, default_value)
        return color.get(key,{}).get(prop, default_value)
