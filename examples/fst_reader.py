#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-2-Clause
# Copyright (c) 2026 ikwzm

import libfst
from enum import IntEnum

class FST_Reader:
    def __init__(self, file_name):
        self.reader    = libfst.Reader(file_name)
        self.file_name = file_name
        self.file_type = self.reader.file_type
        self.date      = self.reader.date.rstrip("\n\r")
        self.version   = self.reader.version.rstrip("\n\r")
        self.tree      = {"contents": []}

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
        attributes = []
        stack      = [self.tree]
        
        for item in self.reader.hiers():
            if   isinstance(item, libfst.hier.Scope):
                node = {
                    "name"       : item.name,
                    "type"       : self.enum_name(self.ScopeType,item.scope_type),
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

    def close(self):
        if (self.reader is not None):
            self.reader.close()

    def print_info(self):
        print(f"File      : {self.file_name}")
        print(f"FileType  : {self.enum_name(self.FileType, self.file_type)}")
        print(f"Date      : {self.date}")
        print(f"Version   : {self.version}")
        print(f"StartTime : {self.reader.start_time}")
        print(f"EndTime   : {self.reader.end_time}")
        print(f"Signals   : {self.reader.var_count}")
