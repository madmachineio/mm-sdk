# Copyright 2018 Open Source Foundries Limited.
# Copyright 2019 Foundries.io Limited.
#
# SPDX-License-Identifier: Apache-2.0

'''Provides common methods for printing messages to display to the user.

WestCommand instances should generally use the functions in this
module rather than calling print() directly if possible, as these
respect the ``color.ui`` configuration option and verbosity level.
'''

import colorama
import sys
from typing import NoReturn

VERBOSE_NONE = 0
'''No messages printed.'''

VERBOSE_ERR = 1
'''error messages will be printed.'''

VERBOSE_WRN = 2
'''warning messages will be printed.'''

VERBOSE_INF = 3
'''info messages will be printed.'''

VERBOSE_DBG = 4
'''debug messages will be printed.'''




VERBOSE = VERBOSE_INF
'''Global verbosity level. VERBOSE_INF is the default.'''




#: Color used (when applicable) for printing with err() and die()
ERR_COLOR = colorama.Fore.LIGHTRED_EX
# ERR_COLOR = colorama.Fore.RED

#: Color used (when applicable) for printing with wrn()
# WRN_COLOR = colorama.Fore.LIGHTYELLOW_EX
WRN_COLOR = colorama.Fore.YELLOW

#: Color used (when applicable) for printing with inf()
INF_COLOR = colorama.Fore.LIGHTGREEN_EX
# INF_COLOR = colorama.Fore.GREEN

#: Color used (when applicable) for printing with dbg()
DBG_COLOR = colorama.Fore.LIGHTGREEN_EX
# DBG_COLOR = colorama.Fore.GREEN




def set_verbosity(value):
    '''Set the logging verbosity level.
    :param value: verbosity level to set, e.g. VERBOSE_INF.
    '''
    global VERBOSE
    VERBOSE = int(value)

def dbg(*args, colorize=True, prefix=True, level=VERBOSE_DBG):
    '''Print a verbose debug logging message.
    :param args: sequence of arguments to print.
    :param value: verbosity level to set, e.g. VERBOSE_DBG.
    The message is only printed if level is at least the current
    verbosity level.
    '''
    
    if level > VERBOSE:
        return

    if not _use_colors():
        colorize = False

    # This approach colorizes any sep= and end= text too, as expected.
    #
    # colorama automatically strips the ANSI escapes when stdout isn't a
    # terminal (by wrapping sys.stdout).
    if colorize:
        print(DBG_COLOR, end='')

    print('debug: ' if prefix else '', end='')
    print(*args)

    if colorize:
        _reset_colors(sys.stdout)
    

def inf(*args, colorize=False, prefix=False, level=VERBOSE_INF):
    '''Print an informational message.

    :param args: sequence of arguments to print.
    :param colorize: If this is True, the configuration option ``color.ui``
                     is undefined or true, and stdout is a terminal, then
                     the message is printed in green.
    '''

    if level > VERBOSE:
        return

    if not _use_colors():
        colorize = False

    # This approach colorizes any sep= and end= text too, as expected.
    #
    # colorama automatically strips the ANSI escapes when stdout isn't a
    # terminal (by wrapping sys.stdout).
    if colorize:
        print(INF_COLOR, end='')

    print('info: ' if prefix else '', end='')
    print(*args)

    if colorize:
        _reset_colors(sys.stdout)

def banner(*args):
    '''Prints args as a "banner" at inf() level.
    The args are prefixed with '=== ' and colorized by default.'''
    inf('===', *args, colorize=True, prefix=False)

def small_banner(*args):
    '''Prints args as a smaller banner(), i.e. prefixed with '-- ' and
    not colorized.'''
    inf('---', *args, colorize=False, prefix=False)

def wrn(*args, prefix=True, level=VERBOSE_WRN):
    '''Print a warning.
    :param args: sequence of arguments to print.
    The message is prefixed with the string ``"warning: "``.
    If the configuration option ``color.ui`` is undefined or true and
    stdout is a terminal, then the message is printed in yellow.'''

    if level > VERBOSE:
        return

    if _use_colors():
        print(WRN_COLOR, end='')

    print('warning: ' if prefix else '', end='')
    print(*args)

    if _use_colors():
        _reset_colors(sys.stdout)

def err(*args, prefix=True, level=VERBOSE_ERR):
    '''Print an error.

    This function does not abort the program. For that, use `die()`.

    :param args: sequence of arguments to print.
    :param prefix: if True, the the message is prefixed with "error: ";
                  otherwise, "" is used.

    If the configuration option ``color.ui`` is undefined or true and
    stdout is a terminal, then the message is printed in red.'''

    if _use_colors():
        print(ERR_COLOR, end='', file=sys.stderr)

    print('error: ' if prefix else '', end='', file=sys.stderr)
    print(*args, file=sys.stderr)

    if _use_colors():
        _reset_colors(sys.stderr)

def die(*args, prefix=True, exit_code=1) -> NoReturn:
    '''Print a fatal error, and abort the program.
    :param args: sequence of arguments to print.
    :param exit_code: return code the program should use when aborting.
    Equivalent to ``die(*args, fatal=True)``, followed by an attempt to
    abort with the given *exit_code*.'''
    err(*args, prefix=prefix)
    sys.exit(exit_code)

def msg(*args, color=None, stream=sys.stdout):
    '''Print a message using a color.
    :param args: sequence of arguments to print.
    :param color: color to print in (e.g. INF_COLOR), must be given
    :param stream: file to print to (default is stdout)
    If color.ui is disabled, the message will still be printed, but
    without color.
    '''
    if color is None:
        raise ValueError('no color was given')

    if _use_colors():
        print(color, end='', file=stream)

    print(*args, file=stream)

    if _use_colors():
        _reset_colors(stream)

def use_color():
    '''Returns True if the configuration requests colored output.'''
    return _use_colors(warn=False)

def _use_colors(warn=True):
    return True

def _reset_colors(file):
    # The flush=True avoids issues with unrelated output from commands (usually
    # Git) becoming colorized, due to the final attribute reset ANSI escape
    # getting line-buffered
    print(colorama.Style.RESET_ALL, end='', file=file, flush=True)