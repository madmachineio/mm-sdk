import os, subprocess
from pathlib import Path
import log, version
import re


SDK_ENV = ''
SDK_PATH = ''

SWIFT_PATH = ''

SDK_ID = 'madmachine-sdk'
ARTIFACT_PATH = SDK_ID + '-' + str(version.__VERSION__) + '.artifactbundle'


sdk_tool_set = {
    'ld': 'usr/bin/arm-none-eabi-ld',
    'objcopy': 'usr/bin/arm-none-eabi-objcopy',
    'serial-loader': 'boards/SerialLoader.bin'
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
        log.die(str(swift_path) + " doesn't exist")

    if not tool_path.is_dir():
        log.die(str(tool_path) + " doesn't exist")

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
    subpath = swift_tool_set.get(tool)
    if subpath is not None:
        tool_path = Path(SWIFT_PATH / subpath)
    else:
        subpath = sdk_tool_set.get(tool)
        tool_path = Path(SDK_PATH / subpath)

    if not tool_path.is_file():
        log.die('cannot find ' + str(tool_path))

    return tool_path

def get_tool(tool):
    return quote_string(get_tool_path(tool))


def check_swift_version(prefix, path, minimum):
    swiftc = Path(path / 'usr/bin/swiftc')
    if not swiftc.is_file():
        return False

    cmd = quote_string(swiftc) + ' -v'

    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ret = p.wait()
    cmd_out, cmd_err = p.communicate()

    if ret:
        return False

    if cmd_err:
        ret = cmd_err.decode('utf-8').rstrip()

    match = re.search(r'\b\d+(\.\d+)+\b', ret)
    if match:
        version = match.group()
        check_ret = is_newer(version, minimum)
        if check_ret:
            log.inf(prefix + ' Swift toolchain: ' + version, prefix=False, level=log.VERBOSE_DBG)
            return check_ret

    return False


def is_newer(version, target):
    def normalize_version(v, length=3):
        parts = list(map(int, v.split(".")))
        while len(parts) < length:
            parts.append(0)
        return tuple(parts)
    return normalize_version(version) >= normalize_version(target)

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

    log.inf(cmd, prefix=False, level=log.VERBOSE_DBG)

    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=SDK_ENV)
    ret = p.wait()
    cmd_out, cmd_err = p.communicate()

    if ret:
        log.die(cmd_err.decode('utf-8'), prefix=False)
    

    if cmd_err:
        log.inf(cmd_err.decode('utf-8'), prefix=False, level=log.VERBOSE_DBG)
        return cmd_err.decode('utf-8')

    log.inf(cmd_out.decode('utf-8'), prefix=False, level=log.VERBOSE_DBG)
    return cmd_out.decode('utf-8')