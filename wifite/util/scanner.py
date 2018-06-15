#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..tools.airodump import Airodump
from ..util.color import Color
from ..util.input import raw_input, xrange
from ..model.target import Target
from ..config import Configuration

from time import sleep, time

class Scanner(object):
    ''' Scans wifi networks & provides menu for selecting targets '''

    # Console code for moving up one line
    UP_CHAR = '\x1B[1F'

    def __init__(self):
        '''
            Starts scan, prints as it goes.
            Upon interrupt, sets 'targets'.
        '''
        self.previous_target_count = 0
        self.targets = []
        self.target = None # Specific target (based on ESSID/BSSID)

        self.err_msg = None

        Color.pl("")
        # Loads airodump with interface/channel/etc from Configuration
        try:
            with Airodump() as airodump:
                # Loop until interrupted (Ctrl+C)
                scan_start_time = time()

                while True:
                    if airodump.pid.poll() is not None:
                        # Airodump process died
                        self.err_msg = '\r{!} {R}Airodump exited unexpectedly (Code: %d){O} Command: {W}%s' % (airodump.pid.poll(), " ".join(airodump.pid.command))
                        raise KeyboardInterrupt

                    self.targets = airodump.get_targets()

                    if self.found_target():
                        # We found the target we want
                        return

                    for target in self.targets:
                        if target.bssid in airodump.decloaked_bssids:
                            target.decloaked = True

                    self.print_targets()

                    target_count = len(self.targets)
                    client_count = sum(
                                       [len(t.clients)
                                           for t in self.targets])
                    outline = "\r{+} Scanning"
                    if airodump.decloaking:
                        outline += " & decloaking"
                    outline += ". Found"
                    outline += " {G}%d{W} target(s)," % target_count
                    outline += " {G}%d{W} client(s)." % client_count
                    outline += " {O}Ctrl+C{W} when ready "
                    Color.clear_entire_line()
                    Color.p(outline)

                    if Configuration.scan_time > 0 and time() > scan_start_time + Configuration.scan_time:
                        return

                    sleep(1)
        except KeyboardInterrupt:
            pass

    def found_target(self):
        '''
            Check if we discovered the target AP
            Returns: the Target if found,
                     Otherwise None.
        '''
        bssid = Configuration.target_bssid
        essid = Configuration.target_essid

        if bssid is None and essid is None:
            return False

        for target in self.targets:
            if Configuration.wps_only and target.wps != True:
                continue
            if bssid and target.bssid and bssid.lower() == target.bssid.lower():
                self.target = target
                break
            if essid and target.essid and essid.lower() == target.essid.lower():
                self.target = target
                break

        if self.target:
            Color.pl('\n{+} {C}found target{G} %s {W}({G}%s{W})'
                % (self.target.bssid, self.target.essid))
            return True

        return False

    def print_targets(self):
        '''
            Prints targets to console
        '''
        if len(self.targets) == 0:
            Color.p('\r')
            return

        if self.previous_target_count > 0:
            # We need to "overwrite" the previous list of targets.
            if Configuration.verbose <= 1:
                # Don't clear screen buffer in verbose mode.
                if self.previous_target_count > len(self.targets) or \
                   Scanner.get_terminal_height() < self.previous_target_count + 3:
                    # Either:
                    # 1) We have less targets than before, so we can't overwrite the previous list
                    # 2) The terminal can't display the targets without scrolling.
                    # Clear the screen.
                    from ..util.process import Process
                    Process.call('clear')
                else:
                    # We can fit the targets in the terminal without scrolling
                    # "Move" cursor up so we will print over the previous list
                    Color.pl(Scanner.UP_CHAR * (3 + self.previous_target_count))

        self.previous_target_count = len(self.targets)

        # Overwrite the current line
        Color.p('\r')

        # First row: columns
        Color.p('   NUM')
        Color.p('                      ESSID')
        if Configuration.show_bssids:
            Color.p('              BSSID')
        Color.pl('   CH  ENCR  POWER  WPS?  CLIENT')

        # Second row: separator
        Color.p('   ---')
        Color.p('  -------------------------')
        if Configuration.show_bssids:
            Color.p('  -----------------')
        Color.pl('  ---  ----  -----  ----  ------')

        # Remaining rows: targets
        for idx, target in enumerate(self.targets, start=1):
            Color.clear_entire_line()
            Color.p('   {G}%s  ' % str(idx).rjust(3))
            Color.pl(target.to_str(Configuration.show_bssids))

    @staticmethod
    def get_terminal_height():
        import os
        (rows, columns) = os.popen('stty size', 'r').read().split()
        return int(rows)

    @staticmethod
    def get_terminal_width():
        import os
        (rows, columns) = os.popen('stty size', 'r').read().split()
        return int(columns)

    def select_targets(self):
        ''' Asks user to select target(s) '''

        if len(self.targets) == 0:
            if self.err_msg is not None:
                Color.pl(self.err_msg)

            # TODO Print a more-helpful reason for failure.
            # 1. Link to wireless drivers wiki,
            # 2. How to check if your device supporst monitor mode,
            # 3. Provide airodump-ng command being executed.
            raise Exception("No targets found."
                + " You may need to wait longer,"
                + " or you may have issues with your wifi card")

        if Configuration.scan_time > 0:
            return self.targets

        self.print_targets()
        Color.clear_entire_line()

        if self.err_msg is not None:
            Color.pl(self.err_msg)

        input_str  = '{+} select target(s)'
        input_str += ' ({G}1-%d{W})' % len(self.targets)
        input_str += ' separated by commas, dashes'
        input_str += ' or {G}all{W}: '

        chosen_targets = []
    
        for choice in raw_input(Color.s(input_str)).split(','):
            choice = choice.strip()
            if choice.lower() == 'all':
                chosen_targets = self.targets
                break
            if '-' in choice:
                # User selected a range
                (lower,upper) = [int(x) - 1 for x in choice.split('-')]
                for i in xrange(lower, min(len(self.targets), upper + 1)):
                    chosen_targets.append(self.targets[i])
            elif choice.isdigit():
                choice = int(choice) - 1
                chosen_targets.append(self.targets[choice])
            else:
                pass
        return chosen_targets

if __name__ == '__main__':
    # Example displays targets and selects the appropriate one
    Configuration.initialize()
    try:
        s = Scanner()
        targets = s.select_targets()
    except Exception as e:
        Color.pl('\r {!} {R}Error{W}: %s' % str(e))
        Configuration.exit_gracefully(0)
    for t in targets:
        Color.pl("    {W}Selected: %s" % t)
    Configuration.exit_gracefully(0)

