# coding=utf-8
#
# Copyright (C) 2019 Martin Owens
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110, USA.
#
"""
This API provides methods for calling Inkscape to execute a given
Inkscape command. This may be needed for various compiling options
(e.g., png), running other extensions or performing other options only
available via the shell API.

Best practice is to avoid using this API except when absolutely necessary,
since it is resource-intensive to invoke a new Inkscape instance.

However, in any circumstance when it is necessary to call Inkscape, it
is strongly recommended that you do so through this API, rather than calling
it yourself, to take advantage of the security settings and testing functions.

"""

import os
import sys

from subprocess import Popen, PIPE
from tempfile import TemporaryDirectory
from lxml.etree import ElementTree

from .elements import SvgDocumentElement

INKSCAPE_EXECUTABLE_NAME = os.environ.get('INKSCAPE_COMMAND')
if INKSCAPE_EXECUTABLE_NAME == None:
    if sys.platform == 'win32':
        # prefer inkscape.exe over inkscape.com which spawns a command window
        INKSCAPE_EXECUTABLE_NAME = 'inkscape.exe'
    else:
        INKSCAPE_EXECUTABLE_NAME = 'inkscape'

class CommandNotFound(IOError):
    """Command is not found"""
    pass

class ProgramRunError(ValueError):
    """Command returned non-zero output"""
    pass

def which(program):
    """
    Attempt different methods of trying to find if the program exists.
    """
    if os.path.isabs(program) and os.path.isfile(program):
        return program

    # This code can be simplified using shutil.which in Python3. However, on Windows, 
    # shutil.which("pdflatex") returns ".\pdflatex.py", i.e. the path to the extension,
    # probably because Windows doesn't have the concept of an execute flag. In order to not break
    # the extension on Windows, the change e8bbec5f was partially reverted.
    try:
        # Python2 and python3, but must have distutils and may not always
        # work on windows versions (depending on the version)
        from distutils.spawn import find_executable
        prog = find_executable(program)
        if prog:
            return prog
    except ImportError:
        pass

    try:
        # Python3 only version of which
        from shutil import which as warlock
        prog = warlock(program)
        if prog:
            return prog
    except ImportError:
        pass # python2


    # There may be other methods for doing a `which` command for other
    # operating systems; These should go here as they are discovered.

    raise CommandNotFound(f"Can not find the command: '{program}'")

def write_svg(svg, *filename):
    """Writes an svg to the given filename"""
    filename = os.path.join(*filename)
    if os.path.isfile(filename):
        return filename
    with open(filename, 'wb') as fhl:
        if isinstance(svg, SvgDocumentElement):
            svg = ElementTree(svg)
        if hasattr(svg, 'write'):
            # XML document
            svg.write(fhl)
        elif isinstance(svg, bytes):
            fhl.write(svg)
        else:
            raise ValueError("Not sure what type of SVG data this is.")
    return filename


def to_arg(arg, oldie=False):
    """Convert a python argument to a command line argument"""
    if isinstance(arg, (tuple, list)):
        (arg, val) = arg
        arg = '-' + arg
        if len(arg) > 2 and not oldie:
            arg = '-' + arg
        if val is True:
            return arg
        if val is False:
            return None
        return f"{arg}={str(val)}"
    return str(arg)

def to_args(prog, *positionals, **arguments):
    """Compile arguments and keyword arguments into a list of strings which Popen will understand.

    :param prog:
        Program executable prepended to the output.
    :type first: ``str``

    :Arguments:
        * (``str``) -- String added as given
        * (``tuple``) -- Ordered version of Kwyward Arguments, see below

    :Keyword Arguments:
        * *name* (``str``) --
          Becomes ``--name="val"``
        * *name* (``bool``) --
          Becomes ``--name``
        * *name* (``list``) --
          Becomes ``--name="val1"`` ...
        * *n* (``str``) --
          Becomes ``-n=val``
        * *n* (``bool``) --
          Becomes ``-n``

    :return: Returns a list of compiled arguments ready for Popen.
    :rtype: ``list[str]``
    """
    args = [prog]
    oldie = arguments.pop('oldie', False)
    for arg, value in arguments.items():
        arg = arg.replace('_', '-').strip()

        if isinstance(value, tuple):
            value = list(value)
        elif not isinstance(value, list):
            value = [value]

        for val in value:
            args.append(to_arg((arg, val), oldie))

    args += [to_arg(pos, oldie) for pos in positionals if pos is not None]
    # Filter out empty non-arguments
    return [arg for arg in args if arg is not None]

def _call(program, *args, **kwargs):
    stdin = kwargs.pop('stdin', None)
    if isinstance(stdin, str):
        stdin = stdin.encode('utf-8')
    inpipe = PIPE if stdin else None

    args = to_args(which(program), *args, **kwargs)
    process = Popen(
        args,
        shell=False, # Never have shell=True
        stdin=inpipe, # StdIn not used (yet)
        stdout=PIPE, # Grab any output (return it)
        stderr=PIPE, # Take all errors, just incase
    )
    (stdout, stderr) = process.communicate(input=stdin)
    if process.returncode == 0:
        return stdout
    raise ProgramRunError(f"Return Code: {process.returncode}: {stderr}\n{stdout}\nargs: {args}")

def call(program, *args, **kwargs):
    """
    Generic caller to open any program and return its stdout.

    stdout = call('executable', arg1, arg2, dash_dash_arg='foo', d=True, ...)

    Will raise ProgramRunError() if return code is not 0.

     * return_binary - Should stdout return raw bytes (default: False)
     * stdin - The string or bytes containing the stdin (default: None)
     * All other arguments converted using to_args(...) function.
    """
    # We use this long input because it's less likely to conflict with --binary=
    binary = kwargs.pop('return_binary', False)
    stdout = _call(program, *args, **kwargs)
    # Convert binary to string when we wish to have strings we do this here
    # so the mock tests will also run the conversion (always returns bytes)
    if not binary and isinstance(stdout, bytes):
        return stdout.decode(sys.stdout.encoding or 'utf-8')
    return stdout

def inkscape(svg_file, *args, **kwargs):
    """
    Call Inkscape with the given svg_file and the given arguments, see call()
    """
    return call(INKSCAPE_EXECUTABLE_NAME, svg_file, *args, **kwargs)

def inkscape_command(svg, select=None, verbs=()):
    """
    Executes a list of commands, a mixture of verbs, selects etc.

    inkscape_command('<svg...>', ('verb', 'VerbName'), ...)
    """
    with TemporaryDirectory(prefix='inkscape-command') as tmpdir:
        svg_file = write_svg(svg, tmpdir, 'input.svg')
        select = ('select', select) if select else None
        verbs += ('FileSave', 'FileQuit')
        inkscape(svg_file, select, batch_process=True, verb=';'.join(verbs))
        with open(svg_file, 'rb') as fhl:
            return fhl.read()

def take_snapshot(svg, dirname, name='snapshot', ext='png', dpi=96, **kwargs):
    """
    Take a snapshot of the given svg file.

    Resulting filename is yielded back, after generator finishes, the
    file is deleted so you must deal with the file inside the for loop.
    """
    svg_file = write_svg(svg, dirname, name + '.svg')
    ext_file = os.path.join(dirname, name + '.' + str(ext).lower())
    inkscape(svg_file, export_dpi=dpi, export_filename=ext_file, export_type=ext, **kwargs)
    return ext_file


def is_inkscape_available():
    """Return true if the Inkscape executable is available."""
    try:
        return bool(which(INKSCAPE_EXECUTABLE_NAME))
    except CommandNotFound:
        return False
