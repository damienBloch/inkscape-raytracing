# coding=utf-8
#
# Copyright (C) 2010 Nick Drobchenko, nick@cnc-club.ru
# Copyright (C) 2005 Aaron Spike, aaron@ekips.org
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
"""
Basic common utility functions for calculated things
"""
import os
import sys
import random
import re
import math

from itertools import tee
from argparse import ArgumentTypeError

# All the names that get added to the inkex API itself.
__all__ = ('AbortExtension', 'DependencyError', 'Boolean', 'errormsg')

ABORT_STATUS = -5

(X, Y) = range(2)
PY3 = sys.version_info[0] == 3

# Taken from https://www.w3.org/Graphics/SVG/1.1/paths.html#PathDataBNF
DIGIT_REX_PART = r'[0-9]'
DIGIT_SEQUENCE_REX_PART = fr'(?:{DIGIT_REX_PART}+)'
INTEGER_CONSTANT_REX_PART = DIGIT_SEQUENCE_REX_PART
SIGN_REX_PART = r'[+-]'
EXPONENT_REX_PART = fr'(?:[eE]{SIGN_REX_PART}?{DIGIT_SEQUENCE_REX_PART})'
FRACTIONAL_CONSTANT_REX_PART = fr'(?:{DIGIT_SEQUENCE_REX_PART}?\.{DIGIT_SEQUENCE_REX_PART}|{DIGIT_SEQUENCE_REX_PART}\.)'
FLOATING_POINT_CONSTANT_REX_PART = fr'(?:{FRACTIONAL_CONSTANT_REX_PART}{EXPONENT_REX_PART}?|{DIGIT_SEQUENCE_REX_PART}{EXPONENT_REX_PART})'
NUMBER_REX = re.compile(fr'(?:{SIGN_REX_PART}?{FLOATING_POINT_CONSTANT_REX_PART}|{SIGN_REX_PART}?{INTEGER_CONSTANT_REX_PART})')

def _pythonpath():
    for pth in os.environ.get('PYTHONPATH', '').split(':'):
        if os.path.isdir(pth):
            yield pth

def get_user_directory():
    """Return the user directory where extensions are stored."""
    if 'INKSCAPE_PROFILE_DIR' in os.environ:
        return os.path.abspath(
            os.path.expanduser(
                os.path.join(os.environ['INKSCAPE_PROFILE_DIR'], 'extensions')))

    home = os.path.expanduser("~")
    for pth in _pythonpath():
        if pth.startswith(home):
            return pth

def get_inkscape_directory():
    """Return the system directory where inkscape's core is."""
    for pth in _pythonpath():
        if os.path.isdir(os.path.join(pth, 'inkex')):
            return pth


class KeyDict(dict):
    """
    A normal dictionary, except asking for anything not in the dictionary
    always returns the key itself. This is used for translation dictionaries.
    """
    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            return key


def Boolean(value):
    """ArgParser function to turn a boolean string into a python boolean"""
    if value.upper() == 'TRUE':
        return True
    elif value.upper() == 'FALSE':
        return False
    return None

def to_bytes(content):
    """Ensures the content is bytes"""
    if isinstance(content, bytes):
        return content
    return str(content).encode("utf8")

def debug(what):
    """Print debug message if debugging is switched on"""
    errormsg(what)
    return what

def do_nothing(*args, **kwargs): # pylint: disable=unused-argument
    """A blank function to do nothing"""
    pass

def errormsg(msg):
    """Intended for end-user-visible error messages.

       (Currently just writes to stderr with an appended newline, but could do
       something better in future: e.g. could add markup to distinguish error
       messages from status messages or debugging output.)

       Note that this should always be combined with translation:

         import inkex
         ...
         inkex.errormsg(_("This extension requires two selected paths."))
    """
    try:
        sys.stderr.write(msg)
    except TypeError:
        sys.stderr.write(str(msg))
    except UnicodeEncodeError:
        # Python 2:
        # Fallback for cases where sys.stderr.encoding is not Unicode.
        # Python 3:
        # This will not work as write() does not accept byte strings, but AFAIK
        # we should never reach this point as the default error handler is
        # 'backslashreplace'.

        # This will be None by default if stderr is piped, so use ASCII as a
        # last resort.
        encoding = sys.stderr.encoding or 'ascii'
        sys.stderr.write(msg.encode(encoding, 'backslashreplace'))

    # Write '\n' separately to avoid dealing with different string types.
    sys.stderr.write('\n')


class AbortExtension(Exception):
    """Raised to print a message to the user without backtrace"""

    def __init__(self, message=""):
        self.message = message

    def write(self):
        """write the error message out to the user"""
        errormsg(self.message)


class DependencyError(NotImplementedError):
    """Raised when we need an external python module that isn't available"""

class FragmentError(Exception):
    """Raised when trying to do rooty things on an xml fragment"""

def to(kind):  # pylint: disable=invalid-name
    """
    Decorator which will turn a generator into a list, tuple or other object type.
    """

    def _inner(call):
        def _outer(*args, **kw):
            return kind(call(*args, **kw))

        return _outer

    return _inner


def strargs(string, kind=float):
    """Returns a list of floats from a string with commas or space separators, 
        also splits at -(minus) signs by adding a space in front of the - sign
    """
    return [kind(val) for val in NUMBER_REX.findall(string)]


class classproperty:  # pylint: disable=invalid-name, too-few-public-methods
    """Combine classmethod and property decorators"""

    def __init__(self, func):
        self.func = func

    def __get__(self, obj, owner):
        return self.func(owner)


def filename_arg(name):
    """Existing file to read or option used in script arguments"""
    filename = os.path.abspath(os.path.expanduser(name))
    if not os.path.isfile(filename):
        raise ArgumentTypeError("File not found: {}".format(name))
    return filename

def pairwise(iterable, start=True):
    "Iterate over a list with overlapping pairs (see itertools recipes)"
    first, then = tee(iterable)
    starter = [(None, next(then, None))]
    if not start:
        starter = []
    return starter + list(zip(first, then))

EVAL_GLOBALS = {}
EVAL_GLOBALS.update(random.__dict__)
EVAL_GLOBALS.update(math.__dict__)

def math_eval(function, variable="x"):
    """Interpret a function string. All functions from math and random may be used.
    @returns a lambda expression if sucessful; otherwise None.
    """
    try:
        if function != "":
            return eval(f'lambda {variable}: ' + (function.strip('"') or 't'), EVAL_GLOBALS, {})
    # handle incomplete/invalid function gracefully
    except SyntaxError:
        pass
    return None

def is_number(string):
    """Checks if a value is a number"""
    try:
        float(string)
        return True
    except ValueError:
        return False