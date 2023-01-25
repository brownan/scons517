#define PY_SSIZE_T_CLEAN
#include <Python.h>

static PyObject *
example_func(PyObject *self, PyObject *args)
{
    printf("Hello, world!");

    Py_RETURN_NONE;
}

static PyMethodDef ExtensionMethods[] = {
    {"example", example_func, METH_NOARGS},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef extensionmodule = {
    PyModuleDef_HEAD_INIT,
    "extension",
    NULL,
    -1,
    ExtensionMethods,
};

PyMODINIT_FUNC
PyInit_extension(void)
{
    return PyModule_Create(&extensionmodule);
}