include $(top_srcdir)/Rules-cpp.mak

AM_CFLAGS += $(LIBTIRPC_CFLAGS)

plugindir = $(libdir)/enigma2/python/Plugins/SystemPlugins/NetworkBrowser

plugin_LTLIBRARIES = netscan.la rpcinfo.la

netscan_la_SOURCES = \
	main.c \
	nbtscan.c \
	nbtscan.h \
	showmount.c \
	showmount.h \
	smb.h \
	smbinfo.c \
	smbinfo.h \
	statusq.c \
	statusq.h

netscan_la_LDFLAGS = \
	$(PLUGIN_LIBTOOL_FLAGS)

netscan_la_LIBADD = \
	$(LIBTIRPC_LIBS) \
	$(PYTHON_LDFLAGS) \
	-lnfs -lrpcsvc

rpcinfo_la_SOURCES = \
	rpcinfo.c

rpcinfo_la_LIBADD = \
	$(LIBTIRPC_LIBS)

rpcinfo_la_LDFLAGS = \
	$(PLUGIN_LIBTOOL_FLAGS)
