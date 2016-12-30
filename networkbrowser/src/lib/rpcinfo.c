/*
 * Copyright (c) 2009, Sun Microsystems, Inc.
 * Copyright (c) 2016, Dream Property GmbH
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 * - Redistributions of source code must retain the above copyright notice,
 *   this list of conditions and the following disclaimer.
 * - Redistributions in binary form must reproduce the above copyright notice,
 *   this list of conditions and the following disclaimer in the documentation
 *   and/or other materials provided with the distribution.
 * - Neither the name of Sun Microsystems, Inc. nor the names of its
 *   contributors may be used to endorse or promote products derived
 *   from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */
/*
 * Copyright (c) 1986 - 1991 by Sun Microsystems, Inc.
 */

#include <Python.h>
#include <ctype.h>
#include <netdb.h>
#include <rpc/clnt.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>

#define	MIN_VERS	((u_long)0)
#define	MAX_VERS	((u_long)4294967295UL)

static u_long getprognum(const char *arg)
{
  char *strptr;
  struct rpcent *rpc;
  u_long prognum;
  const char *tptr = arg;

  while (*tptr && isdigit (*tptr++))
	;
  if (*tptr || isalpha (*(tptr - 1)))
    {
      rpc = getrpcbyname (arg);
      if (rpc == NULL)
	{
	  fprintf (stderr, "rpcinfo: %s is unknown service\n", arg);
	  return ULONG_MAX;
	}
      prognum = rpc->r_number;
    }
  else
    {
      prognum = strtol (arg, &strptr, 10);
      if (strptr == arg || *strptr != '\0')
	{
	  fprintf (stderr, "rpcinfo: %s is illegal program number\n", arg);
	  return ULONG_MAX;
	}
    }
  return (prognum);
}

/*
 * This routine should take a pointer to an "rpc_err" structure, rather than
 * a pointer to a CLIENT structure, but "clnt_perror" takes a pointer to
 * a CLIENT structure rather than a pointer to an "rpc_err" structure.
 * As such, we have to keep the CLIENT structure around in order to print
 * a good error message.
 */
static bool pstatus(CLIENT *client, u_long prog, u_long vers)
{
	struct rpc_err rpcerr;

	clnt_geterr(client, &rpcerr);
	if (rpcerr.re_status != RPC_SUCCESS) {
		clnt_perror(client, "rpcinfo");
		printf("program %lu version %lu is not available\n", prog, vers);
		return false;
	}

	printf("program %lu version %lu ready and waiting\n", prog, vers);
	return true;
}

/*
 * If the version number is given, ping that (prog, vers); else try to find
 * the version numbers supported for that prog and ping all the versions.
 * Remote rpcbind is *contacted* for this service. The requests are
 * then sent directly to the services themselves.
 */
static bool progping(const char *netid, const char *host, const char *prognum_str, unsigned int versnum)
{
	CLIENT *client;
	const struct timeval to = {
		.tv_sec = 1,
	};
	enum clnt_stat rpc_stat;
	u_int32_t prognum, minvers, maxvers;
	struct rpc_err rpcerr;
	bool success = false;
	struct netconfig *nconf;

	prognum = getprognum(prognum_str);

	nconf = getnetconfigent(netid);
	if (nconf == NULL) {
		fprintf(stderr, "rpcinfo: Could not find %s\n", netid);
		return false;
	}
	client = clnt_tp_create_timed(host, prognum, versnum, nconf, &to);
	if (client == NULL) {
		clnt_pcreateerror("rpcinfo");
		return false;
	}
	rpc_stat = CLNT_CALL(client, NULLPROC, (xdrproc_t)xdr_void,
			NULL, (xdrproc_t)xdr_void,
			NULL, to);
	if (versnum != 0) {
		/* Version number was known */
		success = pstatus(client, prognum, versnum);
		CLNT_DESTROY(client);
		return success;
	}

	/*
	 * Version number not known.
	 * Start with invalid defaults.
	 */
	minvers = UINT_MAX;
	maxvers = 0;
	if (rpc_stat == RPC_PROGVERSMISMATCH) {
		clnt_geterr(client, &rpcerr);
		minvers = rpcerr.re_vers.low;
		maxvers = rpcerr.re_vers.high;
	} else if (rpc_stat == RPC_SUCCESS) {
		/*
		 * Oh dear, it DOES support version 0.
		 * Let's try version MAX_VERS.
		 */
		versnum = MAX_VERS;
		CLNT_CONTROL(client, CLSET_VERS, (char *)&versnum);
		rpc_stat = CLNT_CALL(client, NULLPROC,
				(xdrproc_t)xdr_void, NULL,
				(xdrproc_t)xdr_void, NULL, to);
		if (rpc_stat == RPC_PROGVERSMISMATCH) {
			clnt_geterr (client, &rpcerr);
			minvers = rpcerr.re_vers.low;
			maxvers = rpcerr.re_vers.high;
		}
	}

	for (versnum = minvers; versnum <= maxvers; versnum++) {
		CLNT_CONTROL(client, CLSET_VERS, (char *)&versnum);
		rpc_stat = CLNT_CALL(client, NULLPROC, (xdrproc_t)xdr_void,
				NULL, (xdrproc_t) xdr_void,
				NULL, to);
		success = pstatus(client, prognum, versnum);
		if (success)
			break;
	}

	CLNT_DESTROY(client);
	return success;
}

static PyObject *py_progping(PyObject *self, PyObject *args)
{
	char *netid;
	char *host;
	char *prognum;
	/*
	 * A call to version 0 should fail with a program/version
	 * mismatch, and give us the range of versions supported.
	 */
	int versnum = 0;
	PyObject *robj;
	int rv;

	if (!PyArg_ParseTuple(args, "sss|i", &netid, &host, &prognum, &versnum)) {
		PyErr_SetString(PyExc_TypeError, "bool progping(char *netid, char *host, char *prognum[, int versnum])");
		return NULL;
	}

	Py_BEGIN_ALLOW_THREADS
	rv = progping(netid, host, prognum, versnum);
	Py_END_ALLOW_THREADS

	robj = PyBool_FromLong(rv);
	Py_INCREF(robj);
	return robj;
}

static PyMethodDef ops[] = {
	{ "progping", py_progping, METH_VARARGS },
	{ NULL, },
};

void initrpcinfo(void)
{
	Py_InitModule("rpcinfo", ops);
}
