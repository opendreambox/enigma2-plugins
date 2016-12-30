include $(top_srcdir)/Rules-cpp.mak

plugindir = $(libdir)/enigma2/python/Plugins/SystemPlugins/NetworkBrowser

plugin_LTLIBRARIES = netscan.la rpcinfo.la

netscan_la_SOURCES = \
	list.c \
	list.h \
	main.c \
	nbtscan.c \
	nbtscan.h \
	range.c \
	range.h \
	showmount.c \
	showmount.h \
	smb.h \
	smbinfo.c \
	smbinfo.h \
	statusq.c \
	statusq.h

netscan_la_LDFLAGS = \
	$(PLUGIN_LIBTOOL_FLAGS)

rpcinfo_la_CPPFLAGS = \
	$(AM_CPPFLAGS) \
	$(LIBTIRPC_CFLAGS)

rpcinfo_la_SOURCES = \
	rpcinfo.c

rpcinfo_la_LIBADD = \
	$(LIBTIRPC_LIBS)

rpcinfo_la_LDFLAGS = \
	$(PLUGIN_LIBTOOL_FLAGS)
