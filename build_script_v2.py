#!/user/bin/python3

import os, sys
import errno
import argparse
import subprocess
import struct
from zlib import crc32


projectPath = ''
buildPath = ''

sdkPath = ''
toolsBase = ''
projectName = ''
srcPaths = []
searchPaths = []
cHeader = ''
verbose = False



def suffix(file, *suffixName):  
    array = map(file.endswith, suffixName)  
    if True in array :  
        return True  
    else :  
        return False  

def deleteFiles(targetPath, *suffixName):  
    files = os.listdir(targetPath)
    for file in files:  
        targetFile = os.path.join(targetPath, file)  
        if suffix(file, suffixName):  
            os.remove(targetFile)

def getFiles(targetPath, suffixName):
    files = os.listdir(targetPath)
    targetFiles = []
    for file in files:
        if suffix(file, suffixName):
            targetFiles.append(file)
    targetFiles.sort()
    targetFiles = list(map(lambda item: os.path.join(targetPath, item), targetFiles))
    return targetFiles

def initBuildPath(targetPath, delete):
    buildPath = os.path.join(targetPath, '.build')
    if not os.path.exists(buildPath):
        try:
            os.mkdir(buildPath)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    if delete == True:
        deleteFiles(buildPath, '.bin', '.elf', '.map', '.a', '.o', '.obj', '.c', '.swiftmodule', '.swiftdoc')

    return buildPath


def getSDKTool(tool):
    value = ''
    if tool == 'swiftc':
        value = toolsBase + 'toolchains/swift/bin/swiftc'
    elif tool == 'stdPath':
        value = toolsBase + 'toolchains/swift/lib/swift/zephyr/thumbv7em'
    elif tool == 'ar':
        value = toolsBase + 'toolchains/gcc/bin/arm-none-eabi-ar'
    elif tool == 'gcc':
        value = toolsBase + 'toolchains/gcc/bin/arm-none-eabi-gcc'
    elif tool == 'gpp':
        value = toolsBase + 'toolchains/gcc/bin/arm-none-eabi-g++'
    elif tool == 'objcopy':
        value = toolsBase + 'toolchains/gcc/bin/arm-none-eabi-objcopy'
    elif tool == 'gen_isr_tables':
        value = toolsBase + 'scripts/dist/gen_isr_tables/gen_isr_tables'
    return value






def initArgs():
    global projectPath
    global buildPath
    global sdkPath
    global toolsBase
    global projectName
    global srcPaths
    global searchPaths
    global cHeader 
    global verbose


    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--type", type = str, choices = ['exe', 'lib'], default = 'exe', help = "Compile type, default type is exe")
    parser.add_argument("-n", "--name", type = str, required = True, help = "Project name")
    parser.add_argument("--sdk", type = str, required = True, help = "SDK path")
    parser.add_argument("--src", type = str, required = True, action = 'append', help = "Swift source path")
    parser.add_argument("--module", type = str, action = 'append', help = "Swift module(library) search path")
    parser.add_argument("--header", type = str, help = "C header file")
    parser.add_argument("-v", "--verbose", action = 'store_true', help = "Increase output verbosity")
    args = parser.parse_args()

    projectPath = os.path.abspath('.')
    buildPath = initBuildPath(projectPath, True)

    projectName = args.name
    sdkPath = os.path.abspath(args.sdk)

    if sys.platform.startswith('darwin'):
        toolsBase = 'tools_mac/'
    elif sys.platform.startswith('win'):
        toolsBase = 'tools_win/'
    elif sys.platform.startswith('linux'):
        toolsBase = 'tools_linux/'

    if args.header:
        cHeader = os.path.abspath(args.header)

    for item in args.src:
        srcPaths.append(os.path.abspath(item))

    if args.module:
        for item in args.module:
            searchPaths.append(os.path.abspath(item))

    if args.verbose:
        verbose = True

    stdPath = os.path.join(sdkPath, getSDKTool('stdPath'))
    searchPaths.append(stdPath)

    '''
    if verbose:
        print("Compile type:", args.type)
        print("Project name:", projectName)
        print("Build path:", buildPath)
        print("SDK path:", sdkPath)
        print("Source paths:", srcPaths)
        print("Search paths:", searchPaths)
        if cHeader:
            print("C header:", cHeader)
    '''

    return args

def generateBin(targetPath, name):
    cmd = os.path.join(sdkPath, getSDKTool('objcopy'))

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

    flags.append(os.path.join(targetPath, name + '.elf'))
    flags.append(os.path.join(targetPath, name + '.bin'))

    for item in flags:
        cmd += ' ' + item

    os.chdir(targetPath)
    if verbose:
        print(cmd)
    p = subprocess.Popen(cmd, shell = True)
    p.wait()
    return p.poll()


def generateIsrTable(targetPath, name):
    cmd = os.path.join(sdkPath, getSDKTool('gen_isr_tables'))

    flags = [
        '--output-source',
        'isr_tables.c',
        '--kernel ' + os.path.join(targetPath, name + '_prebuilt.elf'),
        '--intlist',
        'isrList.bin',
        '--sw-isr-table',
        '--vector-table'
    ]

    for item in flags:
        cmd += ' ' + item

    os.chdir(targetPath)
    if verbose:
        print(cmd)
    p = subprocess.Popen(cmd, shell = True)
    p.wait()
    return p.poll()

def generateIsr(targetPath, name):
    cmd = os.path.join(sdkPath, getSDKTool('objcopy'))

    flags = [
        '-I elf32-littlearm',
        '-O binary',
        '--only-section=.intList',
        os.path.join(targetPath, name + '_prebuilt.elf'),
        'isrList.bin'
    ]


    for item in flags:
        cmd += ' ' + item

    os.chdir(targetPath)
    if verbose:
        print(cmd)
    p = subprocess.Popen(cmd, shell = True)
    p.wait()
    return p.poll()

def compileIsr(targetPath):
    cmd = os.path.join(sdkPath, getSDKTool('gcc'))

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
        flags.append('-I' + os.path.join(sdkPath, item))
    
    flags.append('-isystem ' + os.path.join(sdkPath, toolsBase + 'toolchains/gcc/arm-none-eabi/include'))
    flags.append('-imacros ' + os.path.join(sdkPath, 'hal/HalSwiftIOBoard/generated/autoconf.h'))
    flags.append('-o ' + os.path.join(targetPath, 'isr_tables.c.obj'))
    flags.append('-c ' + os.path.join(targetPath, 'isr_tables.c'))

    for item in flags:
        cmd += ' ' + item

    os.chdir(targetPath)
    if verbose:
        print(cmd)
    p = subprocess.Popen(cmd, shell = True)
    p.wait()
    return p.poll()


def linkELF(targetPath, name, step):
    cmd = os.path.join(sdkPath, getSDKTool('gpp'))

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
        #'-Wl,-Map=' + buildFolder + '/' + projectName + '.map',
        #halPath + '/generated/empty_file.c.obj'
    ]

    if step == 'step2':
        mapTarget = os.path.join(targetPath, projectName + '.map')
        flags.append('-Wl,-Map=' + mapTarget)
        flags.append('-Wl,--print-memory-usage')
        linkScript = os.path.join(sdkPath, 'hal/HalSwiftIOBoard/generated/linker_pass_final.cmd')
        flags.append('-Wl,-T ' + linkScript)
        flags.append(os.path.join(targetPath, 'isr_tables.c.obj'))
    elif step == 'step1':
        linkScript = os.path.join(sdkPath, 'hal/HalSwiftIOBoard/generated/linker.cmd')
        flags.append('-Wl,-T ' + linkScript)  
        flags.append(os.path.join(sdkPath, 'hal/HalSwiftIOBoard/generated/empty_file.c.obj'))
    
    flags.append('-L' + os.path.join(sdkPath, toolsBase + 'toolchains/gcc/arm-none-eabi/lib/thumb/v7e-m'))
    flags.append('-L' + os.path.join(sdkPath, toolsBase + 'toolchains/gcc/lib/gcc/arm-none-eabi/7.3.1/thumb/v7e-m'))

    flags.append('-Wl,--whole-archive')
    flags.append(os.path.join(sdkPath, toolsBase + 'toolchains/swift/lib/swift/zephyr/thumbv7em/swiftrt.o'))
    flags.append(os.path.join(targetPath, 'lib' + projectName + '.a'))

    library = getFiles(os.path.join(sdkPath, 'hal/HalSwiftIOBoard/generated/whole'), '.a')
    for file in library:
        flags.append(file)

    flags.append('-Wl,--no-whole-archive')

    if step == 'step1':
        #searchPaths.append(targetPath)
        searchPaths.append(os.path.join(sdkPath, 'hal/HalSwiftIOBoard/generated/no_whole'))


    flags.append('-Wl,--start-group')
    for item in reversed(searchPaths):
        files = getFiles(item, '.a')
        for file in files:
            flags.append(file)

    
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
        flags.append(os.path.join(targetPath, projectName + '_prebuilt.elf'))
    elif step == 'step2':
        flags.append(os.path.join(targetPath, projectName + '.elf'))

    for item in flags:
        cmd += ' ' + item

    os.chdir(targetPath)
    if verbose:
        print(cmd)
    p = subprocess.Popen(cmd, shell = True)
    p.wait()
    return p.poll()



def mergeObjects(targetPath, libName):
    cmd = os.path.join(sdkPath, getSDKTool('ar'))

    arFlags = [
        '-rcs'
    ]

    targetName = os.path.join(targetPath, 'lib' + libName + '.a')
    arFlags.append(targetName)

    files = getFiles(targetPath, '.o')
    for file in files:
        arFlags.append(file)

    for item in arFlags:
        cmd += ' ' + item

    os.chdir(targetPath)
    if verbose:
        print(cmd)
    p = subprocess.Popen(cmd, shell = True)
    p.wait()
    return p.poll()


def compileWithSwiftIOModule(targetPath):
    swiftio = os.path.join(sdkPath, 'lib/SwiftIO')
    #srcPaths.append(swiftio)
    searchPaths.append(swiftio)
    return swiftCompile(buildPath, 'exe')


def swiftCompile(targetPath, target):
    cmd = os.path.join(sdkPath, getSDKTool('swiftc'))

    swiftFlags = [
        '-module-name ' + projectName,
        '-target thumbv7em-none--eabi',
        '-target-cpu cortex-m7',
        '-target-fpu fpv5-dp-d16',
        '-float-abi soft',
        #'-parse-as-library',
        '-O',
        '-static-stdlib',
        '-function-sections',
        '-data-sections',
        '-Xcc -D__ZEPHYR__',
        '-Xfrontend -assume-single-threaded',
        '-no-link-objc-runtime'
    ]



    if target == 'module':
        swiftFlags.insert(0, '-parse-as-library')
        swiftFlags.insert(0, '-emit-module')
    elif target == 'object':
        swiftFlags.insert(0, '-parse-as-library')
        swiftFlags.insert(0, '-c')
    elif target == 'exe':
        swiftFlags.insert(0, '-c')
    else:
        os._exit(-1)

    if cHeader: 
        swiftFlags.append('-import-objc-header ' + cHeader)
    
    for item in searchPaths:
        swiftFlags.append('-I ' + item)

    for item in srcPaths:
        files = getFiles(item, '.swift')
        for file in files:
            swiftFlags.append(file)

    for item in swiftFlags:
        cmd += ' ' + item

    os.chdir(targetPath)
    if verbose:
        print(cmd)
    p = subprocess.Popen(cmd, shell = True)
    p.wait()
    return p.poll()




def getCrc32(fileName): 
    with open(fileName, 'rb') as f:
        return crc32(f.read())

def int32_to_int8(n):
    mask = (1 << 8) - 1
    return [(n >> k) & mask for k in range(0, 32, 8)]

def addCrcToBin(targetPath, name):
    fileName = os.path.join(targetPath, name + '.bin')
    value = getCrc32(fileName)
    list_dec = int32_to_int8(value)

    targetFile = os.path.join(targetPath, 'swiftio.bin')

    os.chdir(targetPath)
    with open(fileName, 'rb') as f0:
        with open(targetFile, 'wb') as f1:
            f1.write(f0.read())
            for x in list_dec:
                a = struct.pack('B', x)
                f1.write(a)



if __name__ == '__main__':
    args = initArgs()

    if args.type == 'lib':
        if swiftCompile(buildPath, 'module'):
            os._exit(-1)
        if swiftCompile(buildPath, 'object'):
            os._exit(-1)
        if  mergeObjects(buildPath, projectName):
            os._exit(-1)
    elif args.type == 'exe':
        if compileWithSwiftIOModule(buildPath):
            os._exit(-1)
        if mergeObjects(buildPath, projectName):
            os._exit(-1)
        if linkELF(buildPath, projectName, 'step1'):
            os._exit(-1)
        if generateIsr(buildPath, projectName):
            os._exit(-1)
        if generateIsrTable(buildPath, projectName):
            os._exit(-1)
        if compileIsr(buildPath):
            os._exit(-1)
        if linkELF(buildPath, projectName, 'step2'):
            os._exit(-1)
        if generateBin(buildPath, projectName):
            os._exit(-1)
        if addCrcToBin(buildPath, projectName):
            os._exit(-1)

    

    if verbose:
        print("Compile type:", args.type)
        print("Project name:", projectName)
        print("Build path:", buildPath)
        print("SDK path:", sdkPath)
        print("Source paths:", srcPaths)
        print("Module(library) search paths:", searchPaths)
        if cHeader:
            print("C header:", cHeader)    









