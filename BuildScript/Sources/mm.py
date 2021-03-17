  
#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import os, sys
import argparse
import json
import subprocess
from pathlib import Path
import struct
from zlib import crc32

gSdkPath = ''
gProjectPath = ''
gVerbose = False

def quoteStr(path):
    return '"%s"' % str(path)

def generateProjectFile(name, type):
    ret = sorted(Path('.').glob('*.mmp'))

    if ret:
        print('error: Project file ' + ret[0].name + ' already exists in this directory')
        os._exit(-1)
    
    Path('./' + name + '.mmp').touch(exist_ok = True)

def initProject(args):
    initType = args.type
    if args.name:
        name = args.name
    else:
        name = Path('.').resolve().name

    initFlags = [
        '--type ' + initType,
        '--name ' + name
    ]
    generateProjectFile(name, args.type)
    
    cmd = quoteStr(getSdkTool('swift-package')) + ' init'
    for item in initFlags:
        cmd += ' ' + item

    if gVerbose:
        print(cmd)
    p = subprocess.Popen(cmd, shell = True)
    p.wait()
    if p.poll():
        os._exit(-1)
    os._exit(0)

def getProjectName():
    ret = sorted(Path('.').glob('*.mmp'))

    if not ret:
        print('error: MadMachine project file not exists in this directory')
        os._exit(-1)
    
    if len(ret) > 1:
        print('error: More than one MadMachine project files exist in this directory')
        os._exit(-1)

    ret = ret[0].name
    name = ret.split('.')[0]

    return name

def getSdkTool(tool):
    value = ''
    if tool == 'swift-build':
        value = (gSdkPath / 'usr/bin/swift-build')
    elif tool == 'swift-package':
        value = (gSdkPath / 'usr/bin/swift-package')
    elif tool == 'objcopy':
        value = (gSdkPath / 'usr/bin/arm-none-eabi-objcopy')
    return value

def cleanBin(targetArch):
    files = sorted((gProjectPath / '.build' / targetArch / 'release').glob('*.bin'))
    for file in files:
        file.unlink()

def generateBin(projectName, targetArch):
    cmd = quoteStr(getSdkTool('objcopy'))

    flags = [
        '-S',
        '-Obinary',
        '--gap-fill',
        '0xFF',
        '-R',
        '.comment',
        '-R',
        'COMMON',
        '-R',
        '.eh_frame',
        quoteStr(gProjectPath / '.build' / targetArch / 'release' / projectName),
        quoteStr(gProjectPath / '.build' / targetArch / 'release' / (projectName + '.bin'))
    ]

    for item in flags:
        cmd += ' ' + item

    if gVerbose:
        print(cmd)
    p = subprocess.Popen(cmd, shell = True)
    p.wait()
    if p.poll():
        print('error: Generating binary failed!')
        os._exit(-1)

def addCrcToBin(boardName, projectName, targetArch):
    if boardName == 'SwiftIOFeather':
        targetFile = gProjectPath / '.build' / targetArch / 'release/feather.bin'
    elif boardName == 'SwiftIOBoard':
        targetFile = gProjectPath / '.build' / targetArch / 'release/swiftio.bin'

    data = (gProjectPath / '.build/release' / (projectName + '.bin')).read_bytes()
    value = crc32(data)
    mask = (1 << 8) - 1
    list_dec = [(value >> k) & mask for k in range(0, 32, 8)]

    with open(targetFile, 'wb') as file:
        file.write(data)
        for number in list_dec:
            byte = struct.pack('B', number)
            file.write(byte)

def getCArch(floatType):
    if floatType == 'hard':
        flags = [
            #'-target',
            #'thumbv7em-unknown-none-eabihf',
            '-mcpu=cortex-m7',
            '-mfloat-abi=hard'
        ]
    else:
        flags = [
            #'-target',
            #'thumbv7em-unknown-none-eabi',
            '-mcpu=cortex-m7+nofp',
            '-mfloat-abi=soft'
        ]
    return flags

def getCPredefined():
    flags = [
        '-nostdinc',
        '-D__MADMACHINE__',
        '-D_POSIX_THREADS',
        '-D_POSIX_READER_WRITER_LOCKS',
        '-D_UNIX98_THREAD_MUTEX_ATTRIBUTES'
    ]
    return flags

def getCIncludePath(floatType):
    if floatType == 'hard':
        subPath = '/v7e-m+dp/hard'
    else:
        subPath = '/v7e-m/nofp'

    flags = [
        'usr/arm-none-eabi/include/c++/9.3.1',
        'usr/arm-none-eabi/include/c++/9.3.1/arm-none-eabi/thumb' + subPath,
        'usr/arm-none-eabi/include/c++/9.3.1/backward',
        'usr/lib/gcc/arm-none-eabi-9.3.1/include',
        'usr/lib/gcc/arm-none-eabi-9.3.1/include-fixed',
        'usr/arm-none-eabi/include',
    ]
    flags = ['-I' + str(gSdkPath / item) for item in flags]
    return flags

def getCFlags(floatType):
    flags = []

    flags += getCArch(floatType)
    flags += getCPredefined()
    flags += getCIncludePath(floatType)
    return flags




def getSwiftArch(floatType):
    if floatType == 'hard':
        flags = [
            '-target',
            'thumbv7em-unknown-none-eabihf',
            '-target-cpu',
            'cortex-m7',
            '-float-abi',
            'hard'
        ]
    else:
        flags = [
            '-target',
            'thumbv7em-unknown-none-eabi',
            '-target-cpu',
            'cortex-m7+nofp',
            '-float-abi',
            'soft'
        ]
    return flags

def getSwiftPredefined():
    flags = [
        '-static-stdlib',
        '-Xfrontend',
        '-function-sections',
        '-Xfrontend',
        '-data-sections',
        '-Xcc',
        '-D__MADMACHINE__',
        '-Xcc',
        '-D_POSIZ_THREADS',
        '-Xcc',
        '-D_POSIX_READER_WRITER_LOCKS',
        '-Xcc',
        '-D_UNIX98_THREAD_MUTEX_ATTRIBUTES'
    ]
    return flags

def getLinkerPredefined():
    flags = [
        '-u,_OffsetAbsSyms',
        '-u,_ConfigAbsSyms',
        '-X',
        '-N',
        '--gc-sections',
        '--build-id=none',
        '--sort-common=descending',
        '--sort-section=alignment',
        '--no-enum-size-warning',
        '--print-memory-usage'
    ]
    flags = ['-Xlinker ' + item for item in flags]
    combinedFlags = ' '.join(flags)
    flags = combinedFlags.split(' ')
    return flags

def getLinkerScript(boardName, floatType):
    flags = [
        '-T',
        str(gSdkPath / 'Boards' / boardName / 'linker/ram.ld')
    ]
    flags = ['-Xlinker ' + item for item in flags]
    combinedFlags = ' '.join(flags)
    flags = combinedFlags.split(' ')
    return flags

def getLibrarySearchFlags(floatType):
    if floatType == 'hard':
        subPath = '/v7e-m+dp/hard'
    else:
        subPath = '/v7e-m/nofp'
    
    flags = [
        'usr/lib/gcc/arm-none-eabi/9.3.1/thumb' + subPath,
        'usr/lib/gcc/thumb' + subPath,
        'usr/arm-none-eabi/lib/arm-none-eabi/9.3.1/thumb' + subPath,
        'usr/arm-none-eabi/lib/thumb' + subPath,
        'usr/arm-none-eabi/lib/arm-none-eabi/9.3.1/thumb' + subPath,
        'usr/arm-none-eabi/lib/thumb' + subPath,
        'usr/arm-none-eabi/usr/lib/arm-none-eabi/9.3.1/thumb' + subPath,
        'usr/arm-none-eabi/usr/lib/thumb' + subPath,
        'usr/lib/gcc/arm-none-eabi/9.3.1',
        'usr/lib/gcc',
        'usr/arm-none-eabi/lib/arm-none-eabi/9.3.1',
        'usr/arm-none-eabi/lib',
        'usr/arm-none-eabi/usr/lib/arm-none-eabi/9.3.1',
        'usr/arm-none-eabi/usr/lib',
    ]
    flags = ['-L' + str(gSdkPath / item) for item in flags]
    return flags


def getBoardLibraryFlags(boardName, floatType):
    if floatType == 'hard':
        subPath = 'eabihf'
    else:
        subPath = 'eabi'

    libraries = ['--whole-archive']
    libraries += sorted((gSdkPath / 'Boards' / boardName / 'lib/thumbv7em' / subPath / 'whole').glob('*.obj'))
    libraries += sorted((gSdkPath / 'Boards' / boardName / 'lib/thumbv7em' / subPath / 'whole').glob('*.a'))
    libraries.append('--no-whole-archive')

    libraries += sorted((gSdkPath / 'Boards' / boardName / 'lib/thumbv7em' / subPath / 'nowhole').glob('*.obj'))
    libraries += sorted((gSdkPath / 'Boards' / boardName / 'lib/thumbv7em' / subPath / 'nowhole').glob('*.a'))

    flags = ['-Xlinker ' + str(item) for item in libraries]
    flags += [
        '-lswiftCore',
        '-lstdc++',
        '-lc',
        '-lg',
        '-lm',
        '-lgcc'
    ]
    combinedFlags = ' '.join(flags)
    flags = combinedFlags.split(' ')
    return flags

def getSwiftcFlags(boardName, floatType):
    flags = []

    flags += getSwiftArch(floatType)
    flags += getSwiftPredefined()
    flags += getLinkerPredefined()
    flags += getLinkerScript(boardName, floatType)
    flags += getLibrarySearchFlags(floatType)
    flags += getBoardLibraryFlags(boardName, floatType)
    return flags

def generateDestinationJson(boardName, floatType, targetArch):
    cFlags = getCFlags(floatType)
    swiftcFlags = getSwiftcFlags(boardName, floatType)
    sdk = str(gSdkPath)
    target = targetArch
    binDir = str(gSdkPath / 'usr/bin')

    dic = {
        'extra-cc-flags': cFlags,
        'extra-cpp-flags': cFlags,
        'extra-swiftc-flags': swiftcFlags,
        'sdk': sdk,
        'target': target,
        'toolchain-bin-dir': binDir,
        'version': 1
    }
    
    js = json.dumps(dic, indent = 4)
    return js

def buildSwift(destinationFile):
    flags = [
        '-c release',
        '--destination',
        quoteStr(destinationFile)
    ]

    cmd = quoteStr(getSdkTool('swift-build'))
    for item in flags:
        cmd += ' ' + item

    os.chdir(gProjectPath)
    if gVerbose:
        cmd += ' -v'
        print(cmd)
    p = subprocess.Popen(cmd, shell = True)
    p.wait()
    if p.poll():
        os._exit(-1)

def buildProject(args):
    boardName = args.board
    floatType = args.float
    if floatType == 'hard':
        targetArch = 'thumbv7em-unknown-none-eabihf'
    else:
        targetArch = 'thumbv7em-unknown-none-eabi'
    projectName = getProjectName()

    cleanBin(targetArch)

    js = generateDestinationJson(boardName, floatType, targetArch)
    (gProjectPath / '.build').mkdir(exist_ok=True)
    destinationFile = gProjectPath / '.build/destination.json'
    destinationFile.write_text(js, encoding='UTF-8')

    buildSwift(destinationFile)
    generateBin(projectName, targetArch)
    addCrcToBin(boardName, projectName, targetArch)

def parseArgs():
    global gProjectPath
    global gSdkPath
    global gVerbose

    gSdkPath = Path(os.path.realpath(__file__))
    gSdkPath = Path(gSdkPath.parent.parent.parent)
    gProjectPath = Path('.').resolve()

    parentParser = argparse.ArgumentParser()
    parentParser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase output verbosity")

    subparsers = parentParser.add_subparsers(title='actions')

    initParser = subparsers.add_parser('init', help = 'Initiaize a new project. Could be either an executable or a library')
    initParser.add_argument('--type', type = str, choices = ['executable', 'library'], default = 'executable', help = 'Project type, default type is executable')
    initParser.add_argument('--name', type = str, help = 'Initiaize the new project with a specified name, otherwise the project name depends on the current directory name')
    initParser.set_defaults(func = initProject)

    buildParser = subparsers.add_parser('build', help = 'Build a project')
    buildParser.add_argument('-b', '--board', type = str, choices =['SwiftIOBoard', 'SwiftIOFeather'], required = True, help = 'Used for linking lower-level board libraries')
    buildParser.add_argument('-f', '--float', type = str, choices = ['soft', 'hard'], default = 'soft', help = 'Use soft float or hard float, default is soft')
    buildParser.set_defaults(func = buildProject)

    args = parentParser.parse_args()
    if args.verbose:
        gVerbose = True
    args.func(args)

if __name__ == '__main__':
    parseArgs()