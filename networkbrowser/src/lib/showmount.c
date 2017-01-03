/*
 * showmount.c -- show mount information for an NFS server
 * Copyright (C) 1993 Rick Sladkey <jrs@world.std.com>
 * Copyright (C) 2017 Dream Property GmbH
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2, or (at your option)
 * any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 */

#ifdef HAVE_CONFIG_H
#include <enigma2-plugins-config.h>
#endif

#include <stdio.h>
#include <rpc/clnt.h>
#include <rpc/pmap_prot.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <sys/time.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>
#include <memory.h>
#include <stdlib.h>
#include <fcntl.h>

#include <netdb.h>
#include <arpa/inet.h>
#include <errno.h>
#include <getopt.h>
#include <rpcsvc/mount.h>
#include <unistd.h>

#include "nfsrpc.h"

#define TOTAL_TIMEOUT	2

static const char *mount_pgm_tbl[] = {
	"showmount",
	"mount",
	"mountd",
	NULL,
};

static rpcvers_t mount_vers_tbl[] = {
	3, /* MOUNTVERS_NFSV3 */
	2, /* MOUNTVERS_POSIX */
	MOUNTVERS,
};
static const unsigned int max_vers_tblsz = 
	(sizeof(mount_vers_tbl)/sizeof(mount_vers_tbl[0]));

/*
 * Generate an RPC client handle connected to the mountd service
 * at @hostname, or die trying.
 *
 * Supports both AF_INET and AF_INET6 server addresses.
 */
static CLIENT *nfs_get_mount_client(const char *hostname, rpcvers_t vers)
{
	rpcprog_t program = nfs_getrpcbyname(MOUNTPROG, mount_pgm_tbl);
	CLIENT *client;
	const struct timeval to = {
		.tv_sec = 2,
	};

	client = clnt_create_timed(hostname, program, vers, "tcp", &to);
	if (client)
		return client;
	client = clnt_create_timed(hostname, program, vers, "udp", &to);
	if (client)
		return client;

	return NULL;
}

static PyObject *showmount(PyObject *self, PyObject *args)
{
	enum clnt_stat clnt_stat;
	struct timeval total_timeout;
	CLIENT *mclient;
	groups grouplist;
	exports exportlist;
	int unsigned vers=0;
	PyObject *result;
	char *hostname;

	if (!PyArg_ParseTuple(args, "s", &hostname)) {
		PyErr_SetString(PyExc_TypeError, "showmount(node)");
		return NULL;
	}

	result = PyList_New(0);
	if (result == NULL)
		return result;

	Py_BEGIN_ALLOW_THREADS;

	mclient = nfs_get_mount_client(hostname, mount_vers_tbl[vers]);
	if (mclient == NULL) {
		Py_BLOCK_THREADS;
		Py_DECREF(result);
		PyErr_SetString(PyExc_IOError, clnt_spcreateerror("clnt_create_timed"));
		return NULL;
	}
	mclient->cl_auth = nfs_authsys_create();
	if (mclient->cl_auth == NULL) {
		clnt_destroy(mclient);
		Py_BLOCK_THREADS;
		Py_DECREF(result);
		PyErr_SetString(PyExc_IOError, "Unable to create RPC auth handle");
		return NULL;
	}
	total_timeout.tv_sec = TOTAL_TIMEOUT;
	total_timeout.tv_usec = 0;

again:
	exportlist = NULL;

	clnt_stat = clnt_call(mclient, MOUNTPROC_EXPORT,
		(xdrproc_t)xdr_void, NULL,
		(xdrproc_t)xdr_exports, &exportlist,
		total_timeout);
	if (clnt_stat == RPC_PROGVERSMISMATCH) {
		if (++vers < max_vers_tblsz) {
			CLNT_CONTROL(mclient, CLSET_VERS, &mount_vers_tbl[vers]);
			goto again;
		}
	}
	if (clnt_stat != RPC_SUCCESS) {
		Py_BLOCK_THREADS;
		Py_DECREF(result);
		PyErr_SetString(PyExc_IOError, clnt_sperror(mclient, "rpc mount export"));
		clnt_destroy(mclient);
		return NULL;
	}

	Py_END_ALLOW_THREADS;

	while (exportlist) {
		PyObject *dict, *dir, *groups;

		dict = PyDict_New();
		if (dict == NULL)
			break;
		groups = PyList_New(0);
		if (groups == NULL) {
			Py_DECREF(dict);
			break;
		}

		dir = PyString_FromString(exportlist->ex_dir);
		PyDict_SetItemString(dict, "dir", dir);
		Py_DECREF(dir);
		PyDict_SetItemString(dict, "groups", groups);
		Py_DECREF(groups);
		PyList_Append(result, dict);
		Py_DECREF(dict);

		for (grouplist = exportlist->ex_groups; grouplist; grouplist = grouplist->gr_next) {
			PyObject *name = PyString_FromString(grouplist->gr_name);
			PyList_Append(groups, name);
			Py_DECREF(name);
		}

		exportlist = exportlist->ex_next;
	}

	clnt_destroy(mclient);
	return result;
}

static PyMethodDef ops[] = {
	{ "showmount", showmount, METH_VARARGS },
	{ NULL, }
};

void initnfsutils(void)
{
	Py_InitModule("nfsutils", ops);
}
