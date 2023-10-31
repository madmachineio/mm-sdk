import os, subprocess
from pathlib import Path
import log



SDK_ENV = ''
SDK_PATH = ''

tool_set = {
    'swift-build': 'usr/bin/swift-build',
    'swift-package': 'usr/bin/swift-package',
    'swift-test': 'usr/bin/swift-test',
    'objcopy': 'usr/bin/arm-none-eabi-objcopy',
    'llvm-cov': 'usr/bin/llvm-cov',
    'serial-loader': 'Boards/SerialLoader.bin'
}

def quote_string(path):
    return '"%s"' % str(path)


def set_sdk_path(path):
    global SDK_ENV
    global SDK_PATH

    if not path.is_dir():
        log.die(path + "doesn't exists")

    SDK_PATH = path
    SDK_ENV = os.environ.copy()
    SDK_ENV['MM_SDK_PATH'] = str(path)

def get_sdk_path():
    return SDK_PATH

def get_bin_path():
    return SDK_PATH / 'usr/bin'

def get_tool_path(tool):
    pos = tool_set.get(tool)
    path = Path(SDK_PATH / pos)

    if not path.is_file():
        log.die('cannot find ' + str(path))

    return path

def get_tool(tool):
    return quote_string(get_tool_path(tool))


def command(flags):
    cmd = ''
    for item in flags:
        cmd += item + ' '

    if log.VERBOSE > log.VERBOSE_INF:
        cmd += '-v'

    log.inf(cmd, prefix=False, level=log.VERBOSE_DBG)

    p = subprocess.Popen(cmd, shell=True, env=SDK_ENV)
    ret = p.wait()

    return ret


def run_command(flags):
    cmd = ''
    for item in flags:
        cmd += item + ' '

    #if log.VERBOSE > log.VERBOSE_INF:
    #    cmd += '-v'

    log.inf(cmd, prefix=False, level=log.VERBOSE_DBG)

    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=SDK_ENV)
    ret = p.wait()
    cmd_out, cmd_err = p.communicate()
    if ret:
        log.die(cmd_err.decode('utf-8'), prefix=False)
    
    log.inf(cmd_out.decode('utf-8'), prefix=False, level=log.VERBOSE_DBG)
    return cmd_out.decode('utf-8')





