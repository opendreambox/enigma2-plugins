include $(top_srcdir)/Rules-cpp.mak

AM_CFLAGS += $(LIBTIRPC_CFLAGS)

plugindir = $(libdir)/enigma2/python/Plugins/SystemPlugins/NetworkBrowser

plugin_LTLIBRARIES = nfsutils.la rpcinfo.la

nfsutils_la_SOURCES = \
	showmount.c

nfsutils_la_LDFLAGS = \
	$(PLUGIN_LIBTOOL_FLAGS)

nfsutils_la_LIBADD = \
	$(LIBTIRPC_LIBS) \
	$(PYTHON_LDFLAGS) \
	-lnfs -lrpcsvc

rpcinfo_la_SOURCES = \
	rpcinfo.c

rpcinfo_la_LIBADD = \
	$(LIBTIRPC_LIBS)

rpcinfo_la_LDFLAGS = \
	$(PLUGIN_LIBTOOL_FLAGS)
