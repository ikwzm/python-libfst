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
#define MODULE_NAME         hier
#endif

#define MODULE_VERSION      "0.0.1"
#define MODULE_AUTHOR       "Ichiro Kawazome"
#define MODULE_AUTHOR_EMAIL "ichiro_k@ca2-so-net.ne.jp"
#define MODULE_LICENSE      "BSD 2-Clause"
#define MODULE_DESCRIPTION  "GTKWave FST Hier Module"

#define TO_STR(x)           #x
#define NAME_TO_STR(x)      TO_STR(x)
#define PACKAGE_NAME_STRING NAME_TO_STR(PACKAGE_NAME)
#define MODULE_NAME_STRING  NAME_TO_STR(MODULE_NAME)

static PyObject*
new_unicode_or_none(const char* s)
{
    if (s)
        return PyUnicode_FromString(s);
    else
        return Py_NewRef(Py_None);
}

typedef struct {
    PyObject_HEAD
    unsigned char  type;
    PyObject*      name;
    PyObject*      component;
} hier_scope_object;

static PyMemberDef hier_scope_members[] = {
    {"scope_type", Py_T_UBYTE    , offsetof(hier_scope_object, type     ), Py_READONLY, "Scope type"},
    {"name"      , Py_T_OBJECT_EX, offsetof(hier_scope_object, name     ), Py_READONLY, "Scope name"},
    {"component" , Py_T_OBJECT_EX, offsetof(hier_scope_object, component), Py_READONLY, "Scope component"},
    {NULL}
};

#define SCOPE_OBJECT_NAME_STRING "Scope"

static PyObject*
hier_scope_repr(hier_scope_object* self)
{
    return PyUnicode_FromFormat(
        PACKAGE_NAME_STRING "." MODULE_NAME_STRING "." SCOPE_OBJECT_NAME_STRING
        "(scope_type=%d, name=%R, component=%R)",
        self->type,
        self->name,
        self->component
    );
}

static void
hier_scope_dealloc(hier_scope_object* self)
{
    Py_XDECREF(self->name);
    Py_XDECREF(self->component);
    Py_TYPE(self)->tp_free((PyObject*)self);
}    

static PyTypeObject hier_scope_type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name       = PACKAGE_NAME_STRING "." MODULE_NAME_STRING "." SCOPE_OBJECT_NAME_STRING,
    .tp_basicsize  = sizeof(hier_scope_object),
    .tp_dealloc    = (destructor)hier_scope_dealloc,
    .tp_repr       = (reprfunc)hier_scope_repr,
    .tp_flags      = Py_TPFLAGS_DEFAULT,
    .tp_members    = hier_scope_members,
    .tp_doc        = "GTKWave FST hierarchy scope",
};

static PyObject*
hier_scope_from_fst(const struct fstHier* h)
{
    hier_scope_object* obj = PyObject_New(hier_scope_object, &hier_scope_type);

    if (obj == NULL)
        return NULL;
    obj->type      = h->u.scope.typ;
    obj->name      = NULL;
    obj->component = NULL;

    obj->name      = new_unicode_or_none(h->u.scope.name);
    if (obj->name == NULL) {
        Py_DECREF(obj);
        return NULL;
    }

    obj->component = new_unicode_or_none(h->u.scope.component);
    if (obj->component == NULL) {
        Py_DECREF(obj);
        return NULL;
    }
    return (PyObject*) obj;
}

typedef struct {
    PyObject_HEAD
} hier_upscope_object;

#define UPSCOPE_OBJECT_NAME_STRING "UpScope"

static PyObject*
hier_upscope_repr(hier_upscope_object* self)
{
    return PyUnicode_FromFormat(
        PACKAGE_NAME_STRING "." MODULE_NAME_STRING "." UPSCOPE_OBJECT_NAME_STRING "()"
    );
}

static void
hier_upscope_dealloc(hier_upscope_object* self)
{
    Py_TYPE(self)->tp_free((PyObject*)self);
}    

static PyTypeObject hier_upscope_type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name       = PACKAGE_NAME_STRING "." MODULE_NAME_STRING "." UPSCOPE_OBJECT_NAME_STRING,
    .tp_basicsize  = sizeof(hier_upscope_object),
    .tp_dealloc    = (destructor)hier_upscope_dealloc,
    .tp_repr       = (reprfunc)hier_upscope_repr,
    .tp_flags      = Py_TPFLAGS_DEFAULT,
    .tp_doc        = "GTKWave FST hierarchy upscope",
};

static PyObject*
hier_upscope_from_fst(const struct fstHier* h)
{
    hier_upscope_object* obj = PyObject_New(hier_upscope_object, &hier_upscope_type);

    if (obj == NULL)
        return NULL;
    return (PyObject*) obj;
}

typedef struct {
    PyObject_HEAD
    unsigned char      type;
    unsigned char      direction;
    PyObject*          name;
    unsigned long long length;
    unsigned long long handle;
    int                is_alias;
} hier_var_object;

static PyMemberDef hier_var_members[] = {
    {"var_type" , Py_T_UBYTE    , offsetof(hier_var_object, type     ), Py_READONLY, "Variable type"},
    {"direction", Py_T_UBYTE    , offsetof(hier_var_object, direction), Py_READONLY, "Variable direction"},
    {"name"     , Py_T_OBJECT_EX, offsetof(hier_var_object, name     ), Py_READONLY, "Variable name"},
    {"length"   , Py_T_ULONGLONG, offsetof(hier_var_object, length   ), Py_READONLY, "Bit Width"},
    {"handle"   , Py_T_ULONGLONG, offsetof(hier_var_object, handle   ), Py_READONLY, "Variable handle"},
    {"is_alias" , Py_T_BOOL     , offsetof(hier_var_object, is_alias ), Py_READONLY, "True if alias"},
    {NULL}
};

#define VAR_OBJECT_NAME_STRING "Var"

static PyObject*
hier_var_repr(hier_var_object* self)
{
    return PyUnicode_FromFormat(
        PACKAGE_NAME_STRING "." MODULE_NAME_STRING "." VAR_OBJECT_NAME_STRING
        "(var_type=%d, direction=%d, name=%R, length=%llu, handle=%llu, alias=%s)",
        self->type,
        self->direction,
        self->name,
        self->length,
        self->handle,
        self->is_alias ? "True" : "False"
    );
}

static void
hier_var_dealloc(hier_var_object* self)
{
    Py_XDECREF(self->name);
    Py_TYPE(self)->tp_free((PyObject*)self);
}    

static PyTypeObject hier_var_type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name       = PACKAGE_NAME_STRING "." MODULE_NAME_STRING "." VAR_OBJECT_NAME_STRING,
    .tp_basicsize  = sizeof(hier_var_object),
    .tp_dealloc    = (destructor)hier_var_dealloc,
    .tp_repr       = (reprfunc)hier_var_repr,
    .tp_flags      = Py_TPFLAGS_DEFAULT,
    .tp_members    = hier_var_members,
    .tp_doc        = "GTKWave FST hierarchy variable",
};

static PyObject*
hier_var_from_fst(const struct fstHier* h)
{
    hier_var_object* obj = PyObject_New(hier_var_object, &hier_var_type);

    if (obj == NULL)
        return NULL;
    obj->type      = h->u.var.typ;
    obj->direction = h->u.var.direction;
    obj->length    = (unsigned long long)h->u.var.length;
    obj->handle    = (unsigned long long)h->u.var.handle;
    obj->is_alias  = h->u.var.is_alias;
    obj->name      = new_unicode_or_none(h->u.var.name);
    if (obj->name == NULL) {
        Py_DECREF(obj);
        return NULL;
    }
    return (PyObject*) obj;
}

typedef struct {
    PyObject_HEAD
    unsigned char      type;
    unsigned char      subtype;
    PyObject*          name;
    unsigned long long arg;
} hier_attr_object;

static PyMemberDef hier_attr_members[] = {
    {"attr_type", Py_T_UBYTE    , offsetof(hier_attr_object, type   ), Py_READONLY, "Attribute type"},
    {"subtype"  , Py_T_UBYTE    , offsetof(hier_attr_object, subtype), Py_READONLY, "Attribute subtype"},
    {"name"     , Py_T_OBJECT_EX, offsetof(hier_attr_object, name   ), Py_READONLY, "Attribute name"},
    {"arg"      , Py_T_ULONGLONG, offsetof(hier_attr_object, arg    ), Py_READONLY, "Attribute Argment"},
    {NULL}
};

#define ATTR_OBJECT_NAME_STRING "Attr"

static PyObject*
hier_attr_repr(hier_attr_object* self)
{
    return PyUnicode_FromFormat(
        PACKAGE_NAME_STRING "." MODULE_NAME_STRING "." ATTR_OBJECT_NAME_STRING
        "(attr_type=%d, subtype=%d, name=%R, arg=%llu)",
        self->type,
        self->subtype,
        self->name,
        self->arg
    );
}

static void
hier_attr_dealloc(hier_attr_object* self)
{
    Py_XDECREF(self->name);
    Py_TYPE(self)->tp_free((PyObject*)self);
}    

static PyTypeObject hier_attr_type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name       = PACKAGE_NAME_STRING "." MODULE_NAME_STRING "." ATTR_OBJECT_NAME_STRING,
    .tp_basicsize  = sizeof(hier_attr_object),
    .tp_dealloc    = (destructor)hier_attr_dealloc,
    .tp_repr       = (reprfunc)hier_attr_repr,
    .tp_flags      = Py_TPFLAGS_DEFAULT,
    .tp_members    = hier_attr_members,
    .tp_doc        = "GTKWave FST reader hierarchy attribute begin",
};

static PyObject*
hier_attr_from_fst(const struct fstHier* h)
{
    hier_attr_object* obj = PyObject_New(hier_attr_object, &hier_attr_type);

    if (obj == NULL)
        return NULL;
    obj->type      = h->u.attr.typ;
    obj->subtype   = h->u.attr.subtype;
    obj->arg       = h->u.attr.arg;
    obj->name      = new_unicode_or_none(h->u.attr.name);
    if (obj->name == NULL) {
        Py_DECREF(obj);
        return NULL;
    }
    return (PyObject*) obj;
}

typedef struct {
    PyObject_HEAD
} hier_attr_end_object;

#define ATTR_END_OBJECT_NAME_STRING "AttrEnd"

static PyObject*
hier_attr_end_repr(hier_attr_end_object* self)
{
    return PyUnicode_FromFormat(
        PACKAGE_NAME_STRING "." MODULE_NAME_STRING "." ATTR_END_OBJECT_NAME_STRING "()"
    );
}

static void
hier_attr_end_dealloc(hier_attr_end_object* self)
{
    Py_TYPE(self)->tp_free((PyObject*)self);
}    

static PyTypeObject hier_attr_end_type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name       = PACKAGE_NAME_STRING "." MODULE_NAME_STRING "." ATTR_END_OBJECT_NAME_STRING,
    .tp_basicsize  = sizeof(hier_attr_end_object),
    .tp_dealloc    = (destructor)hier_attr_end_dealloc,
    .tp_repr       = (reprfunc)hier_attr_end_repr,
    .tp_flags      = Py_TPFLAGS_DEFAULT,
    .tp_doc        = "GTKWave FST reader hierarchy attribute end",
};

static PyObject*
hier_attr_end_from_fst(const struct fstHier* h)
{
    hier_attr_end_object* obj = PyObject_New(hier_attr_end_object, &hier_attr_end_type);

    if (obj == NULL)
        return NULL;
    return (PyObject*) obj;
}

static PyObject*
hier_from_fst(PyObject *self, PyObject *args)
{
    unsigned long long ptr;
    struct fstHier*    h;

    if (!PyArg_ParseTuple(args, "K", &ptr)) {
        return NULL;
    }

    h = (struct fstHier*)ptr;

    switch (h->htyp) {
        case FST_HT_SCOPE:
            return hier_scope_from_fst(h);
        case FST_HT_UPSCOPE:
            return hier_upscope_from_fst(h);
        case FST_HT_VAR:
            return hier_var_from_fst(h);
        case FST_HT_ATTRBEGIN:
            return hier_attr_from_fst(h);
        case FST_HT_ATTREND:
            return hier_attr_end_from_fst(h);
        default:
            Py_RETURN_NONE;
    }
}

static PyMethodDef hier_methods[] = {
    {"from_fst",(PyCFunction)hier_from_fst, METH_VARARGS, "Create hier object from fstHier"},
    {NULL}
};

static struct PyModuleDef hier_module = {
    PyModuleDef_HEAD_INIT,
    PACKAGE_NAME_STRING "." MODULE_NAME_STRING,
    MODULE_DESCRIPTION "\n"
    "License: " MODULE_LICENSE "\n"
    "Author:  " MODULE_AUTHOR  "\n"
    "Version: " MODULE_VERSION,
    -1,
    hier_methods,
};

#define PYINIT_FUNC_NAME(x) PyInit_ ## x
#define PYINIT_FUNC(x) PyMODINIT_FUNC PYINIT_FUNC_NAME(x)(void) 
PYINIT_FUNC(MODULE_NAME) {
    PyObject* m;

    if (PyType_Ready(&hier_scope_type) < 0) {
        return NULL;
    }
    if (PyType_Ready(&hier_upscope_type) < 0) {
        return NULL;
    }
    if (PyType_Ready(&hier_var_type) < 0) {
        return NULL;
    }
    if (PyType_Ready(&hier_attr_type) < 0) {
        return NULL;
    }
    if (PyType_Ready(&hier_attr_end_type) < 0) {
        return NULL;
    }

    m = PyModule_Create(&hier_module);
    if (m == NULL) {
        return NULL;
    }

    Py_INCREF(&hier_scope_type);
    if (PyModule_AddObject(m, SCOPE_OBJECT_NAME_STRING, (PyObject*)&hier_scope_type) < 0) {
        Py_DECREF(&hier_scope_type);
        Py_DECREF(m);
        return NULL;
    }
    
    Py_INCREF(&hier_upscope_type);
    if (PyModule_AddObject(m, UPSCOPE_OBJECT_NAME_STRING, (PyObject*)&hier_upscope_type) < 0) {
        Py_DECREF(&hier_upscope_type);
        Py_DECREF(m);
        return NULL;
    }
    
    Py_INCREF(&hier_var_type);
    if (PyModule_AddObject(m, VAR_OBJECT_NAME_STRING, (PyObject*)&hier_var_type) < 0) {
        Py_DECREF(&hier_var_type);
        Py_DECREF(m);
        return NULL;
    }
    
    Py_INCREF(&hier_attr_type);
    if (PyModule_AddObject(m, ATTR_OBJECT_NAME_STRING, (PyObject*)&hier_attr_type) < 0) {
        Py_DECREF(&hier_attr_type);
        Py_DECREF(m);
        return NULL;
    }
    
    Py_INCREF(&hier_attr_end_type);
    if (PyModule_AddObject(m, ATTR_END_OBJECT_NAME_STRING, (PyObject*)&hier_attr_end_type) < 0) {
        Py_DECREF(&hier_attr_end_type);
        Py_DECREF(m);
        return NULL;
    }
    
    return m;
}
