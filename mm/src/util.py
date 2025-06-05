import os, platform, subprocess
from pathlib import Path
import log, version
import re


SDK_ENV = ''
SDK_PATH = ''

SWIFT_PATH = ''
MACOS_SWIFT_PATH = Path('/Library/Developer/Toolchains/swift-latest.xctoolchain')

SDK_ID = 'madmachine-sdk'
MINIMUM_SWIFT_VERSION = '6.1.0'
ARTIFACT_PATH = SDK_ID + '-' + str(version.__VERSION__) + '.artifactbundle'

swift_tool_set = {
    'swiftc': 'usr/bin/swiftc',
    'swift-build': 'usr/bin/swift-build',
    'swift-package': 'usr/bin/swift-package',
    'swift-test': 'usr/bin/swift-test',
    'llvm-cov': 'usr/bin/llvm-cov'
}

gcc_tool_set = {
    'ld': 'usr/bin/arm-none-eabi-ld',
    'objcopy': 'usr/bin/arm-none-eabi-objcopy'
}

sdk_tool_set = {
    'serial-loader': 'boards/SerialLoader.bin'
}




def quote_string(path):
    return '"%s"' % str(path)


# def set_sdk_path(swift_path, sdk_path, save=False, env_name=None):
#     global SDK_ENV
#     global SDK_PATH
#     global SWIFT_PATH

#     if not swift_path.is_dir():
#         log.die(str(swift_path) + " doesn't exist")

#     if not sdk_path.is_dir():
#         log.die(str(sdk_path) + " doesn't exist")

#     SWIFT_PATH = swift_path

#     SDK_PATH = sdk_path
#     SDK_ENV = os.environ.copy()

#     if save and env_name is not None:
#         SDK_ENV[env_name] = str(sdk_path)

def init_sdk_and_swift_path(sdk_path, swift_path=None, save=False, env_name=None):
    global SDK_PATH
    global SWIFT_PATH
    global SDK_ENV

    if not sdk_path.is_dir():
        log.die(str(sdk_path) + " doesn't exist")
    SDK_PATH = sdk_path

    SDK_ENV = os.environ.copy()
    if save and env_name is not None:
        SDK_ENV[env_name] = str(sdk_path)

    if swift_path is None:
        swift_path = find_default_swift_path()
    SWIFT_PATH = swift_path

def get_sdk_path():
    return SDK_PATH

def get_swift_path():
    return SWIFT_PATH

def get_tool_path(tool):
    subpath = swift_tool_set.get(tool)
    if subpath is not None:
        if platform.system() == 'Windows':
            subpath += '.exe'
        tool_path = Path(SWIFT_PATH / subpath)
        if not tool_path.is_file():
            log.die('cannot find ' + str(tool_path))
        return tool_path

    subpath = gcc_tool_set.get(tool)
    if subpath is not None:
        if platform.system() == 'Windows':
            subpath += '.exe'
        tool_path = Path(SDK_PATH / subpath)
        if not tool_path.is_file():
            log.die('cannot find ' + str(tool_path))
        return tool_path

    subpath = sdk_tool_set.get(tool)
    if subpath is not None:
        tool_path = Path(SDK_PATH / subpath)
        if not tool_path.is_file():
            log.die('cannot find ' + str(tool_path))
        return tool_path

    log.die('unknown tool: ' + tool)

def get_tool_string(tool):
    return quote_string(get_tool_path(tool))
    
def find_default_swift_path():
    system = platform.system()
    if system == 'Darwin':
        log.wrn('Default Swift toolchain with XCode cannot be used for Embedded development cause it comes without the required libraries')
        log.wrn('Trying to find the toolchain at: ' + str(MACOS_SWIFT_PATH))
        if MACOS_SWIFT_PATH.is_dir():
            return MACOS_SWIFT_PATH
        else:
            log.die('Cannot find Swift toolchain at: ' + str(MACOS_SWIFT_PATH))
    elif system == 'Linux':
        flags = ['which', 'swiftc']
    elif system == 'Windows':
        log.inf('Trying to find Swift toolchain in Windows environment')
        flags = ['(Get-Command swiftc).Source']
    else:
        log.die('Unsupported platform: ' + system)

    ret = run_command(flags)

    ret = Path(ret) / '../../..'
    ret = ret.resolve()
    log.inf('Found default toolchain path at: ' + str(ret))

    return ret

def check_swift_version(minimum):
    swiftc = get_tool_string('swiftc')
    cmd = swiftc + ' -v'

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
            log.inf('Using Swift toolchain: ' + version, level=log.VERBOSE_DBG)
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
    if platform.system() == 'Windows':
        cmd = 'powershell.exe -Command '
    else:
        cmd = ''

    for item in flags:
        cmd += item + ' '

    if log.VERBOSE > log.VERBOSE_INF:
        cmd += '-v'

    log.inf(cmd, level=log.VERBOSE_DBG)

    p = subprocess.Popen(cmd, shell=True, env=SDK_ENV)
    ret = p.wait()

    return ret


def run_command(flags):
    if platform.system() == 'Windows':
        cmd = 'powershell.exe -Command '
    else:
        cmd = ''

    for item in flags:
        cmd += item + ' '

    log.inf(cmd, level=log.VERBOSE_DBG)

    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=SDK_ENV)
    ret = p.wait()
    cmd_out, cmd_err = p.communicate()

    if ret:
        log.die(cmd_err.decode('utf-8'))
    
    if cmd_err:
        log.wrn(cmd_err.decode('utf-8'))
        return cmd_err.decode('utf-8')

    log.inf(cmd_out.decode('utf-8'), level=log.VERBOSE_DBG)
    return cmd_out.decode('utf-8')