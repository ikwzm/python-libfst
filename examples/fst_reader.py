#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-2-Clause
# Copyright (c) 2026 ikwzm

import libfst
import fnmatch
from enum import IntEnum

class FST_Reader:
    def __init__(self, file_name):
        self.reader     = libfst.Reader(file_name)
        self.file_name  = file_name
        self.file_type  = self.reader.file_type
        self.date       = self.reader.date.rstrip("\n\r")
        self.version    = self.reader.version.rstrip("\n\r")
        self.time_scale = self.reader.time_scale
        self.start_time = self.reader.start_time
        self.end_time   = self.reader.end_time
        self.tree       = {"contents": []}

    class FileType(IntEnum):
        VERILOG                    = libfst.Enum.FST_FT_VERILOG
        VHDL                       = libfst.Enum.FST_FT_VHDL
        VERILOG_VHDL               = libfst.Enum.FST_FT_VERILOG_VHDL
        
    class ScopeType(IntEnum):
        VCD_MODULE                 = libfst.Enum.FST_ST_VCD_MODULE
        VCD_TASK                   = libfst.Enum.FST_ST_VCD_TASK               
        VCD_FUNCTION               = libfst.Enum.FST_ST_VCD_FUNCTION           
        VCD_BEGIN                  = libfst.Enum.FST_ST_VCD_BEGIN              
        VCD_FORK                   = libfst.Enum.FST_ST_VCD_FORK               
        VCD_GENERATE               = libfst.Enum.FST_ST_VCD_GENERATE           
        VCD_STRUCT                 = libfst.Enum.FST_ST_VCD_STRUCT             
        VCD_UNION                  = libfst.Enum.FST_ST_VCD_UNION              
        VCD_CLASS                  = libfst.Enum.FST_ST_VCD_CLASS              
        VCD_INTERFACE              = libfst.Enum.FST_ST_VCD_INTERFACE          
        VCD_PACKAGE                = libfst.Enum.FST_ST_VCD_PACKAGE            
        VCD_PROGRAM                = libfst.Enum.FST_ST_VCD_PROGRAM            
        VHDL_ARCHITECTURE          = libfst.Enum.FST_ST_VHDL_ARCHITECTURE      
        VHDL_PROCEDURE             = libfst.Enum.FST_ST_VHDL_PROCEDURE         
        VHDL_FUNCTION              = libfst.Enum.FST_ST_VHDL_FUNCTION          
        VHDL_RECORD                = libfst.Enum.FST_ST_VHDL_RECORD            
        VHDL_PROCESS               = libfst.Enum.FST_ST_VHDL_PROCESS           
        VHDL_BLOCK                 = libfst.Enum.FST_ST_VHDL_BLOCK             
        VHDL_FOR_GENERATE          = libfst.Enum.FST_ST_VHDL_FOR_GENERATE      
        VHDL_IF_GENERATE           = libfst.Enum.FST_ST_VHDL_IF_GENERATE       
        VHDL_GENERATE              = libfst.Enum.FST_ST_VHDL_GENERATE          
        VHDL_PACKAGE               = libfst.Enum.FST_ST_VHDL_PACKAGE           
        SV_ARRAY                   = libfst.Enum.FST_ST_SV_ARRAY               
        
    class VarType(IntEnum):
        VCD_EVENT                  = libfst.Enum.FST_VT_VCD_EVENT              
        VCD_INTEGER                = libfst.Enum.FST_VT_VCD_INTEGER            
        VCD_PARAMETER              = libfst.Enum.FST_VT_VCD_PARAMETER          
        VCD_REAL                   = libfst.Enum.FST_VT_VCD_REAL               
        VCD_REAL_PARAMETER         = libfst.Enum.FST_VT_VCD_REAL_PARAMETER     
        VCD_REG                    = libfst.Enum.FST_VT_VCD_REG                
        VCD_SUPPLY0                = libfst.Enum.FST_VT_VCD_SUPPLY0            
        VCD_SUPPLY1                = libfst.Enum.FST_VT_VCD_SUPPLY1            
        VCD_TIME                   = libfst.Enum.FST_VT_VCD_TIME               
        VCD_TRI                    = libfst.Enum.FST_VT_VCD_TRI                
        VCD_TRIAND                 = libfst.Enum.FST_VT_VCD_TRIAND             
        VCD_TRIOR                  = libfst.Enum.FST_VT_VCD_TRIOR              
        VCD_TRIREG                 = libfst.Enum.FST_VT_VCD_TRIREG             
        VCD_TRI0                   = libfst.Enum.FST_VT_VCD_TRI0               
        VCD_TRI1                   = libfst.Enum.FST_VT_VCD_TRI1               
        VCD_WAND                   = libfst.Enum.FST_VT_VCD_WAND               
        VCD_WIRE                   = libfst.Enum.FST_VT_VCD_WIRE               
        VCD_WOR                    = libfst.Enum.FST_VT_VCD_WOR                
        VCD_PORT                   = libfst.Enum.FST_VT_VCD_PORT               
        VCD_SPARRAY                = libfst.Enum.FST_VT_VCD_SPARRAY            
        VCD_REALTIME               = libfst.Enum.FST_VT_VCD_REALTIME           
        GEN_STRING                 = libfst.Enum.FST_VT_GEN_STRING             
        SV_BIT                     = libfst.Enum.FST_VT_SV_BIT                 
        SV_LOGIC                   = libfst.Enum.FST_VT_SV_LOGIC               
        SV_INT                     = libfst.Enum.FST_VT_SV_INT                 
        SV_SHORTINT                = libfst.Enum.FST_VT_SV_SHORTINT            
        SV_LONGINT                 = libfst.Enum.FST_VT_SV_LONGINT             
        SV_BYTE                    = libfst.Enum.FST_VT_SV_BYTE                
        SV_ENUM                    = libfst.Enum.FST_VT_SV_ENUM                
        SV_SHORTREAL               = libfst.Enum.FST_VT_SV_SHORTREAL           
        
    class VarDir(IntEnum):
        IMPLICIT                   = libfst.Enum.FST_VD_IMPLICIT               
        INPUT                      = libfst.Enum.FST_VD_INPUT                  
        OUTPUT                     = libfst.Enum.FST_VD_OUTPUT                 
        INOUT                      = libfst.Enum.FST_VD_INOUT                  
        BUFFER                     = libfst.Enum.FST_VD_BUFFER                 
        LINKAGE                    = libfst.Enum.FST_VD_LINKAGE                

    class AttrType(IntEnum):
        MISC                       = libfst.Enum.FST_AT_MISC                   
        ARRAY                      = libfst.Enum.FST_AT_ARRAY                  
        ENUM                       = libfst.Enum.FST_AT_ENUM                   
        PACK                       = libfst.Enum.FST_AT_PACK
        
    class AttrMiscType(IntEnum):
        COMMENT                    = libfst.Enum.FST_MT_COMMENT                
        ENVVAR                     = libfst.Enum.FST_MT_ENVVAR                 
        SUPVAR                     = libfst.Enum.FST_MT_SUPVAR                 
        PATHNAME                   = libfst.Enum.FST_MT_PATHNAME               
        SOURCESTEM                 = libfst.Enum.FST_MT_SOURCESTEM             
        SOURCEISTEM                = libfst.Enum.FST_MT_SOURCEISTEM            
        VALUELIST                  = libfst.Enum.FST_MT_VALUELIST              
        ENUMTABLE                  = libfst.Enum.FST_MT_ENUMTABLE              
        UNKNOWN                    = libfst.Enum.FST_MT_UNKNOWN                
        
    class AttrArrayType(IntEnum):
        NONE                       = libfst.Enum.FST_AR_NONE                   
        UNPACKED                   = libfst.Enum.FST_AR_UNPACKED               
        PACKED                     = libfst.Enum.FST_AR_PACKED                 
        SPARSE                     = libfst.Enum.FST_AR_SPARSE                 
        
    class AttrEnumType(IntEnum):
        SV_INTEGER                 = libfst.Enum.FST_EV_SV_INTEGER             
        SV_BIT                     = libfst.Enum.FST_EV_SV_BIT                 
        SV_LOGIC                   = libfst.Enum.FST_EV_SV_LOGIC               
        SV_INT                     = libfst.Enum.FST_EV_SV_INT                 
        SV_SHORTINT                = libfst.Enum.FST_EV_SV_SHORTINT            
        SV_LONGINT                 = libfst.Enum.FST_EV_SV_LONGINT             
        SV_BYTE                    = libfst.Enum.FST_EV_SV_BYTE                
        SV_UNSIGNED_INTEGER        = libfst.Enum.FST_EV_SV_UNSIGNED_INTEGER    
        SV_UNSIGNED_BIT            = libfst.Enum.FST_EV_SV_UNSIGNED_BIT        
        SV_UNSIGNED_LOGIC          = libfst.Enum.FST_EV_SV_UNSIGNED_LOGIC      
        SV_UNSIGNED_INT            = libfst.Enum.FST_EV_SV_UNSIGNED_INT        
        SV_UNSIGNED_SHORTINT       = libfst.Enum.FST_EV_SV_UNSIGNED_SHORTINT   
        SV_UNSIGNED_LONGINT        = libfst.Enum.FST_EV_SV_UNSIGNED_LONGINT    
        SV_UNSIGNED_BYTE           = libfst.Enum.FST_EV_SV_UNSIGNED_BYTE       
        REG                        = libfst.Enum.FST_EV_REG                    
        TIME                       = libfst.Enum.FST_EV_TIME                   

    class AttrPackType(IntEnum):
        NONE                       = libfst.Enum.FST_PT_NONE                   
        UNPACKED                   = libfst.Enum.FST_PT_UNPACKED               
        PACKED                     = libfst.Enum.FST_PT_PACKED                 
        TAGGED_PACKED              = libfst.Enum.FST_PT_TAGGED_PACKED          

    class AttrSupplementalVarType(IntEnum):
        SVT_NONE                   = libfst.Enum.FST_SVT_NONE                  
        SVT_VHDL_SIGNAL            = libfst.Enum.FST_SVT_VHDL_SIGNAL           
        SVT_VHDL_VARIABLE          = libfst.Enum.FST_SVT_VHDL_VARIABLE         
        SVT_VHDL_CONSTANT          = libfst.Enum.FST_SVT_VHDL_CONSTANT         
        SVT_VHDL_FILE              = libfst.Enum.FST_SVT_VHDL_FILE             
        SVT_VHDL_MEMORY            = libfst.Enum.FST_SVT_VHDL_MEMORY           

    class AttrSupplementalDataType(IntEnum):
        SDT_NONE                   = libfst.Enum.FST_SDT_NONE                  
        SDT_VHDL_BOOLEAN           = libfst.Enum.FST_SDT_VHDL_BOOLEAN          
        SDT_VHDL_BIT               = libfst.Enum.FST_SDT_VHDL_BIT              
        SDT_VHDL_BIT_VECTOR        = libfst.Enum.FST_SDT_VHDL_BIT_VECTOR       
        SDT_VHDL_STD_ULOGIC        = libfst.Enum.FST_SDT_VHDL_STD_ULOGIC       
        SDT_VHDL_STD_ULOGIC_VECTOR = libfst.Enum.FST_SDT_VHDL_STD_ULOGIC_VECTOR
        SDT_VHDL_STD_LOGIC         = libfst.Enum.FST_SDT_VHDL_STD_LOGIC        
        SDT_VHDL_STD_LOGIC_VECTOR  = libfst.Enum.FST_SDT_VHDL_STD_LOGIC_VECTOR 
        SDT_VHDL_UNSIGNED          = libfst.Enum.FST_SDT_VHDL_UNSIGNED         
        SDT_VHDL_SIGNED            = libfst.Enum.FST_SDT_VHDL_SIGNED           
        SDT_VHDL_INTEGER           = libfst.Enum.FST_SDT_VHDL_INTEGER          
        SDT_VHDL_REAL              = libfst.Enum.FST_SDT_VHDL_REAL             
        SDT_VHDL_NATURAL           = libfst.Enum.FST_SDT_VHDL_NATURAL          
        SDT_VHDL_POSITIVE          = libfst.Enum.FST_SDT_VHDL_POSITIVE         
        SDT_VHDL_TIME              = libfst.Enum.FST_SDT_VHDL_TIME             
        SDT_VHDL_CHARACTER         = libfst.Enum.FST_SDT_VHDL_CHARACTER        
        SDT_VHDL_STRING            = libfst.Enum.FST_SDT_VHDL_STRING           

    def enum_name(self, enum_class, value):
        try:
            return enum_class(value).name
        except ValueError:
            return f"UNKNOWN({value})"

    def attr_subtype_name(self, attr_type, subtype):
        try:
            if attr_type == libfst.Enum.FST_AT_MISC:
                return self.enum_name(self.AttrMiscType, subtype)
            if attr_type == libfst.Enum.FST_AT_ARRAY:
                return self.enum_name(self.AttrArrayType, subtype)
            if attr_type == libfst.Enum.FST_AT_ENUM:
                return self.enum_name(self.AttrEnumType, subtype)
            if attr_type == libfst.Enum.FST_AT_PACK:
                return self.enum_name(self.AttrPackType, subtype)
        except ValueError:
            return f"UNKNOWN({subtype})"
        
    def read_tree(self):
        self.tree.setdefault("contents", []).clear()
        attributes = []
        stack      = [self.tree]
        
        for item in self.reader.hiers():
            if   isinstance(item, libfst.hier.Scope):
                node = {
                    "name"     : item.name,
                    "type"     : self.enum_name(self.ScopeType,item.scope_type),
                }
                if attributes:
                    node.setdefault("attributes", []).extend(attributes)
                    attributes.clear()
                node.setdefault("contents", [])
                stack[-1]["contents"].append(node)
                stack.append(node)
            elif isinstance(item, libfst.hier.UpScope):
                if len(stack) > 1:
                    node = stack.pop()
            elif isinstance(item, libfst.hier.Var):
                node = {
                    "name"     : item.name,
                    "type"     : self.enum_name(self.VarType, item.var_type),
                    "direction": self.enum_name(self.VarDir , item.direction),
                    "width"    : item.length,
                    "handle"   : item.handle,
                    "is_alias" : item.is_alias,
                }
                if attributes:
                    node.setdefault("attributes", []).extend(attributes)
                    attributes.clear()
                stack[-1]["contents"].append(node)
            elif isinstance(item, libfst.hier.AttrSupplemental):
                attributes.append({
                    "name"     : item.name,
                    "type"     : self.enum_name(self.AttrType, item.attr_type),
                    "subtype"  : self.attr_subtype_name(item.attr_type, item.subtype),
                    "var_type" : self.enum_name(self.AttrSupplementalVarType , item.var_type),
                    "data_type": self.enum_name(self.AttrSupplementalDataType, item.data_type),
                })
            elif isinstance(item, libfst.hier.AttrPathname):
                attributes.append({
                    "name"     : item.pathname,
                    "type"     : self.enum_name(self.AttrType, item.attr_type),
                    "subtype"  : self.attr_subtype_name(item.attr_type, item.subtype),
                    "handle"   : item.handle,
                })
            elif isinstance(item, libfst.hier.AttrSourceStem):
                attributes.append({
                    "type"     : self.enum_name(self.AttrType, item.attr_type),
                    "subtype"  : self.attr_subtype_name(item.attr_type, item.subtype),
                    "handle"   : item.handle,
                    "line"     : item.line,
                })
            elif isinstance(item, libfst.hier.Attr):
                attributes.append({
                    "name"     : item.name,
                    "type"     : self.enum_name(self.AttrType, item.attr_type),
                    "subtype"  : self.attr_subtype_name(item.attr_type, item.subtype),
                    "arg"      : item.arg,
                })
            elif isinstance(item, libfst.hier.AttrEnd):
                pass
        return self.tree


    def find_var_list(self, pattern, tree=None, struct_as_var=False):
        var_list     = []
        pattern_list = pattern.split("::")

        def match_parts(path_list, pattern_list):
            if not pattern_list:
                return not path_list
            if pattern_list[0] == "**":
                # ** は0階層以上に一致
                if match_parts(path_list, pattern_list[1:]):
                    return True
                if not path_list:
                    return False
                return match_parts(path_list[1:], pattern_list)
            if not path_list:
                return False
            is_vhdl = path_list[0][1]
            if is_vhdl:
                path    = path_list[0][0].casefold()
                pattern = pattern_list[0].casefold()
            else:
                path    = path_list[0][0]
                pattern = pattern_list[0]
            if fnmatch.fnmatchcase(path, pattern):
                return match_parts(path_list[1:], pattern_list[1:])
            return False

        def walk(node, path_list=None, vhdl_scope=None):
            if path_list is None:
                path_list = []
            if vhdl_scope is None:
                vhdl_scope = (self.file_type == libfst.Enum.FST_FT_VHDL)
            node_name = node.get("name")
            stop_walk = False
            if node_name:
                vhdl_var  = False
                is_struct = False
                if "contents" in node:
                    scope_type = node.get("type")
                    vhdl_scope = ((self.file_type == libfst.Enum.FST_FT_VHDL) or
                                  (scope_type in ("VHDL_ARCHITECTURE", 
                                                  "VHDL_PROCEDURE"   ,
                                                  "VHDL_FUNCTION"    ,
                                                  "VHDL_RECORD"      ,
                                                  "VHDL_PROCESS"     ,
                                                  "VHDL_BLOCK"       ,
                                                  "VHDL_FOR_GENERATE",
                                                  "VHDL_IF_GENERATE" ,
                                                  "VHDL_GENERATE"    ,
                                                  "VHDL_PACKAGE"     )))
                    is_struct = (scope_type in ("VCD_STRUCT", "VCD_UNION", "VHDL_RECORD"))
                else:
                    for attribute in node.get("attributes", []):
                        var_type = attribute.get("var_type")
                        if (var_type == "SVT_VHDL_SIGNAL"   or
                            var_type == "SVT_VHDL_VARIABLE" or 
                            var_type == "SVT_VHDL_CONSTANT" or
                            var_type == "SVT_VHDL_FILE"     or
                            var_type == "SVT_VHDL_MEMORY"   ):
                            vhdl_var = True
                            break
                is_vhdl = (vhdl_scope or vhdl_var)
                path_list.append((node_name, is_vhdl))
                if "handle" in node or (is_struct and struct_as_var):
                    if match_parts(path_list, pattern_list):
                        path_name_list = [name for name,is_vhdl in path_list]
                        var_list.append((path_name_list, node))
                        stop_walk = True
            if not stop_walk:
                for child in node.get("contents", []):
                    walk(child, path_list, vhdl_scope)
            if node_name:
                path_list.pop()

        if tree is None:
            tree = self.tree
        walk(tree)
        return var_list

    def close(self):
        if (self.reader is not None):
            self.reader.close()

    TIME_UNITS = (
       (  0, "s" ),
       ( -3, "ms"),
       ( -6, "us"),    # または "µs"
       ( -9, "ns"),
       (-12, "ps"),
       (-15, "fs"),
       (-18, "as"),
    )

    def format_time_scale(self, time_scale):
        for unit_scale, unit in reversed(self.TIME_UNITS):
            if time_scale <= unit_scale:
                value = 10 ** (unit_scale - time_scale)
                return f"{value:g} {unit}"
        return f"1e{time_scale} s"

    def format_timestamp(self, timestamp, time_scale=None):
        if time_scale is None:
            time_scale = self.time_scale
        for unit_scale, unit in self.TIME_UNITS:
            scale = time_scale - unit_scale
            if scale >= 0:
                value = timestamp * (10 ** scale)
                if value >= 1:
                    return f"{int(value)} {unit}"
            else:
                divisor = 10 ** (-scale)
                if timestamp >= divisor and timestamp % divisor == 0:
                    value = timestamp // divisor
                    return f"{int(value)} {unit}"
        for unit_scale, unit in self.TIME_UNITS:
            value = timestamp * (10 ** (time_scale - unit_scale))            
            if value >= 1:
                return f"{value:g} {unit}"
        unit_scale, unit = self.TIME_UNITS[-1]
        value = timestamp * (10 ** (time_scale - unit_scale))
        return f"{value:g} {unit}"

    def parse_timestamp(self, value, unit=None, time_scale=None):
        if unit is None:
            return int(value)
        if time_scale is None:
            time_scale = self.time_scale
        unit_scale = None
        for scale, name in self.TIME_UNITS:
            if name == unit:
                unit_scale = scale
                break;
        if unit_scale is None:
            raise ValueError(f"Unknown time unit:{unit}")
        timestamp = value * (10 ** (unit_scale - time_scale))
        return int(timestamp)

    def set_limit_time_range(self, start_time, end_time):
        self.reader.set_limit_time_range(start_time, end_time)

    def set_unlimited_time_range(self):
        self.reader.set_unlimited_time_range()

    def set_facility_process_mask(self, handle):
        self.reader.set_facility_process_mask(handle)
    
    def set_facility_process_mask_all(self):
        self.reader.set_facility_process_mask_all()
    
    def clear_facility_process_mask(self, handle):
        self.reader.clear_facility_process_mask(handle)
    
    def clear_facility_process_mask_all(self):
        self.reader.clear_facility_process_mask_all()

    def blocks(self):
        return self.reader.blocks()
    
    def print_info(self):
        print(f"File      : {self.file_name}")
        print(f"FileType  : {self.enum_name(self.FileType, self.file_type)}")
        print(f"Date      : {self.date}")
        print(f"Version   : {self.version}")
        print(f"StartTime : {self.format_timestamp(self.start_time)} ({self.start_time})")
        print(f"EndTime   : {self.format_timestamp(self.end_time)} ({self.end_time})")
        print(f"TimeScale : {self.format_time_scale(self.time_scale)} ({self.time_scale})")
        print(f"Signals   : {self.reader.var_count}")

