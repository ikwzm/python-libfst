/*********************************************************************************
 *
 *       Copyright (C) 2026 Ichiro Kawazome
 *       All rights reserved.
 * 
 *       Redistribution and use in source and binary forms, with or without
 *       modification, are permitted provided that the following conditions
 *       are met:
 * 
 *         1. Redistributions of source code must retain the above copyright
 *            notice, this list of conditions and the following disclaimer.
 * 
 *         2. Redistributions in binary form must reproduce the above copyright
 *            notice, this list of conditions and the following disclaimer in
 *            the documentation and/or other materials provided with the
 *            distribution.
 * 
 *       THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 *       "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 *       LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 *       A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT
 *       OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 *       SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 *       LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 *       DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 *       THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT 
 *       (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 *       OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 * 
 ********************************************************************************/
#include <Python.h>
#include <sys/mman.h>
#include <unistd.h>
#include <stdatomic.h>
#include <libfst/fstapi.h>

#ifndef PACKAGE_NAME
#define PACKAGE_NAME        libfst
#endif

#ifndef MODULE_NAME
#define MODULE_NAME         Enum
#endif

#define MODULE_VERSION      "0.0.1"
#define MODULE_AUTHOR       "Ichiro Kawazome"
#define MODULE_AUTHOR_EMAIL "ichiro_k@ca2-so-net.ne.jp"
#define MODULE_LICENSE      "BSD 2-Clause"
#define MODULE_DESCRIPTION  "GTKWave FST Enumeration Constants"

#define TO_STR(x)           #x
#define NAME_TO_STR(x)      TO_STR(x)
#define PACKAGE_NAME_STRING NAME_TO_STR(PACKAGE_NAME)
#define MODULE_NAME_STRING  NAME_TO_STR(MODULE_NAME)

static struct PyModuleDef enum_module = {
    PyModuleDef_HEAD_INIT,
    PACKAGE_NAME_STRING "." MODULE_NAME_STRING,
    MODULE_DESCRIPTION "\n"
    "License: " MODULE_LICENSE "\n"
    "Author:  " MODULE_AUTHOR  "\n"
    "Version: " MODULE_VERSION,
    -1,
    NULL,
};

#define PYINIT_FUNC_NAME(x) PyInit_ ## x
#define PYINIT_FUNC(x) PyMODINIT_FUNC PYINIT_FUNC_NAME(x)(void) 
PYINIT_FUNC(MODULE_NAME) {
    PyObject* m;

    m = PyModule_Create(&enum_module);
    if (m == NULL) {
        return NULL;
    }

#define ADD_INT(name)                                      \
    {                                                      \
        if (PyModule_AddIntConstant(m, #name, name) < 0)   \
            goto error;                                    \
    }

    /*
     * enum fstWriterPackType
     */
    ADD_INT( FST_WR_PT_ZLIB                );
    ADD_INT( FST_WR_PT_FASTLZ              );
    ADD_INT( FST_WR_PT_LZ4                 );

    /*
     * enum fstFileType
     */
    ADD_INT( FST_FT_MIN                    );
    ADD_INT( FST_FT_VERILOG                );
    ADD_INT( FST_FT_VHDL                   );
    ADD_INT( FST_FT_VERILOG_VHDL           );
    ADD_INT( FST_FT_MAX                    );

    /*
     * enum fstBlockType
     */
    ADD_INT( FST_BL_HDR                    );
    ADD_INT( FST_BL_VCDATA                 );
    ADD_INT( FST_BL_BLACKOUT               );
    ADD_INT( FST_BL_GEOM                   );
    ADD_INT( FST_BL_HIER                   );
    ADD_INT( FST_BL_VCDATA_DYN_ALIAS       );
    ADD_INT( FST_BL_HIER_LZ4               );
    ADD_INT( FST_BL_HIER_LZ4DUO            );
    ADD_INT( FST_BL_VCDATA_DYN_ALIAS2      );
    ADD_INT( FST_BL_ZWRAPPER               );
    ADD_INT( FST_BL_SKIP                   );

    /*
     * enum fstScopeType
     */
    ADD_INT( FST_ST_MIN                    );
    ADD_INT( FST_ST_VCD_MODULE             );
    ADD_INT( FST_ST_VCD_TASK               );
    ADD_INT( FST_ST_VCD_FUNCTION           );
    ADD_INT( FST_ST_VCD_BEGIN              );
    ADD_INT( FST_ST_VCD_FORK               );
    ADD_INT( FST_ST_VCD_GENERATE           );
    ADD_INT( FST_ST_VCD_STRUCT             );
    ADD_INT( FST_ST_VCD_UNION              );
    ADD_INT( FST_ST_VCD_CLASS              );
    ADD_INT( FST_ST_VCD_INTERFACE          );
    ADD_INT( FST_ST_VCD_PACKAGE            );
    ADD_INT( FST_ST_VCD_PROGRAM            );

    ADD_INT( FST_ST_VHDL_ARCHITECTURE      );
    ADD_INT( FST_ST_VHDL_PROCEDURE         );
    ADD_INT( FST_ST_VHDL_FUNCTION          );
    ADD_INT( FST_ST_VHDL_RECORD            );
    ADD_INT( FST_ST_VHDL_PROCESS           );
    ADD_INT( FST_ST_VHDL_BLOCK             );
    ADD_INT( FST_ST_VHDL_FOR_GENERATE      );
    ADD_INT( FST_ST_VHDL_IF_GENERATE       );
    ADD_INT( FST_ST_VHDL_GENERATE          );
    ADD_INT( FST_ST_VHDL_PACKAGE           );

    ADD_INT( FST_ST_SV_ARRAY               );
    ADD_INT( FST_ST_MAX                    );

    ADD_INT( FST_ST_GEN_ATTRBEGIN          );
    ADD_INT( FST_ST_GEN_ATTREND            );

    ADD_INT( FST_ST_VCD_SCOPE              );
    ADD_INT( FST_ST_VCD_UPSCOPE            );

    /*
     * enum fstVarType
     */
    ADD_INT( FST_VT_MIN                    );
    ADD_INT( FST_VT_VCD_EVENT              );
    ADD_INT( FST_VT_VCD_INTEGER            );
    ADD_INT( FST_VT_VCD_PARAMETER          );
    ADD_INT( FST_VT_VCD_REAL               );
    ADD_INT( FST_VT_VCD_REAL_PARAMETER     );
    ADD_INT( FST_VT_VCD_REG                );
    ADD_INT( FST_VT_VCD_SUPPLY0            );
    ADD_INT( FST_VT_VCD_SUPPLY1            );
    ADD_INT( FST_VT_VCD_TIME               );
    ADD_INT( FST_VT_VCD_TRI                );
    ADD_INT( FST_VT_VCD_TRIAND             );
    ADD_INT( FST_VT_VCD_TRIOR              );
    ADD_INT( FST_VT_VCD_TRIREG             );
    ADD_INT( FST_VT_VCD_TRI0               );
    ADD_INT( FST_VT_VCD_TRI1               );
    ADD_INT( FST_VT_VCD_WAND               );
    ADD_INT( FST_VT_VCD_WIRE               );
    ADD_INT( FST_VT_VCD_WOR                );
    ADD_INT( FST_VT_VCD_PORT               );
    ADD_INT( FST_VT_VCD_SPARRAY            );
    ADD_INT( FST_VT_VCD_REALTIME           );

    ADD_INT( FST_VT_GEN_STRING             );

    ADD_INT( FST_VT_SV_BIT                 );
    ADD_INT( FST_VT_SV_LOGIC               );
    ADD_INT( FST_VT_SV_INT                 );
    ADD_INT( FST_VT_SV_SHORTINT            );
    ADD_INT( FST_VT_SV_LONGINT             );
    ADD_INT( FST_VT_SV_BYTE                );
    ADD_INT( FST_VT_SV_ENUM                );
    ADD_INT( FST_VT_SV_SHORTREAL           );
    ADD_INT( FST_VT_MAX                    );

    /*
     * enum fstVarDir
     */
    ADD_INT( FST_VD_MIN                    );
    ADD_INT( FST_VD_IMPLICIT               );
    ADD_INT( FST_VD_INPUT                  );
    ADD_INT( FST_VD_OUTPUT                 );
    ADD_INT( FST_VD_INOUT                  );
    ADD_INT( FST_VD_BUFFER                 );
    ADD_INT( FST_VD_LINKAGE                );
    ADD_INT( FST_VD_MAX                    );

    /*
     * enum fstHierType
     */
    ADD_INT( FST_HT_MIN                    );
    ADD_INT( FST_HT_SCOPE                  );
    ADD_INT( FST_HT_UPSCOPE                );
    ADD_INT( FST_HT_VAR                    );
    ADD_INT( FST_HT_ATTRBEGIN              );
    ADD_INT( FST_HT_ATTREND                );
    ADD_INT( FST_HT_TREEBEGIN              );
    ADD_INT( FST_HT_TREEEND                );
    ADD_INT( FST_HT_MAX                    );

    /*
     * enum fstAttrType
     */
    ADD_INT( FST_AT_MIN                    );
    ADD_INT( FST_AT_MISC                   );
    ADD_INT( FST_AT_ARRAY                  );
    ADD_INT( FST_AT_ENUM                   );
    ADD_INT( FST_AT_PACK                   );
    ADD_INT( FST_AT_MAX                    );

    /*
     * enum fstMiscType
     */
    ADD_INT( FST_MT_MIN                    );
    ADD_INT( FST_MT_COMMENT                );
    ADD_INT( FST_MT_ENVVAR                 );
    ADD_INT( FST_MT_SUPVAR                 );
    ADD_INT( FST_MT_PATHNAME               );
    ADD_INT( FST_MT_SOURCESTEM             );
    ADD_INT( FST_MT_SOURCEISTEM            );
    ADD_INT( FST_MT_VALUELIST              );
    ADD_INT( FST_MT_ENUMTABLE              );
    ADD_INT( FST_MT_UNKNOWN                );
    ADD_INT( FST_MT_MAX                    );
        
    /*
     * enum fstArrayType
     */
    ADD_INT( FST_AR_MIN                    );
    ADD_INT( FST_AR_NONE                   );
    ADD_INT( FST_AR_UNPACKED               );
    ADD_INT( FST_AR_PACKED                 );
    ADD_INT( FST_AR_SPARSE                 );
    ADD_INT( FST_AR_MAX                    );

    /*
     * enum fstEnumValueType
     */
    ADD_INT( FST_EV_SV_INTEGER             );
    ADD_INT( FST_EV_SV_BIT                 );
    ADD_INT( FST_EV_SV_LOGIC               );
    ADD_INT( FST_EV_SV_INT                 );
    ADD_INT( FST_EV_SV_SHORTINT            );
    ADD_INT( FST_EV_SV_LONGINT             );
    ADD_INT( FST_EV_SV_BYTE                );
    ADD_INT( FST_EV_SV_UNSIGNED_INTEGER    );
    ADD_INT( FST_EV_SV_UNSIGNED_BIT        );
    ADD_INT( FST_EV_SV_UNSIGNED_LOGIC      );
    ADD_INT( FST_EV_SV_UNSIGNED_INT        );
    ADD_INT( FST_EV_SV_UNSIGNED_SHORTINT   );
    ADD_INT( FST_EV_SV_UNSIGNED_LONGINT    );
    ADD_INT( FST_EV_SV_UNSIGNED_BYTE       );

    ADD_INT( FST_EV_REG                    );
    ADD_INT( FST_EV_TIME                   );
    ADD_INT( FST_EV_MAX                    );

    /*
     * enum fstPackType
     */
    ADD_INT( FST_PT_NONE                   );
    ADD_INT( FST_PT_UNPACKED               );
    ADD_INT( FST_PT_PACKED                 );
    ADD_INT( FST_PT_TAGGED_PACKED          );
    ADD_INT( FST_PT_MAX                    );

    /*
     * enum fstSupplementalVarType
     */
    ADD_INT( FST_SVT_MIN                   );
    ADD_INT( FST_SVT_NONE                  );
    ADD_INT( FST_SVT_VHDL_SIGNAL           );
    ADD_INT( FST_SVT_VHDL_VARIABLE         );
    ADD_INT( FST_SVT_VHDL_CONSTANT         );
    ADD_INT( FST_SVT_VHDL_FILE             );
    ADD_INT( FST_SVT_VHDL_MEMORY           );
    ADD_INT( FST_SVT_MAX                   );

    /*
     * enum fstSupplementalDataType
     */
    ADD_INT( FST_SDT_MIN                   );
    ADD_INT( FST_SDT_NONE                  );
    ADD_INT( FST_SDT_VHDL_BOOLEAN          );
    ADD_INT( FST_SDT_VHDL_BIT              );
    ADD_INT( FST_SDT_VHDL_BIT_VECTOR       );
    ADD_INT( FST_SDT_VHDL_STD_ULOGIC       );
    ADD_INT( FST_SDT_VHDL_STD_ULOGIC_VECTOR);
    ADD_INT( FST_SDT_VHDL_STD_LOGIC        );
    ADD_INT( FST_SDT_VHDL_STD_LOGIC_VECTOR );
    ADD_INT( FST_SDT_VHDL_UNSIGNED         );
    ADD_INT( FST_SDT_VHDL_SIGNED           );
    ADD_INT( FST_SDT_VHDL_INTEGER          );
    ADD_INT( FST_SDT_VHDL_REAL             );
    ADD_INT( FST_SDT_VHDL_NATURAL          );
    ADD_INT( FST_SDT_VHDL_POSITIVE         );
    ADD_INT( FST_SDT_VHDL_TIME             );
    ADD_INT( FST_SDT_VHDL_CHARACTER        );
    ADD_INT( FST_SDT_VHDL_STRING           );
    ADD_INT( FST_SDT_MAX                   );

    ADD_INT( FST_SDT_SVT_SHIFT_COUNT       );
    ADD_INT( FST_SDT_ABS_MAX               );
        
    return m;
 error:
    Py_DECREF(m);
    return NULL;
}
