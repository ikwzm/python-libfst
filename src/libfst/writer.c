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
#include <stdbool.h>
#include <stdatomic.h>
#include <fstapi.h>

#ifndef PACKAGE_NAME
#define PACKAGE_NAME        libfst
#endif

#ifndef MODULE_NAME
#define MODULE_NAME         writer
#endif

#ifndef OBJECT_NAME
#define OBJECT_NAME         Writer
#endif

#define MODULE_VERSION      "0.0.8"
#define MODULE_AUTHOR       "Ichiro Kawazome"
#define MODULE_AUTHOR_EMAIL "ichiro_k@ca2-so-net.ne.jp"
#define MODULE_LICENSE      "BSD 2-Clause"
#define MODULE_DESCRIPTION  "GTKWave FST Writer Module"

#define TO_STR(x)           #x
#define NAME_TO_STR(x)      TO_STR(x)
#define PACKAGE_NAME_STRING NAME_TO_STR(PACKAGE_NAME)
#define MODULE_NAME_STRING  NAME_TO_STR(MODULE_NAME)
#define OBJECT_NAME_STRING  NAME_TO_STR(OBJECT_NAME)

typedef struct {
    PyObject_HEAD
    fstWriterContext* ctx;
} writer_object;

static PyObject*
writer_object_new(PyTypeObject* type, PyObject* args, PyObject* kwdict)
{
    writer_object* self;
    self = (writer_object*)type->tp_alloc(type, 0);
    if (self != NULL) {
        self->ctx = NULL;
    }
    return (PyObject*)self;
}

static int
writer_object_init(writer_object* self, PyObject* args, PyObject* kwdict)
{
    static char* kwlist[] = { "filename", "use_compressed_hier", NULL };
    const  char* filename;
    int          use_compressed_hier = 1;

    if (!PyArg_ParseTupleAndKeywords(args, kwdict, "s|i", kwlist, &filename, &use_compressed_hier)) {
        return -1;
    }

    if (self->ctx != NULL) {
        fstWriterClose(self->ctx);
        self->ctx = NULL;
    }

    self->ctx = fstWriterCreate(filename, use_compressed_hier);
    if (self->ctx == NULL) {
        PyErr_Format(PyExc_OSError, "cannot create FST file \"%s\"", filename);
        return -1;
    }

    return 0;
}

static void
writer_object_dealloc(writer_object* self)
{
    if (self->ctx != NULL) {
        fstWriterClose(self->ctx);
        self->ctx = NULL;
    }
    Py_TYPE(self)->tp_free((PyObject*)self);
}

PyDoc_STRVAR(
    writer_close_doc,
    "Close the FST writer.\n"
    "\n"
    "Flush any remaining data, close the underlying output file,\n"
    "and release all resources associated with this writer.\n"
    "\n"
    "After this method returns, the writer object is closed and\n"
    "must not be used for further writing operations.\n"
    "\n"
    "Calling close() multiple times is safe and has no effect after\n"
    "the writer has already been closed.\n"
    "\n"
    "Returns:\n"
    "    None.\n"
);
static PyObject*
writer_close(writer_object* self, PyObject* Py_UNUSED(args))
{
    if (self->ctx != NULL) {
        fstWriterClose(self->ctx);
        self->ctx = NULL;
    }
    Py_RETURN_NONE;
}

PyDoc_STRVAR(
    writer_flush_context_doc,
    "Mark the current FST writer context as pending for flushing.\n"
    "\n"
    "The actual context flush is performed later by the FST writer\n"
    "when appropriate.\n"
    "\n"
    "Returns:\n"
    "    None.\n"
);
static PyObject*
writer_flush_context(writer_object* self, PyObject* Py_UNUSED(args))
{
    if (self->ctx == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "FST writer is closed");
        return NULL;
    }
    
    fstWriterFlushContext(self->ctx);

    Py_RETURN_NONE;
}

PyDoc_STRVAR(
    writer_set_file_type_doc,
    "Set the FST file type stored in the FST file header.\n"
    "\n"
    "Args:\n"
    "    filetype (int): File type identifier.\n"
    "\n"
    "Raises:\n"
    "    ValueError: If the specified file type is invalid.\n"
    "\n"
    "Note:\n"
    "    The file type value is written directly to the FST file header.\n"
    "    The underlying FST writer library provides only a setter API;\n"
    "    the current file type cannot be queried.\n"
    "\n"
    "Returns:\n"
    "    None.\n"
);
static PyObject *
writer_set_file_type(writer_object* self, PyObject* args, PyObject* kwdict)
{
    static const char* kwlist[] = { "filetype", NULL };
    int                file_type;

    if (!PyArg_ParseTupleAndKeywords(args, kwdict, "i", kwlist, &file_type))
        return NULL;

    if ((file_type < FST_FT_MIN) || (file_type > FST_FT_MAX)) {
        PyErr_Format(PyExc_ValueError, "invalid FST file type: %d", file_type);
        return NULL;
    }

    if (self->ctx == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "FST writer is closed");
        return NULL;
    }

    fstWriterSetFileType(self->ctx, (enum fstFileType)file_type);

    Py_RETURN_NONE;
}

PyDoc_STRVAR(
    writer_set_pack_type_doc,
    "Set the compression pack type used for writing value changes.\n"
    "\n"
    "Args:\n"
    "    packtype (int): Compression pack type.\n"
    "\n"
    "Valid values are:\n"
    "    FST_WR_PT_ZLIB\n"
    "    FST_WR_PT_FASTLZ\n"
    "    FST_WR_PT_LZ4\n"
    "\n"
    "Raises:\n"
    "    ValueError: If an invalid pack type is specified.\n"
    "\n"
    "Note:\n"
    "    This setting affects subsequent value changes written to the\n"
    "    FST file.\n"
    "    The underlying FST writer library provides only a setter API;\n"
    "    the current pack type cannot be queried.\n"
    "\n"
    "Returns:\n"
    "    None.\n"
);
static PyObject*
writer_set_pack_type(writer_object* self, PyObject* args, PyObject* kwdict)
{
    static const char* kwlist[] = { "packtype", NULL };
    int                pack_type;

    if (!PyArg_ParseTupleAndKeywords(args, kwdict, "i", kwlist, &pack_type))
        return NULL;

    if ((pack_type != FST_WR_PT_ZLIB)   &&
        (pack_type != FST_WR_PT_FASTLZ) &&
        (pack_type != FST_WR_PT_LZ4)) {
        PyErr_Format(PyExc_ValueError, "invalid FST pack type: %d", pack_type);
        return NULL;
    }

    if (self->ctx == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "FST writer is closed");
        return NULL;
    }

    fstWriterSetPackType(self->ctx,(enum fstWriterPackType)pack_type);

    Py_RETURN_NONE;
}

PyDoc_STRVAR(
    writer_set_date_doc,
    "Set the date string stored in the FST file header.\n"
    "\n"
    "Args:\n"
    "    date (str): Date string to write to the FST file header.\n"
    "\n"
    "Note:\n"
    "    The string is written directly to the FST file header.\n"
    "    If its length exceeds the header field size, it is silently\n"
    "    truncated.\n"
    "    The underlying FST writer library provides only a setter API;\n"
    "    the current date string cannot be queried.\n"
    "\n"
    "Returns:\n"
    "    None.\n"
);
static PyObject*
writer_set_date(writer_object* self, PyObject* args, PyObject* kwdict)
{
    static const char* kwlist[] = { "date", NULL };
    const char*        date;

    if (!PyArg_ParseTupleAndKeywords(args, kwdict, "s", kwlist, &date))
        return NULL;

    if (self->ctx == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "FST writer is closed");
        return NULL;
    }

    fstWriterSetDate(self->ctx, date);

    Py_RETURN_NONE;
}

PyDoc_STRVAR(
    writer_set_version_doc,
    "Set the version string stored in the FST file header.\n"
    "\n"
    "Args:\n"
    "    version (str): Version string to write to the FST file header.\n"
    "\n"
    "Note:\n"
    "    The string is written directly to the FST file header.\n"
    "    If its length exceeds the header field size, it is silently\n"
    "    truncated.\n"
    "    The underlying FST writer library provides only a setter API;\n"
    "    the current version string cannot be queried.\n"
    "\n"
    "Returns:\n"
    "    None.\n"
);
static PyObject*
writer_set_version(writer_object* self, PyObject* args, PyObject* kwdict)
{
    static const char* kwlist[] = { "version", NULL };
    const char*        version;

    if (!PyArg_ParseTupleAndKeywords(args, kwdict, "s", kwlist, &version))
        return NULL;

    if (self->ctx == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "FST writer is closed");
        return NULL;
    }

    fstWriterSetVersion(self->ctx, version);

    Py_RETURN_NONE;
}

PyDoc_STRVAR(
    writer_set_time_scale_doc,
    "Set the time scale used for timestamps in the FST file.\n"
    "\n"
    "Args:\n"
    "    timescale (int or str):\n"
    "        Integer time scale value or a string representation\n"
    "        of the time scale.\n"
    "\n"
    "        Examples:\n"
    "            1\n"
    "            \"1ns\"\n"
    "\n"
    "Returns:\n"
    "    None.\n"
    "\n"
    "Note:\n"
    "    When a string is specified, the value is passed to\n"
    "    fstWriterSetTimescaleFromString(). This function does not\n"
    "    provide an error return value, so invalid strings may not\n"
    "    be detected.\n"
);
static PyObject*
writer_set_time_scale(writer_object* self, PyObject* args, PyObject* kwdict)
{
    static const char* kwlist[] = { "timescale", NULL };
    PyObject*          value;

    if (!PyArg_ParseTupleAndKeywords(args, kwdict, "O", kwlist, &value))
        return NULL;

    if (PyUnicode_Check(value)) {
        const char* time_scale = PyUnicode_AsUTF8(value);
        if (time_scale == NULL)
            return NULL;
        if (self->ctx == NULL) {
            PyErr_SetString(PyExc_RuntimeError, "FST writer is closed");
            return NULL;
        }
        fstWriterSetTimescaleFromString(self->ctx, time_scale);
    } else if (PyLong_Check(value)) {
        long time_scale = PyLong_AsLong(value);
        if ((time_scale == -1) && PyErr_Occurred())
            return NULL;
        if ((time_scale < INT_MIN) || (time_scale > INT_MAX)) {
            PyErr_SetString(PyExc_OverflowError, "'timescale' is out of range");
            return NULL;
        }
        if (self->ctx == NULL) {
            PyErr_SetString(PyExc_RuntimeError, "FST writer is closed");
            return NULL;
        }
        fstWriterSetTimescale(self->ctx, (int)time_scale);
    } else {
        PyErr_SetString(PyExc_TypeError, "'timescale' must be an int or str");
        return NULL;
    }

    Py_RETURN_NONE;
}

PyDoc_STRVAR(
    writer_set_time_zero_doc,
    "Set the simulation time zero stored in the FST file header.\n"
    "\n"
    "Args:\n"
    "    time (int): Time-zero offset to write to the FST file header.\n"
    "        The value is stored as a signed 64-bit integer.\n"
);
static PyObject *
writer_set_time_zero(writer_object* self, PyObject* args, PyObject* kwdict)
{
    static const char* kwlist[] = { "time", NULL };
    long long          time;

    if (!PyArg_ParseTupleAndKeywords(args, kwdict, "L", kwlist, &time))
        return NULL;

    if (self->ctx == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "FST writer is closed");
        return NULL;
    }

    fstWriterSetTimezero(self->ctx, (int64_t)time);

    Py_RETURN_NONE;
}

PyDoc_STRVAR(
    writer_set_dump_size_limit_doc,
    "Set the maximum dump size for the FST file.\n"
    "\n"
    "Args:\n"
    "    numbytes (int): Maximum number of bytes that may be written\n"
    "        to the FST file.\n"
    "\n"
    "Note:\n"
    "    Once the configured limit is reached, the writer stops writing\n"
    "    additional waveform data. The underlying FST writer library\n"
    "    provides only a setter API; the current limit cannot be queried."
);
static PyObject* 
writer_set_dump_size_limit(writer_object* self, PyObject* args, PyObject* kwdict)
{
    static const char* kwlist[] = { "numbytes", NULL };
    unsigned long long numbytes;

    if (!PyArg_ParseTupleAndKeywords(args, kwdict, "K", kwlist, &numbytes))
        return NULL;

    if (self->ctx == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "FST writer is closed");
        return NULL;
    }

    fstWriterSetDumpSizeLimit(self->ctx, (uint64_t)numbytes);

    Py_RETURN_NONE;
}

PyDoc_STRVAR(
    writer_set_repack_on_close_doc,
    "Enable or disable repacking the FST file when the writer is closed.\n"
    "\n"
    "Args:\n"
    "    enable (bool): If True, the FST file is repacked when the\n"
    "        writer is closed. If False, repacking is disabled.\n"
    "\n"
    "Note:\n"
    "    Repacking may reduce the final file size, but it can increase\n"
    "    the time required to close the writer. The underlying FST\n"
    "    writer library provides only a setter API; the current setting\n"
    "    cannot be queried."
);
static PyObject *
writer_set_repack_on_close(writer_object* self, PyObject* args, PyObject* kwdict)
{
    static const char* kwlist[] = { "enable", NULL };
    PyObject*          value;
    int                enable;

    if (!PyArg_ParseTupleAndKeywords(args, kwdict, "O", kwlist, &value))
        return NULL;

    enable = PyObject_IsTrue(value);
    if (enable < 0)
        return NULL;

    if (self->ctx == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "FST writer is closed");
        return NULL;
    }

    fstWriterSetRepackOnClose(self->ctx, enable);

    Py_RETURN_NONE;
}

PyDoc_STRVAR(
    writer_set_parallel_mode_doc,
    "Enable or disable parallel compression mode.\n"
    "\n"
    "Args:\n"
    "    enable (bool): Enable or disable parallel compression.\n"
    "\n"
    "Warning:\n"
    "    If libfst was built without FST_WRITER_PARALLEL support,\n"
    "    enabling parallel mode causes the underlying library to\n"
    "    terminate the process."
);
static PyObject*
writer_set_parallel_mode(writer_object* self, PyObject* args, PyObject* kwdict)
{
    static const char* kwlist[] = { "enable", NULL };
    PyObject*          value;
    int                enable;

    if (!PyArg_ParseTupleAndKeywords(args, kwdict, "O", kwlist, &value))
        return NULL;

    enable = PyObject_IsTrue(value);
    if (enable < 0)
        return NULL;

    if (self->ctx == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "FST writer is closed");
        return NULL;
    }

    fstWriterSetParallelMode(self->ctx, enable);

    Py_RETURN_NONE;
}

PyDoc_STRVAR(
    writer_set_scope_doc,
    "Begin a new scope in the FST hierarchy.\n"
    "\n"
    "Args:\n"
    "    scopetype (int): Scope type value.\n"
    "        Valid values range from FST_ST_MIN (0) to\n"
    "        FST_ST_MAX (22).\n"
    "    name (str, optional): Scope name.\n"
    "    component (str, optional): Scope component name.\n"
    "\n"
    "Returns:\n"
    "    None.\n"
);
static PyObject*
writer_set_scope(writer_object* self, PyObject* args, PyObject* kwdict)
{
    static const char* kwlist[]  = { "scopetype", "name", "component", NULL };
    int                scopetype;
    const char*        name      = NULL;
    const char*        component = NULL;

    if (!PyArg_ParseTupleAndKeywords(args, kwdict, "i|zz", kwlist, &scopetype, &name, &component))
        return NULL;

    if ((scopetype < FST_ST_MIN) || (FST_ST_MAX < scopetype)) {
        PyErr_Format(PyExc_ValueError, "invalid FST scope type: %d", scopetype);
        return NULL;
    }        

    if (self->ctx == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "FST writer is closed");
        return NULL;
    }

    fstWriterSetScope(self->ctx, (enum fstScopeType)scopetype, name, component);

    Py_RETURN_NONE;
}

PyDoc_STRVAR(
    writer_set_upscope_doc,
    "End the current scope in the FST hierarchy.\n"
    "\n"
    "This writes an upscope marker to the FST hierarchy.\n"
    "\n"
    "Returns:\n"
    "    None.\n"
);
static PyObject*
writer_set_upscope(writer_object* self, PyObject* Py_UNUSED(args))
{
    if (self->ctx == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "FST writer is closed");
        return NULL;
    }

    fstWriterSetUpscope(self->ctx);

    Py_RETURN_NONE;
}

PyDoc_STRVAR(
    writer_set_attr_begin_doc,
    "Begin an attribute entry in the FST hierarchy.\n"
    "\n"
    "Args:\n"
    "    attrtype (int): Attribute type.\n"
    "    subtype (int): Attribute subtype.\n"
    "    name (str, optional): Attribute name.\n"
    "    arg (int, optional): Attribute argument value. Defaults to 0.\n"
    "\n"
    "Note:\n"
    "    The attribute entry is written directly to the FST hierarchy.\n"
    "    If attrtype or subtype is invalid, the underlying FST writer\n"
    "    library replaces it with a default value.\n"
    "\n"
    "Returns:\n"
    "    None.\n"
);
static PyObject*
writer_set_attr_begin(writer_object* self, PyObject* args, PyObject* kwdict)
{
    static const char* kwlist[] = { "attrtype", "subtype", "name", "arg", NULL };
    int                attrtype;
    int                subtype;
    const char*        name = NULL;
    unsigned long long arg  = 0;

    if (!PyArg_ParseTupleAndKeywords(args, kwdict, "ii|zK", kwlist, &attrtype, &subtype, &name, &arg)) {
        return NULL;
    }

    if (self->ctx == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "FST writer is closed");
        return NULL;
    }

    fstWriterSetAttrBegin(self->ctx, (enum fstAttrType)attrtype, subtype, name, (uint64_t)arg);

    Py_RETURN_NONE;
}

PyDoc_STRVAR(
    writer_set_attr_end_doc,
    "End the current attribute entry in the FST hierarchy.\n"
    "\n"
    "This function writes an attribute end marker to the FST\n"
    "hierarchy data.\n"
    "\n"
    "Returns:\n"
    "    None.\n"
);
static PyObject*
writer_set_attr_end(writer_object* self, PyObject* Py_UNUSED(args))
{
    if (self->ctx == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "FST writer is closed");
        return NULL;
    }

    fstWriterSetAttrEnd(self->ctx);

    Py_RETURN_NONE;
}

PyDoc_STRVAR(
    writer_set_comment_doc,
    "Write a comment attribute to the FST hierarchy.\n"
    "\n"
    "Args:\n"
    "    comment (str): Comment string to write.\n"
    "\n"
    "Note:\n"
    "    The comment is stored as an FST hierarchy attribute.\n"
    "    Newline characters ('\\\\n') and carriage return characters\n"
    "    ('\\\\r') in the comment string are replaced with spaces.\n"
    "    The underlying FST writer library provides only a setter API;\n"
    "    written comments cannot be queried.\n"
    "\n"
    "Returns:\n"
    "    None.\n"
);
static PyObject*
writer_set_comment(writer_object* self, PyObject* args, PyObject* kwdict)
{
    static const char* kwlist[] = { "comment", NULL };
    const char*        comment  = NULL;

    if (!PyArg_ParseTupleAndKeywords(args, kwdict, "s", kwlist, &comment))
        return NULL;

    if (self->ctx == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "FST writer is closed");
        return NULL;
    }

    fstWriterSetComment(self->ctx, comment);

    Py_RETURN_NONE;
}

PyDoc_STRVAR(
    writer_set_env_var_doc,
    "Write an environment variable attribute to the FST hierarchy.\n"
    "\n"
    "Args:\n"
    "    var (str): Environment variable string to write.\n"
    "\n"
    "Note:\n"
    "    The environment variable information is stored as an FST\n"
    "    hierarchy attribute (FST_MT_ENVVAR).\n"
    "    Newline characters ('\\\\n') and carriage return characters\n"
    "    ('\\\\r') in the string are replaced with spaces.\n"
    "    The underlying FST writer library provides only a setter API;\n"
    "    written environment variable information cannot be queried.\n"
    "\n"
    "Returns:\n"
    "    None.\n"
);
static PyObject*
writer_set_env_var(writer_object* self, PyObject* args, PyObject* kwdict)
{
    static const char* kwlist[] = { "var", NULL };
    const char*        var      = NULL;

    if (!PyArg_ParseTupleAndKeywords(args, kwdict, "s", kwlist, &var))
        return NULL;

    if (self->ctx == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "FST writer is closed");
        return NULL;
    }

    fstWriterSetEnvVar(self->ctx, var);

    Py_RETURN_NONE;
}

PyDoc_STRVAR(
    writer_set_value_list_doc,
    "Write a value list attribute to the FST hierarchy.\n"
    "\n"
    "Args:\n"
    "    valuelist (str): Value list string to write.\n"
    "\n"
    "Note:\n"
    "    The value list is stored as an FST hierarchy attribute\n"
    "    (FST_MT_VALUELIST).\n"
    "    Newline characters ('\\\\n') and carriage return characters\n"
    "    ('\\\\r') in the value list string are replaced with spaces.\n"
    "    The underlying FST writer library provides only a setter API;\n"
    "    written value list information cannot be queried.\n"
    "\n"
    "Returns:\n"
    "    None.\n"
);
static PyObject*
writer_set_value_list(writer_object* self, PyObject* args, PyObject* kwdict)
{
    static const char* kwlist[] = { "valuelist", NULL };
    const char*        vl       = NULL;

    if (!PyArg_ParseTupleAndKeywords(args, kwdict, "s", kwlist, &vl))
        return NULL;

    if (self->ctx == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "FST writer is closed");
        return NULL;
    }

    fstWriterSetValueList(self->ctx, vl);

    Py_RETURN_NONE;
}

PyDoc_STRVAR(
    writer_set_source_statement_doc,
    "Write source location information to the FST hierarchy.\n"
    "\n"
    "Args:\n"
    "    path (str): Source file path.\n"
    "    linenumber (int): Source line number.\n"
    "    use_realpath (bool): If true, resolve the path to a real path\n"
    "        before storing it.\n"
    "\n"
    "Note:\n"
    "    The source location information is stored as FST hierarchy\n"
    "    attributes (FST_MT_PATHNAME and FST_MT_SOURCESTEM).\n"
    "    The source path may be shared by multiple source statements\n"
    "    using an internal path index.\n"
    "    The underlying FST writer library provides only a setter API;\n"
    "    written source information cannot be queried.\n"
    "\n"
    "Returns:\n"
    "    None.\n"
);
static PyObject*
writer_set_source_statement(writer_object* self, PyObject* args, PyObject* kwdict)
{
    static const char* kwlist[] = { "path", "linenumber", "use_realpath", NULL };
    const char*        path = NULL;
    unsigned int       line;
    int                use_realpath;

    if (!PyArg_ParseTupleAndKeywords(args, kwdict, "sIp", kwlist, &path, &line, &use_realpath))
        return NULL;

    if (self->ctx == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "FST writer is closed");
        return NULL;
    }

    fstWriterSetSourceStem(self->ctx, path, line, (unsigned int)use_realpath);

    Py_RETURN_NONE;
}

PyDoc_STRVAR(
    writer_set_source_instantiation_statement_doc,
    "Write source instantiation location information to the FST hierarchy.\n"
    "\n"
    "Args:\n"
    "    path (str): Source file path of the instantiation.\n"
    "    linenumber (int): Source line number of the instantiation.\n"
    "    use_realpath (bool): If true, resolve the path to a real path\n"
    "        before storing it.\n"
    "\n"
    "Note:\n"
    "    The source instantiation information is stored as FST hierarchy\n"
    "    attributes (FST_MT_PATHNAME and FST_MT_SOURCEISTEM).\n"
    "    The source path may be shared by multiple source locations\n"
    "    using an internal path index.\n"
    "    The underlying FST writer library provides only a setter API;\n"
    "    written source instantiation information cannot be queried.\n"
    "\n"
    "Returns:\n"
    "    None.\n"
);
static PyObject*
writer_set_source_instantiation_statement(writer_object* self, PyObject* args, PyObject* kwdict)
{
    static const char* kwlist[] = { "path", "linenumber", "use_realpath", NULL };
    const char*        path = NULL;
    unsigned int       line;
    int                use_realpath;

    if (!PyArg_ParseTupleAndKeywords(args, kwdict, "sIp", kwlist, &path, &line, &use_realpath))
        return NULL;

    if (self->ctx == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "FST writer is closed");
        return NULL;
    }

    fstWriterSetSourceInstantiationStem(self->ctx, path, line, (unsigned int)use_realpath);

    Py_RETURN_NONE;
}

PyDoc_STRVAR(
    writer_create_var_doc,
    "Create a variable in the FST hierarchy.\n"
    "\n"
    "This method creates a Verilog/SystemVerilog variable using\n"
    "fstWriterCreateVar().\n"
    "If supplemental type information is specified, the extended\n"
    "fstWriterCreateVar2() API is used.\n"
    "\n"
    "Args:\n"
    "    var_type (int): Variable type (fstVarType).\n"
    "    direction (int): Variable direction (fstVarDir).\n"
    "    length (int): Variable width or size in bits.\n"
    "    name (str): Variable name.\n"
    "    alias (int, optional): Handle of an existing variable to use\n"
    "        as an alias. Default is 0 (no alias).\n"
    "    supplemental_type (str, optional): Supplemental type information.\n"
    "        If specified, the extended FST variable creation API\n"
    "        (fstWriterCreateVar2) is used. This is mainly intended for\n"
    "        VHDL or other languages requiring additional type metadata.\n"
    "    supplemental_var_type (int, optional): Supplemental variable type\n"
    "        identifier. Used only when supplemental_type is specified.\n"
    "    supplemental_data_type (int, optional): Supplemental data type\n"
    "        identifier. Used only when supplemental_type is specified.\n"
    "\n"
    "Returns:\n"
    "    int: Handle of the created variable.\n"
    "\n"
    "Raises:\n"
    "    ValueError: If var_type or direction is invalid, or if the\n"
    "        variable name is empty.\n"
    "    RuntimeError: If the FST writer has already been closed.\n"
    "\n"
    "Note:\n"
    "    When supplemental_type is specified, an additional FST hierarchy\n"
    "    attribute (FST_MT_SUPVAR) is written to store supplemental type\n"
    "    information before creating the variable.\n"
    "    For normal Verilog/SystemVerilog variables, supplemental\n"
    "    arguments should be omitted.\n"
);
static PyObject*
writer_create_var(writer_object* self, PyObject* args, PyObject* kwdict)
{
    static const char* kwlist[] = {"var_type", "direction", "length", "name", "alias", 
                                   "supplemental_type",
                                   "supplemental_var_type", 
                                   "supplemental_data_type",
                                   NULL
    };
    int                var_type;
    int                direction;
    unsigned int       length;
    const char*        name;
    unsigned int       alias       = 0;
    const char*        supp_type   = NULL;
    int                supp_v_type = 0;
    int                supp_d_type = 0;
    fstHandle          handle;

    if (!PyArg_ParseTupleAndKeywords(args, kwdict, "iiIs|Izii", kwlist,
                                     &var_type, &direction, &length, &name, &alias,
                                     &supp_type, &supp_v_type, &supp_d_type))
        return NULL;

    if ((var_type  < FST_VT_MIN) || (var_type  > FST_VT_MAX)) {
        PyErr_Format(PyExc_ValueError, "invalid FST variable type: %d", var_type);
        return NULL;
    }

    if ((direction < FST_VD_MIN) || (direction > FST_VD_MAX)) {
        PyErr_Format(PyExc_ValueError, "invalid FST variable direction: %d", direction);
        return NULL;
    }

    if (name == NULL || name[0] == '\0') {
        PyErr_SetString(PyExc_ValueError, "variable name must not be empty");
        return NULL;
    }

    if (supp_type != NULL) {
        if ((supp_v_type < FST_SVT_MIN) || (supp_v_type > FST_SVT_MAX)) {
            PyErr_Format(PyExc_ValueError, "invalid FST supplemental variable type: %d", supp_v_type);
            return NULL;
        }
        if ((supp_d_type < FST_SDT_MIN) || (supp_d_type > FST_SDT_MAX)) {
            PyErr_Format(PyExc_ValueError, "invalid FST supplemental data type: %d", supp_d_type);
            return NULL;
        }
    }
    
    if (self->ctx == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "FST writer is closed");
        return NULL;
    }

    if (supp_type != NULL) {
        handle = fstWriterCreateVar2(
                    self->ctx,
                    (enum fstVarType)var_type ,
                    (enum fstVarDir )direction,
                    length,
                    name,
                    (fstHandle)alias,
                    supp_type,
                    (enum fstSupplementalVarType )supp_v_type,
                    (enum fstSupplementalDataType)supp_d_type);
    }
    else {
        handle = fstWriterCreateVar(
                    self->ctx,
                    (enum fstVarType)var_type ,
                    (enum fstVarDir )direction,
                    length,
                    name,
                    (fstHandle)alias);
    }

    return PyLong_FromUnsignedLong(handle);
}

PyDoc_STRVAR(
    writer_create_enum_table_doc,
    "Create an enumeration table in the FST hierarchy.\n"
    "\n"
    "Args:\n"
    "    name (str): Enumeration table name.\n"
    "    literals (list[str]): List of enumeration literal names.\n"
    "    values (list[str]): List of encoded binary values corresponding\n"
    "        to each literal.\n"
    "    min_valbits (int, optional): Minimum width of encoded values.\n"
    "        Default is 0.\n"
    "\n"
    "Returns:\n"
    "    int: Handle of the created enumeration table.\n"
    "\n"
    "Raises:\n"
    "    ValueError: If literals and values have different lengths,\n"
    "        or if the list is empty.\n"
    "    TypeError: If literals or values are not lists of strings.\n"
    "    RuntimeError: If the FST writer has already been closed.\n"
);
static PyObject*
writer_create_enum_table(writer_object* self, PyObject* args, PyObject* kwdict)
{
    static const char* kwlist[] = { "name", "literals", "values", "min_valbits", NULL };
    const char*        name;
    PyObject*          literals;
    PyObject*          values;
    unsigned int       min_valbits = 0;

    const char**       lit_array = NULL;
    const char**       val_array = NULL;

    Py_ssize_t         elem_count;
    fstEnumHandle      handle = 0;

    if (!PyArg_ParseTupleAndKeywords(args, kwdict, "sOO|I", kwlist, &name, &literals, &values, &min_valbits))
        return NULL;

    if (!PyList_Check(literals) || !PyList_Check(values)) {
        PyErr_SetString(PyExc_TypeError, "'literals' and 'values' must be lists");
        return NULL;
    }
    
    elem_count = PyList_Size(literals);
    if (elem_count == 0 || elem_count != PyList_Size(values)) {
        PyErr_SetString(PyExc_ValueError, "'literals' and 'values' must have the same non-zero length");
        return NULL;
    }

    if (name == NULL || name[0] == '\0') {
        PyErr_SetString(PyExc_ValueError, "variable name must not be empty");
        return NULL;
    }

    if (self->ctx == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "FST writer is closed");
        return NULL;
    }

    lit_array = calloc(elem_count, sizeof(char*));
    val_array = calloc(elem_count, sizeof(char*));
    if (!lit_array || !val_array) {
        free(lit_array);
        free(val_array);
        PyErr_NoMemory();
        return NULL;
    }

    for (Py_ssize_t i = 0; i < elem_count; i++) {
        PyObject* lit_obj = PyList_GetItem(literals, i);
        PyObject* val_obj = PyList_GetItem(values  , i);
        if (!PyUnicode_Check(lit_obj) || !PyUnicode_Check(val_obj)) {
            free(lit_array);
            free(val_array);
            PyErr_SetString(PyExc_TypeError, "enumeration literals and values must be strings");
            return NULL;
        }
        lit_array[i] = PyUnicode_AsUTF8(lit_obj);
        val_array[i] = PyUnicode_AsUTF8(val_obj);

        if (!lit_array[i] || !val_array[i]) {
            free(lit_array);
            free(val_array);
            return NULL;
        }
    }

    handle = fstWriterCreateEnumTable(
                 self->ctx,
                 name,
                 (uint32_t)elem_count,
                 min_valbits,
                 lit_array,
                 val_array);

    free(lit_array);
    free(val_array);

    if (handle == 0) {
        PyErr_SetString(PyExc_RuntimeError, "failed to create FST enumeration table");
        return NULL;
    }

    return PyLong_FromUnsignedLong((unsigned long)handle);
}

PyDoc_STRVAR(
    writer_emit_enum_table_doc,
    "Emit a reference to an existing enumeration table in the FST hierarchy.\n"
    "\n"
    "Args:\n"
    "    handle (int): Enumeration table handle returned by\n"
    "        create_enum_table().\n"
    "\n"
    "Raises:\n"
    "    ValueError: If the enumeration table handle is invalid (0).\n"
    "    RuntimeError: If the FST writer has already been closed.\n"
    "\n"
    "Note:\n"
    "    This method writes an FST_MT_ENUMTABLE hierarchy attribute\n"
    "    containing only a reference to an existing enumeration table.\n"
    "    The enumeration table itself must have been created previously\n"
    "    using create_enum_table().\n"
    "\n"
    "Returns:\n"
    "    None.\n"
);
static PyObject*
writer_emit_enum_table(writer_object* self, PyObject* args, PyObject* kwdict)
{
    static const char* kwlist[] = { "handle", NULL };
    unsigned long long handle;

    if (!PyArg_ParseTupleAndKeywords(args, kwdict, "K", kwlist, &handle))
        return NULL;

    if (handle == 0) {
        PyErr_SetString(PyExc_ValueError, "invalid enumeration table handle: 0");
        return NULL;
    }

    if (self->ctx == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "FST writer is closed");
        return NULL;
    }

    fstWriterEmitEnumTableRef(self->ctx, (fstEnumHandle)handle);

    Py_RETURN_NONE;
}

PyDoc_STRVAR(
    writer_emit_dump_active_doc,
    "Record a dump active/inactive event at the current simulation time.\n"
    "\n"
    "Args:\n"
    "    enable (bool):\n"
    "        True to mark waveform dumping as active.\n"
    "        False to mark waveform dumping as inactive.\n"
    "\n"
    "Note:\n"
    "    The event is recorded at the current simulation time previously\n"
    "    specified with set_time().\n"
    "    Multiple dump activity transitions may be emitted during a\n"
    "    simulation.\n"
    "\n"
    "Returns:\n"
    "    None.\n"
);
static PyObject*
writer_emit_dump_active(writer_object* self, PyObject* args, PyObject* kwdict)
{
    static const char* kwlist[] = { "enable", NULL };
    PyObject*          value;
    int                enable;

    if (!PyArg_ParseTupleAndKeywords(args, kwdict, "O", kwlist, &value))
        return NULL;

    enable = PyObject_IsTrue(value);
    if (enable < 0)
        return NULL;

    if (self->ctx == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "FST writer is closed");
        return NULL;
    }

    fstWriterEmitDumpActive(self->ctx, enable);

    Py_RETURN_NONE;
}

PyDoc_STRVAR(
    writer_emit_value_change_doc,
    "Emit a value change.\n"
    "\n"
    "Args:\n"
    "    handle (int): Variable handle.\n"
    "    value: New value. Supported types are:\n"
    "        str\n"
    "        int\n"
    "        sequence[int]\n"
    "    bits (int, optional): Bit width required for integer values.\n"
    "\n"
    "For string values, the value is written directly.\n"
    "For integer values, the value is converted to a binary string.\n"
    "For sequences of integers, each element is treated as a 32-bit or\n"
    "64-bit word depending on its value.\n"
    "\n"
    "Returns:\n"
    "    None.\n"
    "\n"
    "Raises:\n"
    "    RuntimeError:\n"
    "        If the writer has already been closed.\n"
    "    ValueError:\n"
    "        If bits is omitted for integer or vector values,\n"
    "        or if an integer value exceeds 64 bits.\n"
    "    TypeError:\n"
    "        If value is not str, int, or sequence[int].\n"
);
static PyObject *
writer_emit_value_change(writer_object* self, PyObject* args, PyObject* kwdict)
{
    static const char *kwlist[] = { "handle", "value", "bits", NULL };
    unsigned int       handle;
    PyObject*          value;
    unsigned int       bits = 0;

    if (!PyArg_ParseTupleAndKeywords(args, kwdict, "IO|I", kwlist, &handle, &value, &bits))
        return NULL;

    if (self->ctx == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "FST writer is closed");
        return NULL;
    }
    /*
     * str
     */
    if (PyUnicode_Check(value)) {
        const char *val = PyUnicode_AsUTF8(value);
        if (!val)
            return NULL;
        /*
         * Emit for both fixed-length and variable-length variables.
         * Only the appropriate writer routine actually performs the write.
         */
        fstWriterEmitValueChange(self->ctx, (fstHandle)handle, val);
        fstWriterEmitVariableLengthValueChange(self->ctx, (fstHandle)handle, val, (uint32_t)strlen(val));
        Py_RETURN_NONE;
    }
    /*
     * int
     */
    if (PyLong_Check(value)) {
        unsigned long long val = PyLong_AsUnsignedLongLong(value);
        if (PyErr_Occurred())
            return NULL;
        if (bits == 0) {
            PyErr_SetString(PyExc_ValueError, "'bits' is required for integer values");
            return NULL;
        }
        if (bits <= 32) {
            fstWriterEmitValueChange32(self->ctx, (fstHandle)handle, bits, (uint32_t)val);
        } else if (bits <= 64) {
            fstWriterEmitValueChange64(self->ctx, (fstHandle)handle, bits, (uint64_t)val);
        } else {
            PyErr_SetString(PyExc_ValueError, "integer values support at most 64 bits");
            return NULL;
        }
        Py_RETURN_NONE;
    }
    /*
     * sequence[int]
     */
    if (PyList_Check(value) || PyTuple_Check(value)) {
        if (bits == 0) {
            PyErr_SetString(PyExc_ValueError, "'bits' is required for vector values");
            return NULL;
        }
        PyObject*  seq   = PySequence_Fast(value, "value must be a sequence");
        if (!seq)
            return NULL;
        Py_ssize_t size  = PySequence_Fast_GET_SIZE(seq);
        if (size == 0) {
            Py_DECREF(seq);
            PyErr_SetString(PyExc_ValueError, "value sequence is empty");
            return NULL;
        }
        PyObject** items = PySequence_Fast_ITEMS(seq);
        bool       use64 = false;

        for (Py_ssize_t i = 0; i < size; i++) {
            unsigned long long val64 = PyLong_AsUnsignedLongLong(items[i]);
            if (PyErr_Occurred()) {
                Py_DECREF(seq);
                return NULL;
            }
            if (val64 > UINT32_MAX)
                use64 = true;
        }
        if (!use64) {
            uint32_t* vec = PyMem_New(uint32_t, size);
            if (!vec) {
                Py_DECREF(seq);
                return PyErr_NoMemory();
            }
            for (Py_ssize_t i = 0; i < size; i++) {
                unsigned long val32 = PyLong_AsUnsignedLong(items[i]);
                if (PyErr_Occurred()) {
                    PyMem_Free(vec);
                    Py_DECREF(seq);
                    return NULL;
                }
                vec[i] = (uint32_t)val32;
            }
            fstWriterEmitValueChangeVec32(self->ctx, (fstHandle)handle, bits, vec);
            PyMem_Free(vec);
        } else {
            uint64_t* vec = PyMem_New(uint64_t, size);
            if (!vec) {
                Py_DECREF(seq);
                return PyErr_NoMemory();
            }
            for (Py_ssize_t i = 0; i < size; i++) {
                unsigned long long val64 = PyLong_AsUnsignedLongLong(items[i]);
                if (PyErr_Occurred()) {
                    PyMem_Free(vec);
                    Py_DECREF(seq);
                    return NULL;
                }
                vec[i] = (uint64_t)val64;
            }
            fstWriterEmitValueChangeVec64(self->ctx, (fstHandle)handle, bits, vec);
            PyMem_Free(vec);
        }
        Py_DECREF(seq);
        Py_RETURN_NONE;
    }

    PyErr_SetString(PyExc_TypeError, "value must be str, int, or sequence[int]");
    return NULL;
}

PyDoc_STRVAR(
    writer_emit_time_change_doc,
    "Advance the simulation time.\n"
    "\n"
    "Args:\n"
    "    time (int): Simulation time.\n"
    "\n"
    "Returns:\n"
    "    None.\n"
    "\n"
    "Raises:\n"
    "    RuntimeError:\n"
    "        If the FST writer has already been closed.\n"
    "    OverflowError:\n"
    "        If the time value cannot be represented as a 64-bit unsigned integer.\n"
);
static PyObject*
writer_emit_time_change(writer_object* self, PyObject* args, PyObject* kwdict)
{
    static const char* kwlist[] = { "time", NULL };
    unsigned long long time;

    if (!PyArg_ParseTupleAndKeywords(args, kwdict, "K", kwlist, &time))
        return NULL;

    if (self->ctx == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "FST writer is closed");
        return NULL;
    }

    fstWriterEmitTimeChange(self->ctx, (uint64_t)time);

    Py_RETURN_NONE;
}

#define DEFINE_WRITER_RO_BOOL_PROPERTY(name, fst_func, doc)                   \
PyDoc_STRVAR(writer_ ## name ## _doc, doc);                                   \
static PyObject*                                                              \
writer_get_ ## name(writer_object* self, PyObject* Py_UNUSED(args))           \
{                                                                             \
    int property = fst_func(self->ctx);                                       \
    return PyBool_FromLong(property);                                         \
}

DEFINE_WRITER_RO_BOOL_PROPERTY(
    dump_size_limit_reached,
    fstWriterGetDumpSizeLimitReached,
    "Return whether the configured dump size limit has been reached.\n"
    "\n"
    "Returns:\n"
    "    bool: True if the dump size limit has been reached,\n"
    "        False otherwise."
);

DEFINE_WRITER_RO_BOOL_PROPERTY(
    fseek_failed,
    fstWriterGetFseekFailed,
    "Return whether the writer has encountered an fseek() failure.\n"
    "\n"
    "Returns:\n"
    "    bool: True if an fseek() operation has failed,\n"
    "        False otherwise."
);

DEFINE_WRITER_RO_BOOL_PROPERTY(
    flush_context_pending,
    fstWriterGetFlushContextPending,
    "Return whether a flush context is pending.\n"
    "\n"
    "This property returns False during the initial simulation time,\n"
    "even if internal flush conditions have been met.\n"
    "\n"
    "Returns:\n"
    "    bool: True if a flush context is pending,\n"
    "        False otherwise."
);

#define WRITER_PROPERTY(name) { #name, (getter)writer_get_##name, NULL, writer_##name##_doc, NULL}

static PyGetSetDef  writer_getset[] = {
    WRITER_PROPERTY(dump_size_limit_reached),
    WRITER_PROPERTY(fseek_failed           ),
    WRITER_PROPERTY(flush_context_pending  ),
    {NULL}
};

#define WRITER_METHOD(name, flags) { #name, (PyCFunction)writer_##name, flags, writer_##name##_doc }
#define WRITER_METHOD_NOARGS(name) WRITER_METHOD(name, METH_NOARGS)
#define WRITER_METHOD_KVARGS(name) WRITER_METHOD(name, METH_VARARGS | METH_KEYWORDS)

static PyMethodDef  writer_methods[] = {
    WRITER_METHOD_NOARGS(close                             ),
    WRITER_METHOD_NOARGS(flush_context                     ),
    WRITER_METHOD_KVARGS(set_file_type                     ),
    WRITER_METHOD_KVARGS(set_pack_type                     ),
    WRITER_METHOD_KVARGS(set_date                          ),
    WRITER_METHOD_KVARGS(set_version                       ),
    WRITER_METHOD_KVARGS(set_time_scale                    ),
    WRITER_METHOD_KVARGS(set_time_zero                     ),
    WRITER_METHOD_KVARGS(set_dump_size_limit               ),
    WRITER_METHOD_KVARGS(set_repack_on_close               ),
    WRITER_METHOD_KVARGS(set_parallel_mode                 ),
    WRITER_METHOD_KVARGS(set_scope                         ),
    WRITER_METHOD_NOARGS(set_upscope                       ),
    WRITER_METHOD_KVARGS(set_attr_begin                    ),
    WRITER_METHOD_NOARGS(set_attr_end                      ),
    WRITER_METHOD_KVARGS(set_comment                       ),
    WRITER_METHOD_KVARGS(set_env_var                       ),
    WRITER_METHOD_KVARGS(set_value_list                    ),
    WRITER_METHOD_KVARGS(set_source_statement              ),
    WRITER_METHOD_KVARGS(set_source_instantiation_statement),
    WRITER_METHOD_KVARGS(create_var                        ),
    WRITER_METHOD_KVARGS(create_enum_table                 ),
    WRITER_METHOD_KVARGS(emit_dump_active                  ),
    WRITER_METHOD_KVARGS(emit_value_change                 ),
    {NULL}
};

static PyTypeObject writer_type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name       = PACKAGE_NAME_STRING "." MODULE_NAME_STRING "." OBJECT_NAME_STRING,
    .tp_basicsize  = sizeof(writer_object),
    .tp_dealloc    = (destructor)writer_object_dealloc,
    .tp_flags      = Py_TPFLAGS_DEFAULT,
    .tp_doc        = "GTKWave FST Writer Object \n\n"
                     OBJECT_NAME_STRING "(filename,use_compressed_hier=1) \n"
                     "    Create a new " OBJECT_NAME_STRING " instance \n"
                     "    filename (str): FST output file name\n"
                     "    use_compressed_hier (int, optional):\n"
                     "        Enable compressed hierarchy names.\n"
                     "        0: disable\n"
                     "        1: enable (default)\n",
    .tp_methods    = writer_methods,
    .tp_getset     = writer_getset,
    .tp_init       = (initproc)writer_object_init,
    .tp_new        = writer_object_new,
};
    
static struct PyModuleDef writer_module = {
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

    if (PyType_Ready(&writer_type) < 0) {
        return NULL;
    }

    m = PyModule_Create(&writer_module);
    if (m == NULL) {
        return NULL;
    }

    Py_INCREF(&writer_type);
    if (PyModule_AddObject(m, OBJECT_NAME_STRING, (PyObject*)&writer_type) < 0) {
        Py_DECREF(&writer_type);
        Py_DECREF(m);
        return NULL;
    }
    return m;
}
