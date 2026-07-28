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
#define MODULE_NAME         reader
#endif

#ifndef OBJECT_NAME
#define OBJECT_NAME         Reader
#endif

#define MODULE_VERSION      "0.0.7"
#define MODULE_AUTHOR       "Ichiro Kawazome"
#define MODULE_AUTHOR_EMAIL "ichiro_k@ca2-so-net.ne.jp"
#define MODULE_LICENSE      "BSD 2-Clause"
#define MODULE_DESCRIPTION  "GTKWave FST Reader Module"

#define TO_STR(x)           #x
#define NAME_TO_STR(x)      TO_STR(x)
#define PACKAGE_NAME_STRING NAME_TO_STR(PACKAGE_NAME)
#define MODULE_NAME_STRING  NAME_TO_STR(MODULE_NAME)
#define OBJECT_NAME_STRING  NAME_TO_STR(OBJECT_NAME)

#ifndef HIER_MODULE_NAME
#define HIER_MODULE_NAME    hier
#endif

static PyObject* hier_module = NULL;

static int
import_hier_module(void)
{
    if (hier_module == NULL) {
        hier_module = PyImport_ImportModule(PACKAGE_NAME_STRING "." NAME_TO_STR(HIER_MODULE_NAME));
        if (hier_module == NULL)
            return -1;   /* ImportError is already set by PyImport_ImportModule() */
    }
    return 0;
}

static PyObject*
call_hier_from_fst(struct fstHier* hier)
{
    return PyObject_CallMethod(hier_module, "from_fst", "K", (unsigned long long)hier);
}

typedef struct {
    PyObject_HEAD
    fstReaderContext* ctx;
    PyObject*         scope_info_list;
    char*             temp_signal_value_buf;
    Py_ssize_t        temp_signal_value_len;
} reader_object;

static PyObject*
reader_object_new(PyTypeObject* type, PyObject* args, PyObject* kwdict)
{
    reader_object* self;
    self = (reader_object*)type->tp_alloc(type, 0);
    if (self != NULL) {
        self->ctx = NULL;
    }
    return (PyObject*)self;
}

static void
reader_object_clean(reader_object* self)
{
    if (self == NULL)
        return;

    if (self->ctx != NULL) {
        fstReaderClose(self->ctx);
        self->ctx = NULL;
    }

    Py_CLEAR(self->scope_info_list);
    
    if (self->temp_signal_value_buf != NULL) {
        PyMem_Free(self->temp_signal_value_buf);
        self->temp_signal_value_buf = NULL;
    }
    self->temp_signal_value_len = 0;
}
    
static int
reader_object_init(reader_object* self, PyObject* args, PyObject* kwdict)
{
    static char* kwlist[] = { "filename", NULL };
    const  char* filename;

    if (!PyArg_ParseTupleAndKeywords(args, kwdict, "s", kwlist, &filename)) {
        return -1;
    }

    reader_object_clean(self);

    self->ctx = fstReaderOpen(filename);
    if (self->ctx == NULL) {
        PyErr_Format(PyExc_OSError,
                     "cannot open FST file \"%s\"",
                     filename);
        return -1;
    }

    self->scope_info_list = PyList_New(0);

    self->temp_signal_value_len = 0;
    self->temp_signal_value_buf = NULL;
    
    return 0;
}

static void
reader_object_dealloc(reader_object* self)
{
    reader_object_clean(self);
    Py_TYPE(self)->tp_free((PyObject*)self);
}

PyDoc_STRVAR(reader_close_doc,
    "close()\n"
    "--\n"
    "\n"
    "Close the FST reader.\n"
    "\n"
    "Release all resources associated with this reader.\n"
    "After this call, the reader is closed and its scope information\n"
    "is discarded. Calling this method more than once is safe."
);
static PyObject*
reader_close(reader_object* self, PyObject* Py_UNUSED(args))
{
    if (self->ctx != NULL) {
        fstReaderClose(self->ctx);
        self->ctx = NULL;
        Py_CLEAR(self->scope_info_list);
    }
    Py_RETURN_NONE;
}

typedef struct {
    PyObject_HEAD
    reader_object* reader;
} reader_hier_iterator;

static PyObject*
reader_hier_iterator_next(reader_hier_iterator* iter)
{
    struct fstHier* hier;
    hier = fstReaderIterateHier(iter->reader->ctx);
    if (hier == NULL) {
        PyErr_SetNone(PyExc_StopIteration);
        return NULL;
    }
    return call_hier_from_fst(hier);
}

static void
reader_hier_iterator_dealloc(reader_hier_iterator* iter)
{
    Py_XDECREF(iter->reader);
    Py_TYPE(iter)->tp_free((PyObject*)iter);
}

static PyObject*
reader_hier_iterator_iter(PyObject* self)
{
    Py_INCREF(self);
    return self;
}

static PyTypeObject reader_hier_iterator_type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name       = PACKAGE_NAME_STRING "." MODULE_NAME_STRING "." "HierIterator",
    .tp_basicsize  = sizeof(reader_hier_iterator),
    .tp_dealloc    = (destructor)reader_hier_iterator_dealloc,
    .tp_flags      = Py_TPFLAGS_DEFAULT,
    .tp_iter       = reader_hier_iterator_iter,
    .tp_iternext   = (iternextfunc)reader_hier_iterator_next,
    .tp_doc        = "FST hierarchy iterator",
};

PyDoc_STRVAR(reader_hiers_doc,
    "hiers()\n"
    "--\n"
    "\n"
    "Return an iterator over the FST hierarchy.\n"
    "\n"
    "The hierarchy iteration is restarted from the beginning each time\n"
    "this method is called.\n"
    "\n"
    "Yields:\n"
    "    Scope:\n"
    "        Scope entry.\n"
    "    UpScope:\n"
    "        End of the current scope.\n"
    "    Var:\n"
    "        Variable declaration.\n"
    "    Attr:\n"
    "        Attribute entry.\n"
    "    AttrEnd:\n"
    "        End of an attribute block.\n"
    "    None:\n"
    "        An unsupported hierarchy entry."
);    
static PyObject*
reader_hiers(reader_object* self, PyObject* Py_UNUSED(args))
{
    reader_hier_iterator* iter = PyObject_New(reader_hier_iterator, &reader_hier_iterator_type);
    if (iter == NULL)
        return NULL;

    iter->reader = Py_NewRef(self);

    fstReaderIterateHierRewind(self->ctx);

    return (PyObject*)iter;
}

PyDoc_STRVAR(reader_reset_scope_doc,
    "reset_scope()\n"
    "--\n"
    "\n"
    "Clear the current FST hierarchy scope stack.\n"
    "\n"
    "This method removes all scopes added by push_scope() and\n"
    "discards their associated user information."
);
static PyObject*
reader_reset_scope(reader_object* self, PyObject* Py_UNUSED(args))
{
    PyObject* new_list;

    fstReaderResetScope(self->ctx);

    new_list = PyList_New(0);
    if (new_list == NULL)
        return NULL;
    Py_SETREF(self->scope_info_list, new_list);

    Py_RETURN_NONE;
}

PyDoc_STRVAR(reader_push_scope_doc,
    "push_scope(name, info=None)\n"
    "--\n"
    "\n"
    "Add a scope to the current FST hierarchy stack.\n"
    "\n"
    "The optional info object is stored with the scope and can be\n"
    "retrieved by get_current_scope_user_info().\n"
    "\n"
    "Args:\n"
    "    name (str): Scope name.\n"
    "    info (object, optional): User-defined scope information.\n"
    "\n"
    "Returns:\n"
    "    str: Current flattened scope path."
);
static PyObject *
reader_push_scope(reader_object* self, PyObject* args, PyObject* kwds)
{
    static char* kwlist[]  = { "name", "info", NULL };
    const  char* name;
    PyObject*    info      = Py_None;
    void*        user_info = NULL;
    const char*  result;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "s|O", kwlist, &name, &info))
        return NULL;

    if (PyList_Append(self->scope_info_list, info) < 0) {
        return NULL;
    }

    user_info = (info != Py_None) ? (void *)info : NULL;

    result = fstReaderPushScope(self->ctx, name, user_info);

    if (result == NULL)
        Py_RETURN_NONE;

    return PyUnicode_FromString(result);
}

PyDoc_STRVAR(reader_pop_scope_doc,
    "pop_scope()\n"
    "--\n"
    "\n"
    "Remove the current scope from the FST hierarchy stack.\n"
    "\n"
    "This method reverses the operation of push_scope().\n"
    "The user information associated with the scope is discarded.\n"
    "\n"
    "Returns:\n"
    "    str: Current flattened scope path."
);
static PyObject*
reader_pop_scope(reader_object* self, PyObject* Py_UNUSED(args))
{
    const char*  result;
    Py_ssize_t   info_list_size;

    result = fstReaderPopScope(self->ctx);

    if (result == NULL)
        Py_RETURN_NONE;

    info_list_size = PyList_GET_SIZE(self->scope_info_list);

    if (info_list_size > 0) {
        PySequence_DelItem(self->scope_info_list, info_list_size-1);
    }
        
    return PyUnicode_FromString(result);
}

PyDoc_STRVAR(reader_get_current_flat_scope_doc,
    "get_current_flat_scope()\n"
    "--\n"
    "\n"
    "Return the current FST hierarchy scope as a flat name.\n"
    "\n"
    "The scope components are concatenated into a single path string.\n"
    "\n"
    "Returns:\n"
    "    str | None: Flattened hierarchy name, or None if unavailable."
);
static PyObject*
reader_get_current_flat_scope(reader_object* self, PyObject* Py_UNUSED(args))
{
    const char* result = fstReaderGetCurrentFlatScope(self->ctx);
    if (result == NULL)
        Py_RETURN_NONE;
    return PyUnicode_FromString(result);
}

PyDoc_STRVAR(reader_get_current_scope_user_info_doc,
    "get_current_scope_user_info()\n"
    "--\n"
    "\n"
    "Return the user information stored for the current scope.\n"
    "\n"
    "The information object is the same object passed as the info\n"
    "argument to push_scope().\n"
    "\n"
    "Returns:\n"
    "    object | None: Scope user information, or None if not set."
);
static PyObject*
reader_get_current_scope_user_info(reader_object* self, PyObject* Py_UNUSED(args))
{
    void*      user_info;
    Py_ssize_t info_list_size;
    PyObject*  info;

    user_info = fstReaderGetCurrentScopeUserInfo(self->ctx);

    if (user_info == NULL)
        Py_RETURN_NONE;
    
    info_list_size = PyList_GET_SIZE(self->scope_info_list);
    if (info_list_size == 0) {
        PyErr_SetString(PyExc_RuntimeError, "scope info stack is empty.");
        return NULL;
    }

    info = PyList_GET_ITEM(self->scope_info_list, info_list_size-1);
    if ((void*)info != user_info) {
        PyErr_SetString(PyExc_RuntimeError, "scope info stack mismatch.");
        return NULL;
    }
    
    return Py_NewRef(info);
}

PyDoc_STRVAR(reader_get_scope_len_doc,
    "get_scope_len()\n"
    "--\n"
    "\n"
    "Return the length of the current FST hierarchy scope.\n"
    "\n"
    "Returns:\n"
    "    int: Number of characters in the current scope name."
);
static PyObject*
reader_get_scope_len(reader_object* self, PyObject* Py_UNUSED(args))
{
    int result = fstReaderGetCurrentScopeLen(self->ctx);
    return PyLong_FromLong(result);
}

typedef struct {
    PyObject_HEAD
    reader_object* reader;
    PyObject*      events;
    Py_ssize_t     index;
    int            loaded;
} reader_block_iterator;

static void
reader_value_change_callback(void*                user_data,
                             uint64_t             time     ,
                             fstHandle            facidx   ,
                             const unsigned char* value    )
{
    reader_block_iterator* iter = (reader_block_iterator*)user_data;
    PyObject* item  = Py_BuildValue("(KKs)",
                                    (unsigned long long)time,
                                    (unsigned long long)facidx,
                                    value);
    if (item == NULL)
        return;

    if (PyList_Append(iter->events, item) < 0) {
        Py_DECREF(item);
        return;
    }
    Py_DECREF(item);
}

static void
reader_value_change_callback_varlen(void*                user_data,
                                    uint64_t             time     ,
                                    fstHandle            facidx   ,
                                    const unsigned char* value    ,
                                    uint32_t             len      )
{
    reader_block_iterator* iter = (reader_block_iterator*)user_data;
    PyObject* py_value = PyUnicode_FromStringAndSize((const char*)value, len);

    if (py_value == NULL) 
        return;

    PyObject* item = Py_BuildValue("(KKO)",
                                   (unsigned long long)time,
                                   (unsigned long long)facidx,
                                   py_value);
    Py_DECREF(py_value);
    
    if (item == NULL) 
        return;

    if (PyList_Append(iter->events, item) < 0) {
        Py_DECREF(item);
        return;
    }
    Py_DECREF(item);
}

static PyObject*
reader_block_iterator_iter(PyObject* self)
{
    Py_INCREF(self);
    return self;
}

static PyObject*
reader_block_iterator_next(reader_block_iterator* iter)
{
    if (!iter->loaded) {
        fstReaderIterBlocks2(iter->reader->ctx,
                             reader_value_change_callback,
                             reader_value_change_callback_varlen,
                             iter,
                             NULL
        );
        iter->loaded = 1;
    }
    if (iter->index >= PyList_Size(iter->events)) {
        PyErr_SetNone(PyExc_StopIteration);
        return NULL;
    }
    PyObject* item = PyList_GET_ITEM(iter->events, iter->index);
    iter->index++;
    Py_INCREF(item);
    return item;
}

static void
reader_block_iterator_dealloc(reader_block_iterator* iter)
{
    Py_XDECREF(iter->reader);
    Py_XDECREF(iter->events);
    Py_TYPE(iter)->tp_free((PyObject*)iter);
}

static PyTypeObject reader_block_iterator_type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name       = PACKAGE_NAME_STRING "." MODULE_NAME_STRING ".BlockIterator",
    .tp_basicsize  = sizeof(reader_block_iterator),
    .tp_dealloc    = (destructor)reader_block_iterator_dealloc,
    .tp_flags      = Py_TPFLAGS_DEFAULT,
    .tp_iter       = reader_block_iterator_iter,
    .tp_iternext   = (iternextfunc)reader_block_iterator_next,
    .tp_doc        = "FST block iterator",
};

PyDoc_STRVAR(reader_blocks_doc,
    "blocks()\n"
    "--\n"
    "\n"
    "Return an iterator over value changes.\n"
    "\n"
    "Each iteration yields a tuple:\n"
    "    (time, handle, value)\n"
    "\n"
    "where:\n"
    "    time   (int): Simulation time.\n"
    "    handle (int): Facility handle.\n"
    "    value  (str): Signal value."
);
static PyObject*
reader_blocks(reader_object* self, PyObject* Py_UNUSED(args))
{
    reader_block_iterator* iter = PyObject_New(reader_block_iterator, &reader_block_iterator_type);

    if (iter == NULL)
        return NULL;

    iter->reader = Py_NewRef(self);

    iter->events = PyList_New(0);
    if (iter->events == NULL) {
        Py_DECREF(iter);
        return NULL;
    }
    iter->index  = 0;
    iter->loaded = 0;

    return (PyObject*)iter;
}

PyDoc_STRVAR(reader_clear_facility_process_mask_doc,
    "clear_facility_process_mask(handle)\n"
    "--\n"
    "\n"
    "Disable value change processing for a facility.\n"
    "\n"
    "Args:\n"
    "    handle (int): Facility handle to disable."
);
static PyObject*
reader_clear_facility_process_mask(reader_object* self, PyObject* args, PyObject* kwds)
{
    static char*       kwlist[] = { "handle", NULL };
    unsigned long long handle;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "K",kwlist, &handle))
        return NULL;

    fstReaderClrFacProcessMask(self->ctx, (fstHandle)handle);

    Py_RETURN_NONE;
}

PyDoc_STRVAR(reader_clear_facility_process_mask_all_doc,
    "clear_facility_process_mask_all()\n"
    "--\n"
    "\n"
    "Disable value change processing for all facilities.\n"
    "\n"
    "After calling this method, value changes from all facilities are\n"
    "ignored by the reader."
);
static PyObject*
reader_clear_facility_process_mask_all(reader_object* self, PyObject* Py_UNUSED(args))
{
    fstReaderClrFacProcessMaskAll(self->ctx);
    Py_RETURN_NONE;
}

PyDoc_STRVAR(reader_set_facility_process_mask_doc,
    "set_facility_process_mask(handle)\n"
    "--\n"
    "\n"
    "Enable value change processing for a facility.\n"
    "\n"
    "Args:\n"
    "    handle (int): Facility handle to enable."
);
static PyObject*
reader_set_facility_process_mask(reader_object* self, PyObject* args, PyObject* kwds)
{
    static char*       kwlist[] = { "handle", NULL };
    unsigned long long handle;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "K",kwlist, &handle))
        return NULL;

    fstReaderSetFacProcessMask(self->ctx, (fstHandle)handle);

    Py_RETURN_NONE;
}

PyDoc_STRVAR(reader_set_facility_process_mask_all_doc,
    "set_facility_process_mask_all()\n"
    "--\n"
    "\n"
    "Enable value change processing for all facilities.\n"
    "\n"
    "After calling this method, value changes from all facilities are\n"
    "processed by the reader."
);
static PyObject*
reader_set_facility_process_mask_all(reader_object* self, PyObject* Py_UNUSED(args))
{
    fstReaderSetFacProcessMaskAll(self->ctx);
    Py_RETURN_NONE;
}

PyDoc_STRVAR(reader_get_facility_process_mask_doc,
    "get_facility_process_mask(handle)\n"
    "--\n"
    "\n"
    "Check whether a facility is enabled for value change processing.\n"
    "\n"
    "Args:\n"
    "    handle (int): Facility handle.\n"
    "\n"
    "Returns:\n"
    "    bool: True if the facility is enabled, otherwise False."
);
static PyObject*
reader_get_facility_process_mask(reader_object* self, PyObject* args, PyObject* kwds)
{
    static char*       kwlist[] = { "handle", NULL };
    unsigned long long handle;
    int                mask;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "K",kwlist, &handle))
        return NULL;

    mask = fstReaderGetFacProcessMask(self->ctx, (fstHandle)handle);

    return PyBool_FromLong(mask);
}

PyDoc_STRVAR(reader_get_dump_activity_change_time_doc,
    "get_dump_activity_change_time(index)\n"
    "--\n"
    "\n"
    "Return the simulation time associated with a dump activity change.\n"
    "\n"
    "Args:\n"
    "    index (int): Zero-based index of the activity change entry.\n"
    "\n"
    "Returns:\n"
    "    int: Simulation timestamp."
);
static PyObject*
reader_get_dump_activity_change_time(reader_object* self, PyObject* args, PyObject* kwds)
{
    static char*       kwlist[] = { "index", NULL };
    unsigned int       index;
    int                time;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "I", kwlist, &index))
        return NULL;

    time = fstReaderGetDumpActivityChangeTime(self->ctx, (uint32_t)index);

    return PyLong_FromUnsignedLongLong(time);
}

PyDoc_STRVAR(reader_get_dump_activity_change_value_doc,
    "get_dump_activity_change_value(index)\n"
    "--\n"
    "\n"
    "Return the value associated with a dump activity change.\n"
    "\n"
    "Args:\n"
    "    index (int): Zero-based index of the activity change entry.\n"
    "\n"
    "Returns:\n"
    "    int: Unsigned 8-bit activity change value."
);
static PyObject*
reader_get_dump_activity_change_value(reader_object* self, PyObject* args, PyObject* kwds)
{
    static char*       kwlist[] = { "index", NULL };
    unsigned int       index;
    unsigned char      value;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "I", kwlist, &index))
        return NULL;

    value = fstReaderGetDumpActivityChangeValue(self->ctx, (uint32_t)index);

    return PyLong_FromUnsignedLong((unsigned long)value);
}

PyDoc_STRVAR(reader_set_limit_time_range_doc,
    "set_limit_time_range(start_time, end_time)\n"
    "--\n"
    "\n"
    "Set the time range limit for FST reading.\n"
    "\n"
    "Args:\n"
    "    start_time (int): First simulation timestamp to include.\n"
    "    end_time   (int): Last simulation timestamp to include.\n"
    "\n"
    "Use set_unlimited_time_range() to remove the time range limit."
);
static PyObject*
reader_set_limit_time_range(reader_object* self, PyObject* args, PyObject* kwds)
{
    static char*       kwlist[] = { "start_time", "end_time", NULL };
    unsigned long long start_time;
    unsigned long long end_time;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "KK", kwlist, &start_time, &end_time))
        return NULL;

    fstReaderSetLimitTimeRange(self->ctx, (uint64_t)start_time, (uint64_t)end_time);

    Py_RETURN_NONE;
}

PyDoc_STRVAR(reader_set_unlimited_time_range_doc,
    "set_unlimited_time_range()\n"
    "--\n"
    "\n"
    "Clear the time range limit set by set_limit_time_range().\n"
    "\n"
    "After calling this method, the entire simulation time range is processed."
);
static PyObject*
reader_set_unlimited_time_range(reader_object* self, PyObject* Py_UNUSED(args))
{
    fstReaderSetUnlimitedTimeRange(self->ctx);
    Py_RETURN_NONE;
}

PyDoc_STRVAR(reader_set_vcd_extensions_doc,
    "set_vcd_extensions(enable)\n"
    "--\n"
    "\n"
    "Enable or disable VCD extensions.\n"
    "\n"
    "Args:\n"
    "    enable (bool): True to enable VCD extensions, False to disable them."
);
static PyObject*
reader_set_vcd_extensions(reader_object* self, PyObject* args, PyObject* kwds)
{
    static char*       kwlist[] = { "enable", NULL };
    int                enable;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "p", kwlist, &enable))
        return NULL;

    fstReaderSetVcdExtensions(self->ctx, enable);

    Py_RETURN_NONE;
}

PyDoc_STRVAR(reader_process_hierarchy_doc,
    "process_hierarchy(filename=None)\n"
    "--\n"
    "\n"
    "Process the FST hierarchy.\n"
    "\n"
    "If *filename* is specified, the hierarchy is written to the given\n"
    "file while being processed. If omitted or None, the hierarchy is\n"
    "processed without generating an output file.\n"
    "\n"
    "Args:\n"
    "    filename (str | None, optional): Output file name.\n"
    "\n"
    "Raises:\n"
    "    OSError: If the output file cannot be opened.\n"
    "    RuntimeError: If hierarchy processing fails."
);
static PyObject*
reader_process_hierarchy(reader_object* self, PyObject* args, PyObject* kwds)
{
    static char* kwlist[] = { "filename", NULL };
    const  char* filename = NULL;
    FILE*        fv       = NULL;
    int          rc;
    
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|z", kwlist, &filename))
        return NULL;

    if (filename != NULL) {
        fv = fopen(filename, "w");
        if (fv == NULL) {
            return PyErr_SetFromErrnoWithFilename(PyExc_OSError, filename);
        }
    }

    rc = fstReaderProcessHier(self->ctx, fv);

    if (fv != NULL)
        fclose(fv);

    if (!rc) {
        PyErr_SetString(PyExc_RuntimeError, "fstReaderProcessHier() failed");
        return NULL;
    }
    
    Py_RETURN_NONE;
}

PyDoc_STRVAR(
    reader_get_value_from_handle_at_time_doc,
    "Return the signal value at a specified simulation time.\n"
    "\n"
    "Args:\n"
    "    time (int): Simulation timestamp.\n"
    "    handle (int): Facility handle of the signal.\n"
    "\n"
    "Returns:\n"
    "    str: Signal value at the specified time, or None if unavailable."
);
static PyObject*
reader_get_value_from_handle_at_time(reader_object* self, PyObject* args, PyObject* kwds)
{
    static char*       kwlist[] = { "time", "handle", NULL };
    unsigned long long time;
    unsigned long long handle;
    Py_ssize_t         required_len;
    char*              value;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "KK", kwlist, &time, &handle)) 
        return NULL;

    required_len = (Py_ssize_t)fstReaderGetLongestSignalValueLen(self->ctx);
    if (required_len <= 0) {
        PyErr_SetString(PyExc_RuntimeError , "No signal value length information is available.");
        return NULL;
    }
    if (required_len > PY_SSIZE_T_MAX - 1) {
        PyErr_SetString(PyExc_OverflowError, "No signal value length is too large.");
        return NULL;
    }
    if (self->temp_signal_value_buf == NULL) {
        char* new_buf = PyMem_Malloc(required_len+1);
        if (new_buf == NULL) {
            return PyErr_NoMemory();
        }
        self->temp_signal_value_buf = new_buf;
        self->temp_signal_value_len = required_len;
    }
    if (required_len > self->temp_signal_value_len) {
        char* new_buf = PyMem_Realloc(self->temp_signal_value_buf, required_len+1);
        if (new_buf == NULL) {
            return PyErr_NoMemory();
        }
        self->temp_signal_value_buf = new_buf;
        self->temp_signal_value_len = required_len;
    }

    value = fstReaderGetValueFromHandleAtTime(
                self->ctx,
                (uint64_t)time,
                (fstHandle)handle,
                self->temp_signal_value_buf);

    if (value == NULL)
        Py_RETURN_NONE;

    return PyUnicode_FromString(value);
}

PyDoc_STRVAR(
    reader_set_native_doubles_on_callback_doc,
    "Enable or disable native double values in value change callbacks.\n"
    "\n"
    "Args:\n"
    "    enable (bool): If True, callbacks receive native double values.\n"
    "                    If False, callbacks receive the default representation."
);
static PyObject*
reader_set_native_doubles_on_callback(reader_object* self, PyObject* args, PyObject* kwds)
{
    static char* kwlist[] = { "enable", NULL };
    int          enable;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "p", kwlist, &enable)) 
        return NULL;

    fstReaderIterBlocksSetNativeDoublesOnCallback(self->ctx, enable);

    Py_RETURN_NONE;
}

#define DEFINE_READER_PROPERTY_UINT64_GETTER(name, fst_func, doc)   \
static PyObject*                                                    \
reader_get_ ## name(reader_object* self, PyObject* Py_UNUSED(args)) \
{                                                                   \
    uint64_t property = (uint64_t)fst_func(self->ctx);              \
    return PyLong_FromUnsignedLongLong(property);                   \
}                                                                   \
PyDoc_STRVAR(reader_get_ ## name ## _doc, doc);

#define DEFINE_READER_PROPERTY_SINT64_GETTER(name, fst_func, doc)   \
static PyObject*                                                    \
reader_get_ ## name(reader_object* self, PyObject* Py_UNUSED(args)) \
{                                                                   \
    int64_t property = (int64_t)fst_func(self->ctx);                \
    return PyLong_FromLongLong(property);                           \
}                                                                   \
PyDoc_STRVAR(reader_get_ ## name ## _doc, doc);

#define DEFINE_READER_PROPERTY_STRING_GETTER(name, fst_func, doc)   \
static PyObject*                                                    \
reader_get_ ## name(reader_object* self, PyObject* Py_UNUSED(args)) \
{                                                                   \
    const char* property = fst_func(self->ctx);                     \
    if (property == NULL)                                           \
        Py_RETURN_NONE;                                             \
    return PyUnicode_FromString(property);                          \
}                                                                   \
PyDoc_STRVAR(reader_get_ ## name ## _doc, doc);


DEFINE_READER_PROPERTY_UINT64_GETTER( 
    alias_count,
    fstReaderGetAliasCount,
    "Number of aliases in the FST file.\n"
    "\n"
    "Returns:\n"
    "    int: Number of alias entries."
);
DEFINE_READER_PROPERTY_SINT64_GETTER(
    double_endian_match_state,
    fstReaderGetDoubleEndianMatchState,
    "Return the double endian match state of the FST reader.\n"
    "\n"
    "Returns:\n"
    "    int: Double endian match state."
);
DEFINE_READER_PROPERTY_UINT64_GETTER(
    end_time,
    fstReaderGetEndTime,
    "Return the end time of the FST file.\n"
    "\n"
    "Returns:\n"
    "    int: Simulation time at the end of the FST data."
);
DEFINE_READER_PROPERTY_SINT64_GETTER(
    file_type,
    fstReaderGetFileType,
    "Return the file type of the FST file.\n"
    "\n"
    "Returns:\n"
    "    int: FST file type identifier."
);
DEFINE_READER_PROPERTY_SINT64_GETTER(
    fseek_failed,
    fstReaderGetFseekFailed,
    "Return the fseek failure status of the FST reader.\n"
    "\n"
    "Returns:\n"
    "    int: Non-zero if an fseek operation failed, otherwise zero."
);
DEFINE_READER_PROPERTY_SINT64_GETTER(
    max_handle,
    fstReaderGetMaxHandle,
    "Return the maximum facility handle used by the FST reader.\n"
    "\n"
    "Returns:\n"
    "    int: Maximum facility handle value."
);
DEFINE_READER_PROPERTY_UINT64_GETTER(
    memory_used_by_writer,
    fstReaderGetMemoryUsedByWriter,
    "Return the amount of memory used by the FST writer.\n"
    "\n"
    "Returns:\n"
    "    int: Memory usage in bytes."
);
DEFINE_READER_PROPERTY_UINT64_GETTER(
    dump_activity_changes,
    fstReaderGetNumberDumpActivityChanges,
    "Return the number of dump activity changes available in the FST reader.\n"
    "\n"
    "Returns:\n"
    "    int: Number of dump activity change entries."
);
DEFINE_READER_PROPERTY_UINT64_GETTER(
    scope_count,
    fstReaderGetScopeCount,
    "Return the number of scopes in the FST hierarchy.\n"
    "\n"
    "Returns:\n"
    "    int: Number of scope entries."
);
DEFINE_READER_PROPERTY_UINT64_GETTER(
    start_time,
    fstReaderGetStartTime,
    "Return the start time of the FST file.\n"
    "\n"
    "Returns:\n"
    "    int: Simulation timestamp at the beginning of the FST data."
);
DEFINE_READER_PROPERTY_SINT64_GETTER(
    time_scale,
    fstReaderGetTimescale,
    "Return the time scale of the FST file.\n"
    "\n"
    "Returns:\n"
    "    int: Time scale exponent used for simulation timestamps."
);
DEFINE_READER_PROPERTY_SINT64_GETTER(
    time_zero,
    fstReaderGetTimezero,
    "Return the time zero value of the FST file.\n"
    "\n"
    "Returns:\n"
    "    int: Time zero offset for simulation timestamps."
);
DEFINE_READER_PROPERTY_UINT64_GETTER(
    value_change_section_count,
    fstReaderGetValueChangeSectionCount,
    "Return the number of value change sections in the FST file.\n"
    "\n"
    "Returns:\n"
    "    int: Number of value change sections."
);
DEFINE_READER_PROPERTY_UINT64_GETTER(
    var_count,
    fstReaderGetVarCount,
    "Return the number of variables in the FST hierarchy.\n"
    "\n"
    "Returns:\n"
    "    int: Number of variable definitions."
);
DEFINE_READER_PROPERTY_UINT64_GETTER( 
    longest_signal_value_len,
    fstReaderGetLongestSignalValueLen,
    "Return the maximum length of signal values stored in the FST file.\n"
    "\n"
    "This value can be used to determine the buffer size required for\n"
    "reading signal values.\n"
    "\n"
    "Returns:\n"
    "    int: Maximum signal value length."
);
DEFINE_READER_PROPERTY_STRING_GETTER(
    version,
    fstReaderGetVersionString,
    "Return the FST version string.\n"
    "\n"
    "Returns:\n"
    "    str: Version information of the FST file."
);
DEFINE_READER_PROPERTY_STRING_GETTER(
    date,
    fstReaderGetDateString,
    "Return the FST file date string.\n"
    "\n"
    "Returns:\n"
    "    str: Date information of the FST file."
);

#define READER_PROPERTY(name) { #name, (getter)reader_get_##name , NULL, reader_get_##name##_doc, NULL}

static PyGetSetDef  reader_getset[] = {
    READER_PROPERTY(alias_count               ),
    READER_PROPERTY(double_endian_match_state ),
    READER_PROPERTY(end_time                  ),
    READER_PROPERTY(file_type                 ),
    READER_PROPERTY(fseek_failed              ),
    READER_PROPERTY(max_handle                ),
    READER_PROPERTY(memory_used_by_writer     ),
    READER_PROPERTY(dump_activity_changes     ),
    READER_PROPERTY(scope_count               ),
    READER_PROPERTY(start_time                ),
    READER_PROPERTY(time_scale                ),
    READER_PROPERTY(time_zero                 ),
    READER_PROPERTY(value_change_section_count),
    READER_PROPERTY(var_count                 ),
    READER_PROPERTY(longest_signal_value_len  ),
    READER_PROPERTY(version                   ),
    READER_PROPERTY(date                      ),
    {NULL}
};

#define READER_METHOD(name, flags) { #name, (PyCFunction)reader_##name, flags, reader_##name##_doc }
#define READER_METHOD_NOARGS(name) READER_METHOD(name, METH_NOARGS)
#define READER_METHOD_KVARGS(name) READER_METHOD(name, METH_VARARGS | METH_KEYWORDS)

static PyMethodDef  reader_methods[] = {
    READER_METHOD_NOARGS(reset_scope                    ),
    READER_METHOD_KVARGS(push_scope                     ),
    READER_METHOD_NOARGS(pop_scope                      ),
    READER_METHOD_NOARGS(get_current_flat_scope         ),
    READER_METHOD_NOARGS(get_current_scope_user_info    ),
    READER_METHOD_NOARGS(get_scope_len                  ),
    READER_METHOD_KVARGS(clear_facility_process_mask    ),
    READER_METHOD_NOARGS(clear_facility_process_mask_all),
    READER_METHOD_KVARGS(set_facility_process_mask      ),
    READER_METHOD_NOARGS(set_facility_process_mask_all  ),
    READER_METHOD_KVARGS(get_facility_process_mask      ),
    READER_METHOD_KVARGS(get_dump_activity_change_time  ),
    READER_METHOD_KVARGS(get_dump_activity_change_value ),
    READER_METHOD_KVARGS(set_limit_time_range           ),
    READER_METHOD_NOARGS(set_unlimited_time_range       ),
    READER_METHOD_KVARGS(set_vcd_extensions             ),
    READER_METHOD_KVARGS(get_value_from_handle_at_time  ),
    READER_METHOD_KVARGS(set_native_doubles_on_callback ),
    READER_METHOD_KVARGS(process_hierarchy              ),
    READER_METHOD_NOARGS(hiers                          ),
    READER_METHOD_NOARGS(blocks                         ),
    READER_METHOD_NOARGS(close                          ),
    {NULL}
};

static PyTypeObject reader_type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name       = PACKAGE_NAME_STRING "." MODULE_NAME_STRING "." OBJECT_NAME_STRING,
    .tp_basicsize  = sizeof(reader_object),
    .tp_dealloc    = (destructor)reader_object_dealloc,
    .tp_flags      = Py_TPFLAGS_DEFAULT,
    .tp_doc        = "GTKWave FST Reader Object \n\n"
                     OBJECT_NAME_STRING "(filename) \n"
                     "    Create a new " OBJECT_NAME_STRING " instance \n"
                     "    filename (str): FST input file name\n",
    .tp_methods    = reader_methods,
    .tp_getset     = reader_getset,
    .tp_init       = (initproc)reader_object_init,
    .tp_new        = reader_object_new,
};

static struct PyModuleDef reader_module = {
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

    if (PyType_Ready(&reader_type) < 0) {
        return NULL;
    }

    if (PyType_Ready(&reader_hier_iterator_type) < 0) {
        return NULL;
    }

    if (PyType_Ready(&reader_block_iterator_type) < 0) {
        return NULL;
    }

    m = PyModule_Create(&reader_module);
    if (m == NULL) {
        return NULL;
    }

    Py_INCREF(&reader_type);
    if (PyModule_AddObject(m, OBJECT_NAME_STRING, (PyObject*)&reader_type) < 0) {
        Py_DECREF(&reader_type);
        Py_DECREF(m);
        return NULL;
    }

    if (import_hier_module() < 0) {
        Py_DECREF(&reader_type);
        Py_DECREF(m);
        return NULL;
    }

    return m;
}
