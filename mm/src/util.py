import os, subprocess
from pathlib import Path
import log



SDK_ENV = ''
SDK_PATH = ''

SWIFT_PATH = ''

sdk_tool_set = {
    'ld': 'usr/bin/arm-none-eabi-ld',
    'objcopy': 'usr/bin/arm-none-eabi-objcopy',
    'serial-loader': 'Boards/SerialLoader.bin'
}

swift_tool_set = {
    'swift-build': 'usr/bin/swift-build',
    'swift-package': 'usr/bin/swift-package',
    'swift-test': 'usr/bin/swift-test',
    'llvm-cov': 'usr/bin/llvm-cov'
}

def quote_string(path):
    return '"%s"' % str(path)


def set_sdk_path(swift_path, tool_path, save=False, env_name=None):
    global SDK_ENV
    global SDK_PATH
    global SWIFT_PATH

    if not swift_path.is_dir():
        log.die(tool_path + "doesn't exists")

    if not tool_path.is_dir():
        log.die(tool_path + "doesn't exists")

    SWIFT_PATH = swift_path

    SDK_PATH = tool_path
    SDK_ENV = os.environ.copy()

    if save and env_name is not None:
        SDK_ENV[env_name] = str(tool_path)


def get_sdk_path():
    return SDK_PATH

def get_swift_path():
    return SWIFT_PATH

def get_tool_path(tool):
    pos = swift_tool_set.get(tool)
    if pos is not None:
        path = Path(SWIFT_PATH / pos)
    else:
        pos = sdk_tool_set.get(tool)
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





