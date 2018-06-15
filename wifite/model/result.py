#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..util.color import Color

import os
import time
from json import loads, dumps

class CrackResult(object):
    ''' Abstract class containing results from a crack session '''

    # File to save cracks to, in PWD
    cracked_file = "cracked.txt"

    def __init__(self):
        self.date = int(time.time())

    def dump(self):
        raise Exception("Unimplemented method: dump()")

    def to_dict(self):
        raise Exception("Unimplemented method: to_dict()")

    def save(self):
        ''' Adds this crack result to the cracked file and saves it. '''
        name = CrackResult.cracked_file
        json = []
        if os.path.exists(name):
            with open(name, 'r') as fid:
                text = fid.read()
            try:
                json = loads(text)
            except Exception as e:
                Color.pl('{!} error while loading %s: %s' % (name, str(e)))
        json.append(self.to_dict())
        with open(name, 'w') as fid:
            fid.write(dumps(json, indent=2))
        Color.pl('{+} saved crack result to {C}%s{W} ({G}%d total{W})'
            % (name, len(json)))

    @classmethod
    def load_all(cls):
        if not os.path.exists(cls.cracked_file): return []
        with open(cls.cracked_file, "r") as json_file:
            json = loads(json_file.read())
        return json

    @staticmethod
    def load(json):
        ''' Returns an instance of the appropriate object given a json instance '''
        if json['type'] == 'WPA':
            from .wpa_result import CrackResultWPA
            result = CrackResultWPA(json['bssid'],
                                    json['essid'],
                                    json['handshake_file'],
                                    json['key'])
        elif json['type'] == 'WEP':
            from .wep_result import CrackResultWEP
            result = CrackResultWEP(json['bssid'],
                                    json['essid'],
                                    json['hex_key'],
                                    json['ascii_key'])

        elif json['type'] == 'WPS':
            from .wps_result import CrackResultWPS
            result = CrackResultWPS(json['bssid'],
                                    json['essid'],
                                    json['pin'],
                                    json['psk'])
        result.date = json['date']
        return result

if __name__ == '__main__':
    # Deserialize WPA object
    Color.pl('\nCracked WPA:')
    json = loads('{"bssid": "AA:BB:CC:DD:EE:FF", "essid": "Test Router", "key": "Key", "date": 1433402428, "handshake_file": "hs/capfile.cap", "type": "WPA"}')
    obj = CrackResult.load(json)
    obj.dump()

    # Deserialize WEP object
    Color.pl('\nCracked WEP:')
    json = loads('{"bssid": "AA:BB:CC:DD:EE:FF", "hex_key": "00:01:02:03:04", "ascii_key": "abcde", "essid": "Test Router", "date": 1433402915, "type": "WEP"}')
    obj = CrackResult.load(json)
    obj.dump()

    # Deserialize WPS object
    Color.pl('\nCracked WPS:')
    json = loads('{"psk": "the psk", "bssid": "AA:BB:CC:DD:EE:FF", "pin": "01234567", "essid": "Test Router", "date": 1433403278, "type": "WPS"}')
    obj = CrackResult.load(json)
    obj.dump()
