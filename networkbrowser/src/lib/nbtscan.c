/*###########################################################################
#
# written by :	Stephen J. Friedl
#		Software Consultant
#		steve@unixwiz.net
#
# Copyright (C) 2007 - 2008 by
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

#include <arpa/inet.h>
#include <netdb.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/time.h>
#include <unistd.h>
#include "nbtscan.h"
#include "statusq.h"

static bool python_hostinfo(const struct sockaddr_storage *ss, const struct nb_host_info *hostinfo, netinfo *nInfo)
{
	int unique;
	uint8_t service;

	if (hostinfo->names[0].ascii_name[0] == '\0')
		return false;

	memset(nInfo, 0, sizeof(netinfo));

	service = hostinfo->names[0].ascii_name[15];
	unique = !(hostinfo->names[0].rr_flags & 0x0080);
	strncpy(nInfo->name, hostinfo->names[0].ascii_name, 15);
	strncpy(nInfo->domain, hostinfo->names[1].ascii_name, 15);
	sprintf(nInfo->service, "%s", getnbservicename(service, unique, hostinfo->names[0].ascii_name));
	getnameinfo((const struct sockaddr *)ss, sizeof(struct sockaddr_storage), nInfo->ip, sizeof(nInfo->ip), NULL, 0, NI_NUMERICHOST);
	return true;
}

#define BUFFSIZE 1024

bool nodeInfo(const char *node, netinfo *nInfo)
{
	int timeout = 1000;
	char buff[BUFFSIZE];
	int sock;
	socklen_t addrlen;
	struct sockaddr_storage ss;
	struct timeval select_timeout, last_send_time;
	struct nb_host_info hostinfo;
	fd_set fdsr;
	fd_set fdsw;
	int size;
	bool retval = false;
	uint32_t rtt_base;	/* Base time (seconds) for round trip time calculations */
	struct addrinfo hints;
	struct addrinfo *result;
	int s;

	memset(&hints, 0, sizeof(hints));
	hints.ai_family = AF_UNSPEC;
	hints.ai_socktype = SOCK_DGRAM;
	hints.ai_flags = AI_ADDRCONFIG | AI_NUMERICHOST | AI_NUMERICSERV;
	hints.ai_protocol = IPPROTO_UDP;

	s = getaddrinfo(node, "137", &hints, &result);
	if (s != 0) {
		fprintf(stderr, "getaddrinfo: %s\n", gai_strerror(s));
		return 0;
	}

	/* Finished with options */

	/* Prepare socket and address structures */
	sock = socket(result->ai_family, result->ai_socktype, result->ai_protocol);
	if (sock < 0) {
		perror("socket");
		goto out_freeaddrinfo;
	}

	FD_ZERO(&fdsr);
	FD_SET(sock, &fdsr);

	FD_ZERO(&fdsw);
	FD_SET(sock, &fdsw);

	/* timeout is in milliseconds */
	select_timeout.tv_sec = 60;	/* Default 1 min to survive ARP timeouts */
	select_timeout.tv_usec = 0;

	/* Calculate interval between subsequent sends */
	gettimeofday(&last_send_time, NULL);	/* Get current time */
	rtt_base = last_send_time.tv_sec;

	/* Send queries, receive answers and print results */

	while ((select(sock + 1, &fdsr, &fdsw, NULL, &select_timeout)) > 0) {
		if (FD_ISSET(sock, &fdsr)) {
			addrlen = sizeof(struct sockaddr_storage);
			size = recvfrom(sock, buff, BUFFSIZE, 0, (struct sockaddr *)&ss, &addrlen);
			if (size <= 0) {
				char addrstr[INET6_ADDRSTRLEN];
				getnameinfo((const struct sockaddr *)&ss, sizeof(ss), addrstr, sizeof(addrstr), NULL, 0, NI_NUMERICHOST);
				fprintf(stderr, "recvfrom %s: %m", addrstr);
				continue;
			}

			parse_response(buff, size, &hostinfo);
			if (python_hostinfo(&ss, &hostinfo, nInfo)) {
				retval = true;
				break;
			}
		}

		FD_ZERO(&fdsr);
		FD_SET(sock, &fdsr);

		if (FD_ISSET(sock, &fdsw)) {
			send_query(sock, result->ai_addr, rtt_base);
			FD_ZERO(&fdsw);
			/* timeout is in milliseconds */
			select_timeout.tv_sec = timeout / 1000;
			select_timeout.tv_usec = (timeout % 1000) * 1000;	/* Microseconds */
		}
	}

	close(sock);
out_freeaddrinfo:
	freeaddrinfo(result);
	return retval;
}
