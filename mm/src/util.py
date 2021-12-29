import subprocess
from pathlib import Path
import log

SDK_PATH = ''

tool_set = {
    'swift-build': 'usr/bin/swift-build',
    'swift-package': 'usr/bin/swift-package',
    'swift-test': 'usr/bin/swift-test',
    'objcopy': 'usr/bin/arm-none-eabi-objcopy'
}

def quote_string(path):
    return '"%s"' % str(path)


def set_sdk_path(path):
    global SDK_PATH

    if not path.is_dir():
        log.die(path + "doesn't exists")
    SDK_PATH = path

def get_sdk_path():
    return SDK_PATH

def get_bin_path():
    return SDK_PATH / 'usr/bin'

def get_tool(tool):
    pos = tool_set.get(tool)
    path = Path(SDK_PATH / pos)

    if not path.is_file():
        log.die('cannot find ' + quote_string(path))

    return quote_string(path)


def command(flags):
    cmd = ''
    for item in flags:
        cmd += item + ' '

    if log.VERBOSE > log.VERBOSE_NORMAL:
        cmd += '-v'

    log.inf(cmd, level = log.VERBOSE_VERY)

    p = subprocess.Popen(cmd, shell=True)
    ret = p.wait()

    return ret


def run_command(flags):
    cmd = ''
    for item in flags:
        cmd += item + ' '

    #if log.VERBOSE > log.VERBOSE_NORMAL:
    #    cmd += '-v'

    log.inf(cmd, level=log.VERBOSE_VERY)

    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ret = p.wait()
    cmd_out, cmd_err = p.communicate()
    if ret:
        log.die(cmd_err.decode('utf-8'), prefix=False)
    
    return cmd_out.decode('utf-8')





