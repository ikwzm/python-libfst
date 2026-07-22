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

#define MODULE_VERSION      "0.0.3"
#define MODULE_AUTHOR       "Ichiro Kawazome"
#define MODULE_AUTHOR_EMAIL "ichiro_k@ca2-so-net.ne.jp"
#define MODULE_LICENSE      "BSD 2-Clause"
#define MODULE_DESCRIPTION  "GTKWave FST Reader Module"

#define TO_STR(x)           #x
#define NAME_TO_STR(x)      TO_STR(x)
#define PACKAGE_NAME_STRING NAME_TO_STR(PACKAGE_NAME)
#define MODULE_NAME_STRING  NAME_TO_STR(MODULE_NAME)
#define OBJECT_NAME_STRING  NAME_TO_STR(OBJECT_NAME)

static PyObject* hier_module = NULL;

typedef struct {
    PyObject_HEAD
    fstReaderContext* ctx;
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

static int
reader_object_init(reader_object* self, PyObject* args, PyObject* kwdict)
{
    static char* kwlist[] = { "filename", NULL };
    const  char* filename;

    if (!PyArg_ParseTupleAndKeywords(args, kwdict, "s", kwlist, &filename)) {
        return -1;
    }

    if (self->ctx != NULL) {
        fstReaderClose(self->ctx);
        self->ctx = NULL;
    }

    self->ctx = fstReaderOpen(filename);
    if (self->ctx == NULL) {
        PyErr_Format(PyExc_OSError,
                     "cannot open FST file \"%s\"",
                     filename);
        return -1;
    }

    return 0;
}

static void
reader_object_dealloc(reader_object* self)
{
    if (self->ctx != NULL) {
        fstReaderClose(self->ctx);
        self->ctx = NULL;
    }
    Py_TYPE(self)->tp_free((PyObject*)self);
}

static PyObject*
reader_close(reader_object* self, PyObject* Py_UNUSED(args))
{
    if (self->ctx != NULL) {
        fstReaderClose(self->ctx);
        self->ctx = NULL;
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
    return PyObject_CallMethod(hier_module, "from_fst", "K", (unsigned long long)hier);
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
    
static PyObject*
reader_hiers(reader_object *self, PyObject *Py_UNUSED(args))
{
    reader_hier_iterator* iter = PyObject_New(reader_hier_iterator, &reader_hier_iterator_type);
    if (iter == NULL)
        return NULL;

    iter->reader = Py_NewRef(self);

    fstReaderIterateHierRewind(self->ctx);

    return (PyObject*)iter;
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
        fstReaderIterBlocks(iter->reader->ctx,
                            reader_value_change_callback,
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

static PyObject*
reader_blocks(reader_object *self, PyObject *Py_UNUSED(args))
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

static PyObject*
reader_clear_facility_process_mask(reader_object *self, PyObject *args, PyObject *kwds)
{
    static char*       kwlist[] = { "handle", NULL };
    unsigned long long handle;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "K",kwlist, &handle))
        return NULL;

    fstReaderClrFacProcessMask(self->ctx, (fstHandle)handle);

    Py_RETURN_NONE;
}

static PyObject*
reader_clear_facility_process_mask_all(reader_object *self, PyObject* Py_UNUSED(args))
{
    fstReaderClrFacProcessMaskAll(self->ctx);
    Py_RETURN_NONE;
}

static PyObject*
reader_set_facility_process_mask(reader_object *self, PyObject *args, PyObject *kwds)
{
    static char*       kwlist[] = { "handle", NULL };
    unsigned long long handle;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "K",kwlist, &handle))
        return NULL;

    fstReaderSetFacProcessMask(self->ctx, (fstHandle)handle);

    Py_RETURN_NONE;
}

static PyObject*
reader_set_facility_process_mask_all(reader_object *self, PyObject* Py_UNUSED(args))
{
    fstReaderSetFacProcessMaskAll(self->ctx);
    Py_RETURN_NONE;
}

static PyObject*
reader_get_facility_process_mask(reader_object *self, PyObject *args, PyObject *kwds)
{
    static char*       kwlist[] = { "handle", NULL };
    unsigned long long handle;
    int                mask;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "K",kwlist, &handle))
        return NULL;

    mask = fstReaderGetFacProcessMask(self->ctx, (fstHandle)handle);

    return PyBool_FromLong(mask);
}

#define DEFINE_READER_PROPERTY_UINT64_GETTER(name, fst_func)        \
static PyObject*                                                    \
reader_get_ ## name(reader_object* self, PyObject* Py_UNUSED(args)) \
{                                                                   \
    uint64_t property = (uint64_t)fst_func(self->ctx);              \
    return PyLong_FromUnsignedLongLong(property);                   \
}
#define DEFINE_READER_PROPERTY_SINT64_GETTER(name, fst_func)        \
static PyObject*                                                    \
reader_get_ ## name(reader_object* self, PyObject* Py_UNUSED(args)) \
{                                                                   \
    int64_t property = (int64_t)fst_func(self->ctx);                \
    return PyLong_FromLongLong(property);                           \
}
#define DEFINE_READER_PROPERTY_STRING_GETTER(name, fst_func)        \
static PyObject*                                                    \
reader_get_ ## name(reader_object* self, PyObject* Py_UNUSED(args)) \
{                                                                   \
    const char* property = fst_func(self->ctx);                     \
    if (property == NULL)                                           \
        Py_RETURN_NONE;                                             \
    return PyUnicode_FromString(property);                          \
}

#define DEFINE_READER_PROPERTY(name, help) {                        \
    #name                       ,                                   \
    (getter)reader_get_ ## name ,                                   \
    NULL                        ,                                   \
    help                        ,                                   \
    NULL                        ,                                   \
}

DEFINE_READER_PROPERTY_UINT64_GETTER(alias_count               , fstReaderGetAliasCount);
DEFINE_READER_PROPERTY_SINT64_GETTER(double_endian_match_state , fstReaderGetDoubleEndianMatchState);
DEFINE_READER_PROPERTY_UINT64_GETTER(end_time                  , fstReaderGetEndTime);
DEFINE_READER_PROPERTY_SINT64_GETTER(file_type                 , fstReaderGetFileType);
DEFINE_READER_PROPERTY_SINT64_GETTER(fseek_failed              , fstReaderGetFseekFailed);
DEFINE_READER_PROPERTY_SINT64_GETTER(max_handle                , fstReaderGetMaxHandle);
DEFINE_READER_PROPERTY_UINT64_GETTER(memory_used_by_writer     , fstReaderGetMemoryUsedByWriter);
DEFINE_READER_PROPERTY_UINT64_GETTER(dump_activity_changes     , fstReaderGetNumberDumpActivityChanges);
DEFINE_READER_PROPERTY_UINT64_GETTER(scope_count               , fstReaderGetScopeCount);
DEFINE_READER_PROPERTY_UINT64_GETTER(start_time                , fstReaderGetStartTime);
DEFINE_READER_PROPERTY_SINT64_GETTER(time_scale                , fstReaderGetTimescale);
DEFINE_READER_PROPERTY_SINT64_GETTER(time_zero                 , fstReaderGetTimezero);
DEFINE_READER_PROPERTY_UINT64_GETTER(value_change_section_count, fstReaderGetValueChangeSectionCount);
DEFINE_READER_PROPERTY_UINT64_GETTER(var_count                 , fstReaderGetVarCount);
DEFINE_READER_PROPERTY_STRING_GETTER(version                   , fstReaderGetVersionString);
DEFINE_READER_PROPERTY_STRING_GETTER(date                      , fstReaderGetDateString);

static PyGetSetDef  reader_getset[] = {
    DEFINE_READER_PROPERTY(alias_count               , "Number of alases."     ),
    DEFINE_READER_PROPERTY(double_endian_match_state , ""                      ),
    DEFINE_READER_PROPERTY(end_time                  , ""                      ),
    DEFINE_READER_PROPERTY(file_type                 , ""                      ),
    DEFINE_READER_PROPERTY(fseek_failed              , ""                      ),
    DEFINE_READER_PROPERTY(max_handle                , "Number of max handles."),
    DEFINE_READER_PROPERTY(memory_used_by_writer     , ""                      ),
    DEFINE_READER_PROPERTY(dump_activity_changes     , ""                      ),
    DEFINE_READER_PROPERTY(scope_count               , ""                      ),
    DEFINE_READER_PROPERTY(start_time                , ""),
    DEFINE_READER_PROPERTY(time_scale                , ""),
    DEFINE_READER_PROPERTY(time_zero                 , ""),
    DEFINE_READER_PROPERTY(value_change_section_count, "Number of value change sections."),
    DEFINE_READER_PROPERTY(var_count                 , "Number of variables."  ),
    DEFINE_READER_PROPERTY(version                   , ""),
    DEFINE_READER_PROPERTY(date                      , ""),
    {NULL}
};

static PyMethodDef  reader_methods[] = {
    {   "set_facility_process_mask",
        (PyCFunction)reader_set_facility_process_mask,
        METH_VARARGS | METH_KEYWORDS,
        PyDoc_STR(
           "set_facility_process_mask(handle)\n"
           "--\n"
           "\n"
           "Enable value-change processing for the specified facility handle."
        )
    },
    {   "set_facility_process_mask_all",
        (PyCFunction)reader_set_facility_process_mask_all,
        METH_VARARGS,
        PyDoc_STR(
            "set_facility_process_mask_all()\n"
            "--\n"
            "\n"
            "Enable value-change processing for all facilities."
        )
    },
    {   "clear_facility_process_mask",
        (PyCFunction)reader_clear_facility_process_mask,
        METH_VARARGS | METH_KEYWORDS,
        PyDoc_STR(
            "clear_facility_process_mask(handle)\n"
            "--\n"
            "\n"
            "Disable value-change processing for the specified facility handle."
        )
    },
    {   "clear_facility_process_mask_all",
        (PyCFunction)reader_clear_facility_process_mask_all,
        METH_VARARGS,
        PyDoc_STR(
            "clear_facility_process_mask_all()\n"
            "--\n"
            "\n"
            "Disable value-change processing for all facilities."
        )
    },
    {   "get_facility_process_mask",
        (PyCFunction)reader_get_facility_process_mask,
        METH_VARARGS | METH_KEYWORDS,
        PyDoc_STR(
            "get_facility_process_mask(handle)\n"
            "--\n"
            "\n"
            "Return True if value-change processing is enabled for the specified facility."
       )
    },
    {   "hiers",
        (PyCFunction)reader_hiers,
        METH_NOARGS,
        PyDoc_STR(
            "hiers()\n"
            "--\n"
            "\n"
            "Return an iterator over FST hierarchy objects."
        )
    },
    {   "blocks",
        (PyCFunction)reader_blocks,
        METH_NOARGS,
        PyDoc_STR(
          "blocks()\n"
          "--\n"
          "\n"
          "Return an iterator over FST value changes.\n"
          "Each item is returned as a tuple:\n"
          "    (time, facidx, value)\n"
        )
    },
    {   "close",
        (PyCFunction)reader_close,
        METH_NOARGS,
        PyDoc_STR(
            "close()\n"
            "--\n"
            "\n"
            "Close the FST reader and release resources."
       )
    },
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

    if (hier_module == NULL) {
        hier_module = PyImport_ImportModule(PACKAGE_NAME_STRING ".hier");
        if (hier_module == NULL) {
            Py_DECREF(&reader_type);
            Py_DECREF(m);
            return NULL;
        }
    }

    return m;
}
