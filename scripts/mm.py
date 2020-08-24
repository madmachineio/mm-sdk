#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import os, sys
import argparse
import toml
import subprocess
from pathlib import Path
import struct
from zlib import crc32

g_ProjectPath = ''
g_BuildPath = ''
g_SdkPath = ''
g_CHeader = ''
g_ProjectName = ''
g_ToolBase = ''
g_SearchPaths = []
g_Verbose = False
g_Rebuild = False

defaultExeToml = """# This is a MadMachine project file generated automatically.

board = "SwiftIOBoard"
type = "executable"
dependencies = [
    "SwiftIO",
]"""

defaultLibToml = """# This is a MadMachine project file generated automatically.

board = "SwiftIOBoard"
type = "library"
dependencies = [
    "SwiftIO",
]"""

def quoteStr(path):
    return '"%s"' % str(path)

def generateToml(name, type):
    ret = sorted(Path('.').glob('*.mmp'))

    if ret:
        print('Error: Project ' + ret[0].name + ' already exist, initiaization failed!')
        os._exit(-1)

    Path('./' + name + '.mmp').touch(exist_ok = True)
    if type == 'lib':
        Path('./' + name + '.mmp').write_text(defaultLibToml)
        Path('./Sources/' + name + '/' + name + '.swift').touch(exist_ok = True)
    else:
        Path('./' + name + '.mmp').write_text(defaultExeToml)
        Path('./Sources/' + name + '/main.swift').touch(exist_ok = True)


def initProject(args):
    if args.name:
        name = args.name
    else:
        name = Path('.').resolve().name

    src = Path('./Sources') / name
    src.mkdir(parents = True, exist_ok = True)
    generateToml(name, args.type)

    os._exit(0)


def parseTOML():
    ret = sorted(g_ProjectPath.glob('*.mmp'))

    if ret:
        name = ret[0].stem
        tomlString = ret[0].read_text()
        if tomlString:
            try:
                tomlDic = toml.loads(tomlString)
            except:
                print('Error: Project file ' + ret[0].name + ' decoding failed!')
                os._exit(-1)
        else:
            ret[0].write_text(defaultExeToml)
            tomlDic = toml.loads(defaultExeToml)
        tomlDic['name'] = name
        return tomlDic

    print('Error: Can not find project file!')
    os._exit(-1)
    

def cleanBuild(targetPath):
    files =  sorted(targetPath.glob('*.bin'))
    files += sorted(targetPath.glob('*.elf'))
    files += sorted(targetPath.glob('*.map'))
    files += sorted(targetPath.glob('*.a'))
    files += sorted(targetPath.glob('*.o*'))
    files += sorted(targetPath.glob('*.c'))
    files += sorted(targetPath.glob('*.swiftmodule'))
    files += sorted(targetPath.glob('*.swiftdoc'))
    for file in files:
        file.unlink()
    return


def getSdkTool(tool):
    value = ''
    if tool == 'swiftc':
        value = (g_SdkPath / g_ToolBase / 'toolchains/swift/bin/swiftc')
    elif tool == 'stdPath':
        value = (g_SdkPath / g_ToolBase / 'toolchains/swift/lib/swift/zephyr/thumbv7em')
    elif tool == 'ar':
        value = (g_SdkPath / g_ToolBase / 'toolchains/gcc/bin/arm-none-eabi-ar')
    elif tool == 'gcc':
        value = (g_SdkPath / g_ToolBase / 'toolchains/gcc/bin/arm-none-eabi-gcc')
    elif tool == 'gpp':
        value = (g_SdkPath / g_ToolBase / 'toolchains/gcc/bin/arm-none-eabi-g++')
    elif tool == 'objcopy':
        value = (g_SdkPath / g_ToolBase / 'toolchains/gcc/bin/arm-none-eabi-objcopy')
    elif tool == 'gen_isr_tables':
        value = (g_SdkPath / g_ToolBase / 'scripts/dist/gen_isr_tables/gen_isr_tables')
    elif tool == 'mm':
        value = (g_SdkPath / g_ToolBase / 'scripts/dist/mm/mm')
    return value


def resolveModule(modulePath, moduleName):
    ret = sorted(modulePath.glob(moduleName + '*'))
    if ret:
        realPath = ret[0]
    else:
        print("Error: Can not find module " + moduleName)
        os._exit(-1)

    buildPath = realPath / '.build'

    if buildPath.exists() and g_Rebuild == False:
        swiftModule = sorted(buildPath.glob(moduleName + '.swiftmodule'))
        staticLibrary = sorted(buildPath.glob('lib' + moduleName + '.a'))
        if swiftModule and staticLibrary:
            return buildPath

    buildPath.mkdir(exist_ok = True)
    cleanBuild(buildPath)

    cmd = quoteStr(getSdkTool('mm'))
    cmd += ' build --sdk '
    cmd += quoteStr(g_SdkPath)

    cmd += ' --module '
    cmd += quoteStr(modulePath)

    os.chdir(realPath)
    if g_Verbose:
        cmd += ' -v'
        print(cmd)
    p = subprocess.Popen(cmd, shell = True)
    p.wait()
    if p.poll():
        print('Error: Building module ' + moduleName + ' failed!')
        os._exit(-1)
    return buildPath


def compileSwift(target):
    cmd = quoteStr(getSdkTool('swiftc'))

    swiftFlags = [
        '-module-name ' + g_ProjectName,
        '-target thumbv7em-none--eabi',
        '-target-cpu cortex-m7',
        '-target-fpu fpv5-dp-d16',
        '-float-abi soft',
        '-O',
        '-static-stdlib',
        '-function-sections',
        '-data-sections',
        '-Xcc -D__ZEPHYR__',
        '-Xfrontend -assume-single-threaded',
        '-no-link-objc-runtime'
    ]

    if target == 'module':
        swiftFlags.insert(0, '-emit-module')
        swiftFlags.insert(0, '-parse-as-library')
    elif target == 'object':
        swiftFlags.insert(0, '-c')
        swiftFlags.insert(0, '-parse-as-library')
    elif target == 'exe':
        swiftFlags.insert(0, '-c')
    else:
        os._exit(-1)

    if g_CHeader: 
        swiftFlags.append('-import-objc-header ' + quoteStr(g_CHeader))

    for item in g_SearchPaths:
        swiftFlags.append('-I ' + quoteStr(item))

    swiftFiles = sorted((g_ProjectPath / 'Sources' / g_ProjectName).rglob("*.swift"))
    for file in swiftFiles:
        swiftFlags.append(quoteStr(file))

    for item in swiftFlags:
        cmd += ' ' + item

    os.chdir(g_BuildPath)
    if g_Verbose:
        print(cmd)
    p = subprocess.Popen(cmd, shell = True)
    p.wait()
    if p.poll():
        print('Error: Compiling swift files failed!')
        os._exit(-1)


def mergeObjects():
    cmd = quoteStr(getSdkTool('ar'))

    arFlags = [
        '-rcs'
    ]

    targetName = quoteStr(g_BuildPath / ('lib' + g_ProjectName + '.a'))
    arFlags.append(targetName)

    files = sorted(g_BuildPath.glob("*.o"))
    for file in files:
        arFlags.append(quoteStr(file))

    for item in arFlags:
        cmd += ' ' + item

    os.chdir(g_BuildPath)
    if g_Verbose:
        print(cmd)
    p = subprocess.Popen(cmd, shell = True)
    p.wait()
    if p.poll():
        print('Error: Archiving objects failed!')
        os._exit(-1)


def linkELF(step):
    cmd = quoteStr(getSdkTool('gpp'))

    flags = [
        '-mcpu=cortex-m7',
        '-mthumb',
        '-mfpu=fpv5-d16',
        '-mfloat-abi=soft',
        '-mabi=aapcs',
        '-nostdlib',
        '-static',
        '-no-pie',
        '-Wl,-u,_OffsetAbsSyms',
        '-Wl,-u,_ConfigAbsSyms',
        #'-Wl,--print-memory-usage',
        '-Wl,-X',
        '-Wl,-N',
        '-Wl,--gc-sections',
        '-Wl,--build-id=none',
        '-Wl,--sort-common=descending',
        '-Wl,--sort-section=alignment',
        '-Wl,--no-enum-size-warning',
        #'-Wl,--strip-all',
        #'-Wl,--orphan-handling=warn',
        #'-Wl,-Map=' + buildFolder + '/' + g_ProjectName + '.map',
        #halPath + '/generated/empty_file.c.obj'
    ]

    if step == 'step2':
        mapTarget = quoteStr(g_BuildPath / (g_ProjectName + '.map'))
        flags.append('-Wl,-Map=' + mapTarget)
        flags.append('-Wl,--print-memory-usage')
        linkScript = quoteStr(g_SdkPath / 'hal/HalSwiftIOBoard/generated/linker_pass_final.cmd')
        flags.append('-Wl,-T ' + linkScript)
        flags.append(quoteStr(g_BuildPath / 'isr_tables.c.obj'))
    elif step == 'step1':
        linkScript = quoteStr(g_SdkPath / 'hal/HalSwiftIOBoard/generated/linker.cmd')
        flags.append('-Wl,-T ' + linkScript)  
        flags.append(quoteStr(g_SdkPath / 'hal/HalSwiftIOBoard/generated/empty_file.c.obj'))
    
    flags.append('-L' + quoteStr(g_SdkPath / g_ToolBase / 'toolchains/gcc/arm-none-eabi/lib/thumb/v7e-m'))
    flags.append('-L' + quoteStr(g_SdkPath / g_ToolBase / 'toolchains/gcc/lib/gcc/arm-none-eabi/7.3.1/thumb/v7e-m'))

    flags.append('-Wl,--whole-archive')
    flags.append(quoteStr(g_SdkPath / g_ToolBase / 'toolchains/swift/lib/swift/zephyr/thumbv7em/swiftrt.o'))
    flags.append(quoteStr(g_BuildPath / ('lib' + g_ProjectName + '.a')))

    librarFiles = sorted((g_SdkPath / 'hal/HalSwiftIOBoard/generated/whole').rglob("*.a"))
    for file in librarFiles:
        flags.append(quoteStr(file))

    flags.append('-Wl,--no-whole-archive')

    if step == 'step1':
        #g_SearchPaths.append(g_BuildPath)
        g_SearchPaths.append(g_SdkPath / 'hal/HalSwiftIOBoard/generated/no_whole')

    #print(g_SearchPaths)

    flags.append('-Wl,--start-group')
    for item in reversed(g_SearchPaths):
        files = sorted(item.glob("*.a"))
        for file in files:
            flags.append(quoteStr(file))
    
    flags += [
        #'-Wl,--start-group',
        '-lgcc',
        '-lstdc++',
        '-lm',
        '-lc',
        '-Wl,--end-group',
        '-o'
    ]

    if step == 'step1':
        flags.append(quoteStr(g_BuildPath / (g_ProjectName + '_prebuilt.elf')))
    elif step == 'step2':
        flags.append(quoteStr(g_BuildPath / (g_ProjectName + '.elf')))

    for item in flags:
        cmd += ' ' + item

    os.chdir(g_BuildPath)
    if g_Verbose:
        print(cmd)
    p = subprocess.Popen(cmd, shell = True)
    p.wait()
    if p.poll():
        print('Error: Linking failed!')
        os._exit(-1)


def generateIsr():
    cmd = quoteStr(getSdkTool('objcopy'))

    flags = [
        '-I elf32-littlearm',
        '-O binary',
        '--only-section=.intList',
        quoteStr(g_BuildPath / (g_ProjectName + '_prebuilt.elf')),
        'isrList.bin'
    ]

    for item in flags:
        cmd += ' ' + item

    os.chdir(g_BuildPath)
    if g_Verbose:
        print(cmd)
    p = subprocess.Popen(cmd, shell = True)
    p.wait()
    if p.poll():
        print('Error: Generating isrList.bin failed!')
        os._exit(-1)



def generateIsrTable():
    cmd = quoteStr(getSdkTool('gen_isr_tables'))

    flags = [
        '--output-source',
        'isr_tables.c',
        '--kernel ' + quoteStr(g_BuildPath / (g_ProjectName + '_prebuilt.elf')),
        '--intlist',
        'isrList.bin',
        '--sw-isr-table',
        '--vector-table'
    ]

    for item in flags:
        cmd += ' ' + item

    os.chdir(g_BuildPath)
    if g_Verbose:
        print(cmd)
    p = subprocess.Popen(cmd, shell = True)
    p.wait()
    if p.poll():
        print('Error: Generating ISR C code failed!')
        os._exit(-1)


def compileIsr():
    cmd = quoteStr(getSdkTool('gcc'))

    includePath = [
        'hal/HalSwiftIOBoard/zephyr/include',
        'hal/HalSwiftIOBoard/zephyr/soc/arm/nxp_imx/rt',
        'hal/HalSwiftIOBoard/zephyr/lib/libc/newlib/include',
        'hal/HalSwiftIOBoard/zephyr/ext/hal/cmsis/Core/Include',
        'hal/HalSwiftIOBoard/modules/hal/nxp/mcux/devices/MIMXRT1052',
        'hal/HalSwiftIOBoard/modules/hal/nxp/mcux/drivers/imx',
        'hal/HalSwiftIOBoard/generated'
    ]

    flags = [
        '-DBOARD_FLASH_SIZE=CONFIG_FLASH_SIZE',
        '-DBUILD_VERSION=zephyr-v2.2.0',
        '-DCPU_MIMXRT1052DVL6B',
        '-DKERNEL',
        #'-DXIP_BOOT_HEADER_DCD_ENABLE=1',
        #'-DXIP_BOOT_HEADER_ENABLE=1',
        '-D_FORTIFY_SOURCE=2',
        '-D__LINUX_ERRNO_EXTENSIONS__',
        '-D__PROGRAM_START',
        '-D__ZEPHYR__=1',
        '-Os',
        '-ffreestanding',
        '-fno-common',
        '-g',
        '-mthumb',
        '-mcpu=cortex-m7',
        '-mfpu=fpv5-d16',
        '-mfloat-abi=soft',
        '-Wall',
        '-Wformat',
        '-Wformat-security',
        '-Wno-format-zero-length',
        '-Wno-main',
        '-Wno-pointer-sign',
        '-Wpointer-arith',
        '-Wno-unused-but-set-variable',
        '-Werror=implicit-int',
        '-fno-asynchronous-unwind-tables',
        '-fno-pie',
        '-fno-pic',
        '-fno-strict-overflow',
        '-fno-short-enums',
        '-fno-reorder-functions',
        '-fno-defer-pop',
        '-ffunction-sections',
        '-fdata-sections',
        '-mabi=aapcs',
        '-std=c99'
    ]

    for item in includePath:
        flags.append('-I' + quoteStr(g_SdkPath / item))
    
    flags.append('-isystem ' + quoteStr(g_SdkPath / g_ToolBase / 'toolchains/gcc/arm-none-eabi/include'))
    flags.append('-imacros ' + quoteStr(g_SdkPath / 'hal/HalSwiftIOBoard/generated/autoconf.h'))
    flags.append('-o ' + quoteStr(g_BuildPath / 'isr_tables.c.obj'))
    flags.append('-c ' + quoteStr(g_BuildPath / 'isr_tables.c'))

    for item in flags:
        cmd += ' ' + item

    os.chdir(g_BuildPath)
    if g_Verbose:
        print(cmd)
    p = subprocess.Popen(cmd, shell = True)
    p.wait()
    if p.poll():
        print('Error: Compiling ISR C code failed!')
        os._exit(-1)


def generateBin():
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
        '.eh_frame'
    ]

    flags.append(quoteStr(g_BuildPath / (g_ProjectName + '.elf')))
    flags.append(quoteStr(g_BuildPath / (g_ProjectName + '.bin')))

    for item in flags:
        cmd += ' ' + item

    os.chdir(g_BuildPath)
    if g_Verbose:
        print(cmd)
    p = subprocess.Popen(cmd, shell = True)
    p.wait()
    if p.poll():
        print('Error: Generating binary failed!')
        os._exit(-1)


def int32_to_int8(n):
    mask = (1 << 8) - 1
    return [(n >> k) & mask for k in range(0, 32, 8)]


def addCrcToBin():
    data = (g_BuildPath / (g_ProjectName + '.bin')).read_bytes()
    value = crc32(data)
    list_dec = int32_to_int8(value)

    targetFile = (g_BuildPath / 'swiftio.bin')

    os.chdir(g_BuildPath)
    with open(targetFile, 'wb') as file:
        file.write(data)
        for number in list_dec:
            byte = struct.pack('B', number)
            file.write(byte)


def buildLibrary():
    print('Building library ' + g_ProjectName + '...')
    compileSwift('module')
    compileSwift('object')
    mergeObjects()


def buildExecutable():
    print('Building executable ' + g_ProjectName + '...')
    compileSwift('exe')
    mergeObjects()
    linkELF('step1')
    generateIsr()
    generateIsrTable()
    compileIsr()
    linkELF('step2')
    generateBin()
    addCrcToBin()


def buildProject(args):
    global g_ProjectPath
    global g_SdkPath
    global g_BuildPath

    global g_SearchPaths

    global g_ProjectName
    global g_ToolBase
    global g_CHeader
    global g_Verbose
    global g_Rebuild

    g_ProjectPath = Path('.').resolve()

    if Path(args.sdk).exists():
        g_SdkPath = Path(args.sdk).resolve()
    else:
        print('Error: Can not find SDK path: ' + str(args.sdk))
        os._exit(-1)

    if args.verbose:
        g_Verbose = True
    
    if args.rebuild:
        g_Rebuild = True

    if sys.platform.startswith('darwin'):
        g_ToolBase = 'tools_mac'
    elif sys.platform.startswith('win'):
        g_ToolBase = 'tools_win'
    elif sys.platform.startswith('linux'):
        g_ToolBase = 'tools_linux'

    #if args.module:
    modulePath = Path(args.module).resolve()
    #else:
    #    modulePath = (Path.home() / 'Documents' / 'MadMachine' / 'Library').resolve()

    if not modulePath.exists():
        print('Error: Can not find module path: ' + str(modulePath))
        os._exit(-1)

    # Parse name, type, dependencies, c header
    tomlDic = parseTOML()
    g_ProjectName = tomlDic['name']
    if tomlDic.get('header'):
        g_CHeader = Path(tomlDic['header']).resolve()

    for moduleName in tomlDic['dependencies']:
        g_SearchPaths.append(resolveModule(modulePath, moduleName))

    g_SearchPaths.append(getSdkTool('stdPath'))

    g_BuildPath = g_ProjectPath / '.build'
    g_BuildPath.mkdir(exist_ok = True)
    cleanBuild(g_BuildPath)

    if tomlDic['type'] == 'library':
        buildLibrary()
    elif tomlDic['type'] == 'executable':
        buildExecutable()


def parseArgs():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    initParser = subparsers.add_parser('init', help = 'Initiaize a new project. Could be either an executable or a library')
    initParser.add_argument('-n', '--name', type = str, help = 'Initiaize the new project with a specified name, otherwise the project name depends on the current directory name')
    initParser.add_argument("-t", "--type", type = str, choices = ['exe', 'lib'], default = 'exe', help = "Project type, default type is executable")
    initParser.set_defaults(func = initProject)

    buildParser = subparsers.add_parser('build', help = 'Build a project')
    buildParser.add_argument('--sdk', type = str, required = True, help = "SDK path")
    buildParser.add_argument('-m', '--module', type = str, required = True, help = "Swift module search path.")
    buildParser.add_argument('--rebuild', action = 'store_true', help = "Rebuild all related projects, add this option if you did some changes to the related library")
    buildParser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase output verbosity")
    buildParser.set_defaults(func = buildProject)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    parseArgs()