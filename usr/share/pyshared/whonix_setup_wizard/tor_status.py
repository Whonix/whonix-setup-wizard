#!/usr/bin/python

import sys, fileinput
from subprocess import call
import os, time


def set_enabled():
    if not os.path.exists('/etc/tor/torrc'):
        return 'no_torrc'

    fh = open('/etc/tor/torrc','r')
    lines = fh.readlines()
    fh.close()

    line_exists = False

    for line in lines:
        if line.strip() == 'DisableNetwork 0':
            line_exists = True

            # tor might be stopped.
            command = 'service tor status'
            tor_status = call(command, shell=True)

            if tor_status != 0:
                command = 'service tor start'
                call(command, shell=True)

                command = 'service tor status'
                tor_status = call(command, shell=True)

                if tor_status == 0:
                    return 'tor_enabled'
                else:
                    return 'cannot_connect'

            return 'tor_already_enabled'

        elif line.strip() == '#DisableNetwork 0':
            line_exists = True

            for i, line in enumerate(fileinput.input('/etc/tor/torrc', inplace=1)):
                sys.stdout.write(line.replace('#DisableNetwork 0', 'DisableNetwork 0'))

            command = 'service tor start'
            call(command, shell=True)

            command = 'service tor reload'
            call(command, shell=True)
            #time.sleep(1)

            command = 'service tor status'
            tor_status = call(command, shell=True)

            # Extra start required when whonixsetup_check is auto-started.
            # tor start and tor reload returns 0, but tor status returns an error.
            # /run/tor/control and /run/tor/tor.pid are not written.
            # The same happen whether whonix-setup-wizard is run directly or
            # through /usr/lib/whonix-setup-wizard/whonixsetup_check_for_start.
            # The original setup (start-reload-status) works when run by the user.
            # Probably the Tor bug refereed to in /usr/lib/whonixsetup/ft_m_1.
            if tor_status != 0:
                command = 'service tor start'
                call(command, shell=True)
            #    time.sleep(1)

                command = 'service tor status'
                tor_status = call(command, shell=True)
                if tor_status != 0:
                    return 'cannot_connect'

            return 'tor_enabled'

    if not line_exists:
        return 'bad_torrc'


def set_disabled():
    if not os.path.exists('/etc/tor/torrc'):
        return 'no_torrc'

    fh = open('/etc/tor/torrc','r')
    lines = fh.readlines()
    fh.close()

    line_exists = False

    for line in lines:
        if line.strip() == '#DisableNetwork 0':
            line_exists = True
            return 'tor_already_disabled'

        elif line.strip() == 'DisableNetwork 0':
            line_exists = True

            for i, line in enumerate(fileinput.input('/etc/tor/torrc', inplace=1)):
                sys.stdout.write(line.replace('DisableNetwork 0', '#DisableNetwork 0'))

            command = 'service tor stop'
            call(command, shell=True)

            return 'tor_disabled'

    if not line_exists:
        return 'bad_torrc'
