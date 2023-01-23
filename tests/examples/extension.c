#define PY_SIZET_CLEAN
#include <Python.h>

static PyObject *
example_func(PyObject *self, PyObject *args)
{
    PyObject *ret = PyUnicode_FromString("Hello, world!");
    return ret;
}

static PyMethodDef ExtensionMethods[] = {
    {"example", example_func, METH_NOARGS},
    {NULL, NULL, 0, NULL}
}

static struct PyModuleDef extensionmodule = {
    PyModuleDef_HEAD_INIT,
    "extension",
    NULL,
    -1,
    ExtensionMethods,
}

PyMODINIT_FUNC
PyInit_extension(void)
{
    return PyModule_Create(&extensionmodule);
}