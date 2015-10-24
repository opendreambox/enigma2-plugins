/*###########################################################################
#
# Copyright (C) 2007 - 2009 by
# nixkoenner <nixkoenner@newnigma2.to>
# License: GPL
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
###########################################################################*/

#include <stdio.h>
#include <stdlib.h>

#include "nbtscan.h"
#include "smbinfo.h"
#include "showmount.h"

static PyObject *_netInfo(PyObject *self, PyObject *args)
{
	const unsigned int max_hosts = 256;
	netinfo *nInfo;
	char *s;
	PyObject *result;
	unsigned int i, n;

	if(!PyArg_ParseTuple(args, "s", &s)) {
		PyErr_SetString(PyExc_TypeError, "netInfo(ip/24)");
		return NULL;
	}

	result = PyList_New(0);
	if (result == NULL)
		return NULL;

	nInfo = PyMem_New(netinfo, max_hosts);
	if (nInfo == NULL)
		return result;

	memset(nInfo, 0, sizeof(netinfo) * max_hosts);

	Py_BEGIN_ALLOW_THREADS
	n = netInfo(s, nInfo, max_hosts);
	Py_END_ALLOW_THREADS

	for (i = 0; i < n; i++) {
		PyObject *plist = PyList_New(6);
		if (plist == NULL)
			break;
		PyList_SET_ITEM(plist, 0, PyString_FromString("host"));
		PyList_SET_ITEM(plist, 1, PyString_FromString(nInfo[i].name));
		PyList_SET_ITEM(plist, 2, PyString_FromString(nInfo[i].ip));
		PyList_SET_ITEM(plist, 3, PyString_FromString(nInfo[i].mac));
		PyList_SET_ITEM(plist, 4, PyString_FromString(nInfo[i].domain));
		PyList_SET_ITEM(plist, 5, PyString_FromString(nInfo[i].service));
		PyList_Append(result, plist);
		Py_DECREF(plist);
	}

	PyMem_Free(nInfo);
	return result;
}

static PyObject *_nfsShare(PyObject *self, PyObject *args)
{
	const unsigned int max_shares = 256;
	nfsinfo *nfsInfo;
	char *s;
	char *r;
	PyObject *plist, *result;
	unsigned int i;
	int n;

	if(!PyArg_ParseTuple(args, "ss", &s, &r)) {
		PyErr_SetString(PyExc_TypeError, "nfsShare(ip,rechnername)");
		return NULL;
	}

	result = PyList_New(0);
	if (result == NULL)
		return NULL;

	nfsInfo = PyMem_New(nfsinfo, max_shares);
	if (nfsInfo == NULL)
		return result;

	memset(nfsInfo, 0, sizeof(nfsinfo) * max_shares);

	Py_BEGIN_ALLOW_THREADS
	n = showNfsShare(s, nfsInfo, max_shares);
	Py_END_ALLOW_THREADS
	if (n >= 0)
	{
		for (i = 0; i < n; i++) {
			plist = PyList_New(6);
			if (plist == NULL)
				break;
			PyList_SET_ITEM(plist, 0, PyString_FromString("nfsShare"));
			PyList_SET_ITEM(plist, 1, PyString_FromString(r));
			PyList_SET_ITEM(plist, 2, PyString_FromString(s));
			PyList_SET_ITEM(plist, 3, PyString_FromString(nfsInfo[i].ip));
			PyList_SET_ITEM(plist, 4, PyString_FromString(nfsInfo[i].share));
			PyList_SET_ITEM(plist, 5, PyString_FromString(""));
			PyList_Append(result, plist);
			Py_DECREF(plist);
		}
	}
	else
	{
		plist = PyList_New(1);
		if (plist != NULL) {
			PyList_SET_ITEM(plist, 0, PyString_FromString(nfsInfo[0].share));
			PyList_Append(result, plist);
			Py_DECREF(plist);
		}
	}

	PyMem_Free(nfsInfo);
	return result;
}

static PyObject *_smbShare(PyObject *self, PyObject *args)
{
	const unsigned int max_shares = 128;
	int i, n;
	char *s;
	char *r;
	char *u;
	char *p;
	shareinfo *sInfo;
	PyObject *plist, *result;

	if(!PyArg_ParseTuple(args, "ssss", &s,&r,&u,&p)) {
		PyErr_SetString(PyExc_TypeError, "getInfo(ip, rechnername, username, passwort)");
		return NULL;
	}

	result = PyList_New(0);
	if (result == NULL)
		return NULL;

	sInfo = PyMem_New(shareinfo, max_shares);
	if (sInfo == NULL)
		return result;

	memset(sInfo, 0, sizeof(shareinfo) * max_shares);

	Py_BEGIN_ALLOW_THREADS
	n = smbInfo(s, r, u, p, sInfo, max_shares);
	Py_END_ALLOW_THREADS

	for (i = 0; i < n; i++) {
		plist = PyList_New(6);
		if (plist == NULL)
			break;
		PyList_SET_ITEM(plist, 0, PyString_FromString("smbShare"));
		PyList_SET_ITEM(plist, 1, PyString_FromString(r));
		PyList_SET_ITEM(plist, 2, PyString_FromString(s));
		PyList_SET_ITEM(plist, 3, PyString_FromString(sInfo[i].sharename));
		PyList_SET_ITEM(plist, 4, PyString_FromString(sInfo[i].typ));
		PyList_SET_ITEM(plist, 5, PyString_FromString(sInfo[i].comment));
		PyList_Append(result, plist);
		Py_DECREF(plist);
	}

	PyMem_Free(sInfo);
	return result;
}

static PyMethodDef netscanmethods[] = {
	{"netInfo", _netInfo, METH_VARARGS},
	{"smbShare", _smbShare, METH_VARARGS},
	{"nfsShare", _nfsShare, METH_VARARGS},
	{NULL, NULL}
};

void initnetscan(void)
{
	Py_InitModule("netscan", netscanmethods);
}

