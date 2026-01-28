import os, platform, subprocess
from pathlib import Path
import log, version
import re


SDK_ENV = None
SDK_PATH = None

SWIFT_PATH = None
SWIFT_VERSION_MAJOR_MINOR = None
SWIFT_VERSION_FULL = None
#MACOS_SWIFT_PATH = Path('/Library/Developer/Toolchains/swift-latest.xctoolchain')

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

def init_sdk_and_swift_path(sdk_path, swift_path=None, needSwiftToolchain=True):
    global SDK_PATH
    global SWIFT_PATH
    global SDK_ENV

    if not sdk_path.is_dir():
        log.die(str(sdk_path) + " doesn't exist")
    SDK_PATH = sdk_path
    SDK_ENV = os.environ.copy()

    log.dbg('Set mm-sdk path to: ' + str(SDK_PATH))

    # Try to find Swift toolchain:
    # 1. from main command parameter '--toolchain'
    # 2. from environment variable 'TOOLCHAIN'
    if needSwiftToolchain and swift_path is None:
        try: 
            swift_path = Path(SDK_ENV['TOOLCHAIN']).resolve()
            if swift_path.is_dir():
                log.dbg('Using Swift toolchain from environment variable TOOLCHAIN: ' + str(swift_path))
            else:
                swift_path = None
        except KeyError: 
            swift_path = None

    # 3. from command 'swiftly use --print-location'
    if swift_path is None:
        swift_path = find_default_swift_path()
        if swift_path is not None:
            log.dbg('Using default Swift toolchain at: ' + str(swift_path))
    SWIFT_PATH = swift_path

    if needSwiftToolchain:
        if SWIFT_PATH is None:
            log.die('Cannot find a Swift toolchain, please install Swift toolchain for your platform')
        elif not check_swift_version(MINIMUM_SWIFT_VERSION):
            log.die('The current Swift toolchain version is too old, please update to at least ' + MINIMUM_SWIFT_VERSION)
 
def get_sdk_path():
    return SDK_PATH

def get_swift_path():
    return SWIFT_PATH

def get_swift_version_major_minor():
    return SWIFT_VERSION_MAJOR_MINOR

def get_swift_version_full():
    return SWIFT_VERSION_FULL

def get_swift_module_version():
    # Some patch releases can break binary module compatibility.
    overrides = {
        '6.2.3': '6.2.3'
    }
    if SWIFT_VERSION_FULL in overrides:
        return overrides[SWIFT_VERSION_FULL]
    return SWIFT_VERSION_MAJOR_MINOR

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

    if system == 'Windows':
        flags = ['(Get-Command swiftc).Source']
    else:
        flags = ['swiftly', 'use', '--print-location']

    log.dbg('Trying to find Swift toolchain with command: ' + ' '.join(flags))
    ret = run_command(flags).strip()
    if ret:
        # Keep only the first line in case the tool prints update notices.
        ret = ret.splitlines()[0].strip()

    if ret is None or ret == '':
        ret = None
    else:
        ret = Path(ret)
        ret = ret.resolve()

    log.dbg('Found Swift toolchain at: ' + str(ret))
    return ret

def check_swift_version(minimum):
    global SWIFT_VERSION_MAJOR_MINOR
    global SWIFT_VERSION_FULL

    swiftc = get_tool_string('swiftc')
    cmd = swiftc + ' -v'

    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ret = p.wait()
    cmd_out, cmd_err = p.communicate()

    if ret:
        return False

    if cmd_err:
        ret = cmd_err.decode('utf-8').rstrip()

    #match = re.search(r'\b\d+(\.\d+)+\b', ret)
    match = re.search(r'\b(?P<major>\d+)\.(?P<minor>\d+)(?:\.(?P<patch>\d+))?\b', ret)
    if match:
        full_version = match.group(0)
        check_ret = is_newer(full_version, minimum)
        if check_ret:
            SWIFT_VERSION_FULL = full_version
            SWIFT_VERSION_MAJOR_MINOR = f"{match.group('major')}.{match.group('minor')}"
            log.dbg('Swift toolchain version ' + full_version)
            log.dbg('Swift toolchain version without patch ' + SWIFT_VERSION_MAJOR_MINOR)
            return True
        else:
            log.wrn('Swift toolchain version ' + full_version + ' is older than required minimum version ' + minimum)

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
        log.dbg('Command failed: ' + cmd)

    cmd_out_text = cmd_out.decode('utf-8') if cmd_out else ''
    cmd_err_text = cmd_err.decode('utf-8') if cmd_err else ''

    if cmd_err_text:
        log.wrn(cmd_err_text)
    if cmd_out_text:
        log.inf(cmd_out_text, level=log.VERBOSE_DBG)
        return cmd_out_text
    
    return cmd_err_text
