/*
Copyright (c) 2016, EPFL/Blue Brain Project

 This file is part of BluePyOpt <https://github.com/BlueBrain/BluePyOpt>

 This library is free software; you can redistribute it and/or modify it under
 the terms of the GNU Lesser General Public License version 3.0 as published
 by the Free Software Foundation.

 This library is distributed in the hope that it will be useful, but WITHOUT
 ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
 details.

 You should have received a copy of the GNU Lesser General Public License
 along with this library; if not, write to the Free Software Foundation, Inc.,
 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

 The code in this file was original written in 2015 at the                      
 BlueBrain Project, EPFL, Lausanne                                              
 The authors were Werner Van Geit, Michael Gevaert and Jean-Denis Courcol       
 It is based on a C implementation of the IBEA algorithm in the PISA            
 optimization framework developed at the ETH, Zurich                            
 http://www.tik.ee.ethz.ch/pisa/selectors/ibea/?page=ibea.php                   
 
*/

#include <Python.h>

static PyObject * eps_indicator(PyObject *self, PyObject *args)
{
    unsigned n_of_dimensions, dimension;
    double obj1, obj2, range;
    double eps, max_eps = 0.0;
    double min_box_bound, max_box_bound;
    // Individual 1 objectives
    PyObject * objectives1;
    // Individual 2 objectives 
    PyObject * objectives2;
    PyObject * min_box_bounds;
    PyObject * max_box_bounds;
    

    if (!PyArg_ParseTuple( args, "O!O!O!O!", 
                &PyList_Type, &objectives1, 
                &PyList_Type, &objectives2,
                &PyList_Type, &min_box_bounds, 
                &PyList_Type, &max_box_bounds
                )) return NULL;

    n_of_dimensions = PyList_Size(objectives1);
   

    for (dimension = 0; dimension < n_of_dimensions; dimension++) {
        min_box_bound = 
            PyFloat_AsDouble(PyList_GetItem(min_box_bounds, dimension));
        max_box_bound = 
            PyFloat_AsDouble(PyList_GetItem(max_box_bounds, dimension));
            
        range = max_box_bound - min_box_bound;

        obj1 = PyFloat_AsDouble(PyList_GetItem(objectives1, dimension));
        obj2 = PyFloat_AsDouble(PyList_GetItem(objectives2, dimension));

        eps = (obj1 - obj2) / range;

        // Find the maximum eps
        if (dimension == 0) {
            max_eps = eps;
        } else {
            if (eps > max_eps) max_eps = eps; 
        }
    } 

    return Py_BuildValue("f", max_eps);
}

static PyMethodDef EPSMethods[] = {
        {"indicator",  eps_indicator, METH_VARARGS,
               "Calculate the epsilon indicator."},
        {NULL, NULL, 0, NULL}        /* Sentinel */
};

PyMODINIT_FUNC initeps(void) {
    (void) Py_InitModule("eps", EPSMethods);
}
