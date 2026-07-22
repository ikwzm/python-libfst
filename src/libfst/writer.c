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
#define MODULE_NAME         writer
#endif

#ifndef OBJECT_NAME
#define OBJECT_NAME         Writer
#endif

#define MODULE_VERSION      "0.0.1"
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
        PyErr_Format(PyExc_OSError,
                     "cannot create FST file \"%s\"",
                     filename);
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

static PyObject*
writer_close(writer_object* self, PyObject* Py_UNUSED(args))
{
    if (self->ctx != NULL) {
        fstWriterClose(self->ctx);
        self->ctx = NULL;
    }
    Py_RETURN_NONE;
}

static PyMethodDef  writer_methods[] = {
    {"close", (PyCFunction)writer_close, METH_NOARGS, ""},
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
