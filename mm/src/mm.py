#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import os, sys
import platform
import argparse
import toml
import json
import subprocess
import shutil
from pathlib import Path
import struct
from zlib import crc32

gSdkPath = ''
gProjectPath = ''
gSystem = ''
gMountPath = None
gVerbose = False

def getBoardInfo(boardName, info):
    boardDict = {'vid': '0x1fc9',
                'pid': '0x0093',
                'serialNumber': '012345671FC90093',
                'binFileName': 'swiftio.bin'}
    featherDict = {'vid': '0x1fc9',
                'pid': '0x0095',
                'serialNumber': '012345671FC90095',
                'binFileName': 'feather.bin'}

    if boardName == 'SwiftIOBoard':
        dic = boardDict
    else:
        dic = featherDict
    
    return dic.get(info)

def quoteStr(path):
    return '"%s"' % str(path)

def generateProjectFile(boardName=None, floatType=None):
    #projectName = getProjectInfo('name')

    if boardName is None or floatType is None:
        print('error: Please specify --board and --float when generating MadMachine Project file')
        os._exit(-1)
    
    content = """# This is a MadMachine project file in TOML format
# This file holds those parameters that could not be managed by SwiftPM
# Edit this file would change the behavior of the building/downloading procedure
# Those project files in the dependent libraries would be IGNORED

# Specify the board name below, there are "SwiftIOBoard" and "SwiftIOFeather" now
board = "{name}"

# Specifiy the floating-point type below, there are "soft" and "hard"
# If your code use significant floating-point calculation, plz set it to "hard"
float-type = "{float}"

# Reserved for future use 
version = 1
"""
    content = content.format(name=boardName, float=floatType)
    (gProjectPath / 'Package.mmp').write_text(content, encoding='UTF-8')

def rewriteManifest(initType, projectName):
    if initType == 'library': 
        content = """// swift-tools-version:5.3
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "{name}",
    products: [
        // Products define the executables and libraries a package produces, and make them visible to other packages.
        .library(
            name: "{name}",
            targets: ["{name}"]),
    ],
    dependencies: [
        // Dependencies declare other packages that this package depends on.
        .package(url: "https://github.com/madmachineio/SwiftIO.git", .upToNextMajor(from: "0.0.1")),
    ],
    targets: [
        // Targets are the basic building blocks of a package. A target can define a module or a test suite.
        // Targets can depend on other targets in this package, and on products in packages this package depends on.
        .target(
            name: "{name}",
            dependencies: ["SwiftIO"]),
        .testTarget(
            name: "{name}Tests",
            dependencies: ["{name}"]),
    ]
)
"""
    else:
        content = """// swift-tools-version:5.3
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "{name}",
    dependencies: [
        // Dependencies declare other packages that this package depends on.
        .package(url: "https://github.com/madmachineio/SwiftIO.git", .upToNextMajor(from: "0.0.1")),
        .package(url: "https://github.com/madmachineio/MadBoards.git", .upToNextMajor(from: "0.0.1")),
        .package(url: "https://github.com/madmachineio/MadDrivers.git", .upToNextMajor(from: "0.0.1")),
    ],
    targets: [
        // Targets are the basic building blocks of a package. A target can define a module or a test suite.
        // Targets can depend on other targets in this package, and on products in packages this package depends on.
        .target(
            name: "{name}",
            dependencies: [
                "SwiftIO",
                "MadBoards",
                "MadDrivers"]),
        .testTarget(
            name: "{name}Tests",
            dependencies: ["{name}"]),
    ]
)
"""     

    content = content.format(name=projectName)
    (gProjectPath / 'Package.swift').write_text(content, encoding='UTF-8')



def initProject(args):
    global gVerbose
    if args.verbose:
        gVerbose = True

    initType = args.type
    if args.name:
        name = args.name
    else:
        name = Path('.').resolve().name
    initFlags = [
        '--type ' + initType,
        '--name ' + name
    ]
    
    cmd = quoteStr(getSdkTool('swift-package')) + ' init'
    for item in initFlags:
        cmd += ' ' + item

    if gVerbose:
        print(cmd)
    p = subprocess.Popen(cmd, shell = True)
    p.wait()
    if p.poll():
        os._exit(-1)
    
    if not args.nooverride:
        rewriteManifest(initType, name)
    
    if args.board:
        generateProjectFile(args.board, 'soft')

    os._exit(0)

def getProjectInfo(info):
    cmd = quoteStr(getSdkTool('swift-package'))

    flags = [
        'describe --type json'
    ]

    for item in flags:
        cmd += ' ' + item

    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()
    if p.poll():
        cmdOut, cmdErr = p. communicate()
        print(cmdErr.decode('utf-8'))
        os._exit(-1)
    cmdOut, cmdErr = p.communicate()
    jsonData = cmdOut.decode('utf-8')
    projectName = json.loads(jsonData).get('name')
    if info == 'name':
        return projectName

    projectType = None

    products = json.loads(jsonData).get('products')
    for product in products:
        if product.get('name') == projectName:
            productType = product.get('type')
            if productType.get('executable') is not None:
                projectType = 'executable'
            elif productType.get('library') is not None:
                projectType = 'library'
            break

    if projectType is None:
        targets = json.loads(jsonData).get('targets')
        for target in targets:
            if target.get('name') == projectName:
                projectType = target.get('type')
                break

    if projectType is None:
        projectType = 'executable'

    return projectType


def getSdkTool(tool):
    value = ''
    if tool == 'swift-build':
        value = (gSdkPath / 'usr/bin/swift-build')
    elif tool == 'swift-package':
        value = (gSdkPath / 'usr/bin/swift-package')
    elif tool == 'objcopy':
        value = (gSdkPath / 'usr/bin/arm-none-eabi-objcopy')
    elif tool == 'mm':
        value = (gSdkPath / 'usr/mm/mm')

    if not value.exists():
        print('error: Cannot find ' + str(value))
        os._exit(-1)
    return value

def cleanProject(targetArch, deepClean):
    files = sorted((gProjectPath / '.build' / targetArch / 'release').glob('*.bin'))
    for file in files:
        file.unlink()

    if deepClean:
        cmd = quoteStr(getSdkTool('swift-package'))

        flags = [
            'clean'
        ]

        for item in flags:
            cmd += ' ' + item

        p = subprocess.Popen(cmd, shell = True)
        p.wait()

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
        print('error: Generate binary failed!')
        os._exit(-1)

def addCrcToBin(boardName, projectName, targetArch):
    if boardName == 'SwiftIOFeather':
        targetFile = gProjectPath / '.build' / targetArch / 'release' / getBoardInfo(boardName, 'binFileName')
    elif boardName == 'SwiftIOBoard':
        targetFile = gProjectPath / '.build' / targetArch / 'release' / getBoardInfo(boardName, 'binFileName')

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
        'usr/lib/gcc/arm-none-eabi/9.3.1/include',
        'usr/lib/gcc/arm-none-eabi/9.3.1/include-fixed',
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
    libraries += sorted((gSdkPath / 'Boards' / boardName / 'lib/thumbv7em' / subPath / 'whole').glob('[a-z]*.obj'))
    libraries += sorted((gSdkPath / 'Boards' / boardName / 'lib/thumbv7em' / subPath / 'whole').glob('[a-z]*.a'))

    libraries.append('--no-whole-archive')
    libraries += sorted((gSdkPath / 'Boards' / boardName / 'lib/thumbv7em' / subPath / 'nowhole').glob('[a-z]*.obj'))
    libraries += sorted((gSdkPath / 'Boards' / boardName / 'lib/thumbv7em' / subPath / 'nowhole').glob('[a-z]*.a'))

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

def compileSwift(destinationFile):
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
        print('error: Compile failed')
        os._exit(-1)

def buildProject(args):
    global gVerbose
    if args.verbose:
        gVerbose = True


    boardName = args.board
    floatType = args.float
    if floatType == 'hard':
        targetArch = 'thumbv7em-unknown-none-eabihf'
    else:
        targetArch = 'thumbv7em-unknown-none-eabi'

    projectName = getProjectInfo('name')
    cleanProject(targetArch, False)

    js = generateDestinationJson(boardName, floatType, targetArch)
    (gProjectPath / '.build').mkdir(exist_ok=True)
    destinationFile = gProjectPath / '.build/destination.json'
    destinationFile.write_text(js, encoding='UTF-8')

    compileSwift(destinationFile)

    if (gProjectPath / '.build' / targetArch / 'release' / projectName).exists():
        generateBin(projectName, targetArch)
        addCrcToBin(boardName, projectName, targetArch)

def darwinRecursiveParsing(data, vid, pid):
    global gMountPath

    if gMountPath is not None:
        return

    if isinstance(data, list):
        for list_item in data:
            darwinRecursiveParsing(list_item, vid, pid)
    elif isinstance(data, dict):
        venderId = data.get('vendor_id')
        productId = data.get('product_id')
        if venderId is not None and productId is not None:
            venderId = venderId.lower()
            productId = productId.lower()
            if venderId.startswith(vid) and productId.startswith(pid):
                first = data.get('Media')
                if first is not None:
                    second = first[0].get('volumes')
                    if second is not None:
                        third = second[0].get('mount_point')
                        if third is not None:
                            #gMountPath = data.get('Media')[0].get('volumes')[0].get('mount_point')
                            gMountPath = third
                            return
        for key, value in data.items():
            if isinstance(value, dict):
                darwinRecursiveParsing(value, vid, pid)
            elif isinstance(value, list):
                for list_item in value:
                    darwinRecursiveParsing(list_item, vid, pid)

def darwinGetMountPoint(boardName):
    global gMountPath

    vid = getBoardInfo(boardName, 'vid')
    pid = getBoardInfo(boardName, 'pid')
    #serialNumber = getBoardInfo(boardName, 'serialNumber')

    cmd = 'system_profiler -json SPUSBDataType'
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.wait()
    if p.poll():
        cmdOut, cmdErr = p. communicate()
        print(cmdErr.decode('utf-8'))
        os._exit(-1)
    cmdOut, cmdErr = p.communicate()
    jsonData = cmdOut.decode('utf-8')

    gMountPath = None
    darwinRecursiveParsing(json.loads(jsonData), vid, pid)

def darwinDownload(boardName):
    fileName = getBoardInfo(boardName, 'binFileName')
    
    source = gProjectPath / '.build' / 'release' / fileName
    if not source.exists():
        print('error: Cannot find ' + fileName + ', please build the project first')
        os._exit(-1)

    print('Detecting SD card...')
    darwinGetMountPoint(boardName)
    if not gMountPath:
        print('error: Cannot find ' +  boardName + ', please make sure it is corectlly mounted')
        os._exit(-1)
    print(gMountPath + ' found')
    target = Path(gMountPath) / fileName

    print('Copying ' + fileName + '...')
    shutil.copyfile(source, target)
    
    cmd = 'diskutil eject ' + quoteStr(gMountPath)
    print('Ejecting SD card...')
    p = subprocess.Popen(cmd, shell=True)
    p.wait()
    if p.poll():
        print('error: Eject SD card failed')
        os._exit(-1)

def downloadProject(args):
    global gVerbose
    if args.verbose:
        gVerbose = True

    boardName = args.board

    if gSystem != 'Darwin':
        print("error: Windows and Linux are not supported currently, please copy the binary file manually")
        os._exit(-1)
    else:
        darwinDownload(boardName)


def runAction(args):
    acctionType = args.action

    if acctionType == 'generate':
        if not args.board:
            print('error: Board name is needed to generate the project file')
            os._exit(-1)
        boardName = args.board
        floatType = 'soft'
        generateProjectFile(boardName, floatType)

        os._exit(0)

    if acctionType == 'get-status':
        projectFile = gProjectPath / 'Package.mmp'
        if not projectFile.exists():
            print('error: Cannot find MadMachine project file')
            os._exit(-1)
        tomlString = projectFile.read_text()
        try:
            tomlDic = toml.loads(tomlString)
        except:
            print('error: Project file decoding failed')
            os._exit(-1)

        boardName = tomlDic.get('board')
        if boardName is None:
            print('error: Cannot find board name in project file')
            os._exit(-1)

        if gSystem != 'Darwin':
            print('Board detecting on ' + gSystem + ' is not supported currently, please copy the bin file manually')
            os._exit(-1)

        darwinGetMountPoint(boardName)

        if gMountPath is None:
            print(boardName + ' not connected')
        else:
            print(boardName + ' ready')
        os._exit(0)


    projectName = getProjectInfo('name')

    if acctionType == 'get-name':
        print(projectName)
        os._exit(0)


    if acctionType == 'build':
        if args.board:
            print('warning: Board name is defined in project file already!')
        projectFile = gProjectPath / 'Package.mmp'
        if not projectFile.exists():
            print('error: Cannot find MadMachine project file')
            os._exit(-1)
        tomlString = projectFile.read_text()
        try:
            tomlDic = toml.loads(tomlString)
        except:
            print('error: Project file decoding failed')
            os._exit(-1)

        boardName = tomlDic.get('board')
        floatType = tomlDic.get('float-type')
        if boardName is None or floatType is None:
            print('error: Cannot find board name in project file')
            os._exit(-1)

        flags = [
            '--board ' + boardName,
            '--float ' + floatType,
        ]

        cmd = quoteStr(getSdkTool('mm')) + ' build'
        for item in flags:
            cmd += ' ' + item

        print("Building...")
        p = subprocess.Popen(cmd, shell = True)
        p.wait()
        if p.poll():
            print("error: Build failed")
            os._exit(-1)
        os._exit(0)
    
    projectType = getProjectInfo('type')
    if acctionType == 'download':
        if projectType == 'library':
            print('error: Cannot download a library')
            os._exit(-1)

        if args.board:
            print('warning: Board name is defined in project file already!')
        projectFile = gProjectPath / 'Package.mmp'
        if not projectFile.exists():
            print('error: Cannot find MadMachine project file')
            os._exit(-1)
        tomlString = projectFile.read_text()
        try:
            tomlDic = toml.loads(tomlString)
        except:
            print('error: Project file decoding failed')
            os._exit(-1)

        boardName = tomlDic.get('board')
        if boardName is None:
            print('error: Cannot find board name in project file')
            os._exit(-1)

        flags = [
            '--board ' + boardName,
        ]
        cmd = quoteStr(getSdkTool('mm')) + ' download'
        for item in flags:
            cmd += ' ' + item

        print("Downloading...")
        p = subprocess.Popen(cmd, shell = True)
        p.wait()
        if p.poll():
            print("error: Download failed")
            os._exit(-1)
        os._exit(0)


def parseArgs():
    global gProjectPath
    global gSdkPath
    global gSystem

    gSdkPath = Path(os.path.realpath(sys.argv[0]))
    gSdkPath = Path(gSdkPath.parent.parent.parent)
    gProjectPath = Path('.').resolve()
    gSystem = platform.system()

    parentParser = argparse.ArgumentParser()
    subparsers = parentParser.add_subparsers(title='actions')


    initParser = subparsers.add_parser('init', help = 'Initiaize a new project')
    initParser.add_argument('--type', type = str, choices = ['executable', 'library'], default = 'executable', help = 'Project type, default type is executable')
    initParser.add_argument('--name', type = str, help = 'Initiaize the new project with a specified name, otherwise the project name depends on the current directory name')
    initParser.add_argument('-b', '--board', type = str, choices =['SwiftIOBoard', 'SwiftIOFeather'], help = 'Generate MadMachine project file by passing this parameter')
    initParser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase output verbosity")
    initParser.add_argument('--nooverride', action = 'store_true', default = False, help = "Don't overwrite the Package.swift file with a common used template")
    initParser.set_defaults(func = initProject)

    buildParser = subparsers.add_parser('build', help = 'Build a project')
    buildParser.add_argument('-b', '--board', type = str, choices =['SwiftIOBoard', 'SwiftIOFeather'], help = 'Used for linking lower-level board libraries')
    buildParser.add_argument('-f', '--float', type = str, choices = ['soft', 'hard'], default = 'soft', help = 'Use soft or hard floating-point, default is soft')
    buildParser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase output verbosity")
    buildParser.set_defaults(func = buildProject)

    downloadParser = subparsers.add_parser('download', help = 'Download a compiled executable to the board\'s SD card')
    downloadParser.add_argument('-b', '--board', type = str, choices =['SwiftIOBoard', 'SwiftIOFeather'], help = 'Used for linking lower-level board libraries')
    downloadParser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase output verbosity")
    downloadParser.set_defaults(func = downloadProject)

    runParser = subparsers.add_parser('run', help = 'Take actions according to MadMachine project file')
    runParser.add_argument('-a', '--action', type = str, choices =['generate', 'build', 'download', 'get-status', 'get-name'], required = True, help = 'Choose the action you want')
    runParser.add_argument('-b', '--board', type = str, choices =['SwiftIOBoard', 'SwiftIOFeather'], help = 'Generate MadMachine project file by passing this parameter')
    runParser.set_defaults(func = runAction)

    args = parentParser.parse_args()
    d = vars(args)
    if d.get('func') is None:
        print('use \'mm --help\' to get more information')
        os._exit(-1)
    args.func(args)

if __name__ == '__main__':
    parseArgs()