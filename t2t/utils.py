# coding=UTF8

# tune2tube.py
#
# Copyright (C) 2014-2015 Michiel Sikma and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
# or implied. See the License for the specific language governing
# permissions and limitations under the License.


def bytes_to_human(n, bformat='%(value).1f %(symbol)s', symbols='customary'):
    '''
    Convert n bytes into a human readable string based on format.
    symbols can be either "customary", "customary_ext", "iec" or "iec_ext".

    Recipe by Giampaolo Rodola <g.rodola[AT]gmail[DOT]com>, slightly modified.
    Found on <http://goo.gl/Ldo93T>, MIT license.
    '''
    vocab = {
        'customary': ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB'),
        'customary_ext': ('byte', 'kilo', 'mega', 'giga', 'tera', 'peta'),
        'iec': ('Bi', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi'),
        'iec_ext': ('byte', 'kibi', 'mebi', 'gibi', 'tebi', 'pebi'),
    }
    n = int(n)
    if n < 0:
        raise ValueError("n < 0")
    symbols = vocab[symbols]
    prefix = {}
    for i, s in enumerate(symbols[1:]):
        prefix[s] = 1 << (i + 1) * 10
    for symbol in reversed(symbols[1:]):
        if n >= prefix[symbol]:
            value = float(n) / prefix[symbol]
            return bformat % locals()
    return bformat % dict(symbol=symbols[0], value=n)


def error_exit(str='unknown error'):
    '''
    Exits the program with an error message.
    '''
    print('tune2tube.py: error: %(str)s' % {'str': str})
    exit()
