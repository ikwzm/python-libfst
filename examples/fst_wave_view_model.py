#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-2-Clause
# Copyright (c) 2026 ikwzm

from   fst_reader        import FST_Reader
from   fst_wave_database import FST_Wave_DataBase

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

        def get_color(self, key, prop):
            return self.color_option.get(key,{}).get(prop)

        def get_foreground_color(self, key):
            return self.get_color(key, "foreground")

        def get_background_color(self, key):
            return self.get_color(key, "background")
        
    class View_Signal(View_Item):
        DEFAULT_OPTION = {
            "display_name"    : None ,
        }
        def __init__(self, view_list, path, node, parent_group, option=None):
            super().__init__(view_list, parent_group, option)
            self.path         = path
            self.node         = node
            self.name         = node["name"]
            self.handle       = node["handle"]
            self.registered   = False
            self.closed       = False
            self.display_name = self.option["display_name"] or self.name

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
            self.view_item_list = []
            self.item_row_map   = {}

        def close(self):
            if self.root_group is None:
                return
            self.root_group.close()
            self.root_group = None
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

        def rebuild(self):
            self.view_item_list.clear()
            self.item_row_map.clear()
            self._append_group_to_view_item_list(self.root_group)
            for row, item in enumerate(self.view_item_list):
                self.item_row_map[id(item)] = row

        def _append_group_to_view_item_list(self, group):
            for item in group.items():
                self.view_item_list.append(item)
                if self.item_is_group(item):
                    if item.expanded:
                        self._append_group_to_view_item_list(item)

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
        
    DEFAULT_OPTION = {
        "header_height"      : 24 ,
        "footer_height"      : 24 ,
        "signal_height"      : 24 ,
        "signal_name_width"  : 200,
        "signal_value_width" : 200,
        "display_rows"       : 24 ,
        "color"              : {
              "name"  : {"foreground" : "white", "background": "black"},
              "value" : {"foreground" : "white", "background": "black"},
              "wave"  : {"foreground" : "green", "background": "black"},
        }
    }
    INHERITED_OPTION_LIST = ["color"]
    
    def __init__(self, file_name, option=None):
        self.file_name      = file_name
        self.reader         = FST_Reader(file_name)
        self.database       = FST_Wave_DataBase(self.reader)
        self.start_time     = self.reader.start_time
        self.end_time       = self.reader.end_time
        self.current_time   = self.start_time
        self.option         = self.merge_option(option, self.DEFAULT_OPTION)
        self.child_option   = self.get_inherited_option(self.option)
        self.reader.read_tree()
        self.view_list_list = []
        self.curr_view_list = self.add_view_list("top")
        self.closed         = False

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

    def get_inherited_option(self, option):
        return {key: self.option[key] for key in self.INHERITED_OPTION_LIST}
        
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
