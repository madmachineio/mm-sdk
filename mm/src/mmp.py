import platform
import toml, json
from zlib import crc32
from pathlib import Path
import util, log, version

SUPPORTED_ARCHS = [
    'thumbv7em-unknown-none-eabi',
    'thumbv7em-unknown-none-eabihf',
    'armv7em-none-none-eabi'
]

SUPPORTED_BOARDS = [
    'SwiftIOBoard',
    'SwiftIOMicro'
]

SWIFTIO_BOARD = {'vid': '0x1fc9',
                'pid': '0x0093',
                'serial_number': '012345671FC90093',
                'sd_image_name': 'swiftio.bin',
                'usb2serial_device': 'DAPLink CMSIS-DAP'}

SWIFTIO_MICRO = {'vid': '0x1fc9',
                'pid': '0x0095',
                'serial_number': '012345671FC90095',
                'sd_image_name': 'micro.img',
                'usb2serial_device': '/dev/ttyACM0' if platform.system() == 'Linux' else 'wch'}


DEFAULT_MMP_MANIFEST = """# This is a MadMachine project file in TOML format
# This file contains parameters that cannot be managed by SwiftPM
# Editing this file will alter the behavior of the build/download process
# Project files within dependent libraries will be IGNORED

# Specify the board name below
# Supported boards are listed as follows
# "SwiftIOBoard"
# "SwiftIOMicro"
board = "{name}"

# Specify the target triple below
# Supported architectures are listed as follows
# "thumbv7em-unknown-none-eabi"
# "thumbv7em-unknown-none-eabihf"
# "armv7em-none-none-eabi"
triple = "{triple}"

# Enable or disable hardware floating-point support below
# If your code involves significant floating-point calculations, please set it to 'true'
hard-float = {hard_float}

# Enable or disable float register below
# If your code involves significant floating-point calculations, please set it to 'true'
float-abi = {float_abi}

# Reserved for future use 
version = 1
"""

TOML_CONTENT = None

def initialize(content):
    global TOML_CONTENT

    try:
        TOML_CONTENT = toml.loads(content)
    except:
        log.die('decoding Package.mmp failed!')


def init_manifest(board, p_type, triple='armv7em-none-none-eabi', hard_float='true', float_abi='false'):    
    if p_type == 'library':
        board = ''

    if p_type != 'library' and SUPPORTED_BOARDS.count(board) == 0:
        log.die('Unknown board: ' + board)

    triple = triple.strip()
    if SUPPORTED_ARCHS.count(triple) == 0:
        log.die('Unknown triple: ' + triple)

    if triple.endswith('hf') and hard_float != 'true':
        log.die('The specified triple and hard-float settings are in conflict!')

    content = DEFAULT_MMP_MANIFEST.format(name=board, triple=triple, hard_float=hard_float, float_abi=float_abi)

    return content


def get_board_name():
    board = TOML_CONTENT.get('board').strip()

    if board is None:
        log.die('Unable to recognize the board type in Package.mmp!')

    return board


def get_triple():
    triple = TOML_CONTENT.get('triple').strip()
    hard_float = TOML_CONTENT.get('hard-float')

    if len(triple) == 0:
        log.die('The triple configuration is missing in Package.mmp!')

    if SUPPORTED_ARCHS.count(triple) == 0:
        log.die('Unknown triple: ' + triple)

    if triple.endswith('hf') and hard_float == False:
        log.die('The specified triple and hard-float settings are in conflict!')

    if triple.startswith('thumbv7em'):
        triple = 'armv7em-none-none-eabi'

    return triple


def get_float_type(wrn=False):
    hard_float = TOML_CONTENT.get('hard-float')
    float_abi = TOML_CONTENT.get('float-abi')

    if hard_float == False and float_abi == True:
        log.die('The specified float settings are in conflict!')

    if hard_float is None:
        if wrn:
            log.wrn('The hard-float setting is missing in Package.mmp, defualting to true!')
        hard_float = True

    if float_abi is None:
        if wrn:
            log.wrn('The float-abi setting is missing in Package.mmp, defualting to false!')
        float_abi = False

    return hard_float, float_abi


def get_board_info(info):
    board = TOML_CONTENT.get('board').strip()

    if board == 'SwiftIOBoard':
        dic = SWIFTIO_BOARD
    elif board == 'SwiftIOMicro':
        dic = SWIFTIO_MICRO
    else:
        log.die('Unknown board')
    
    return dic.get(info)


def get_c_arch():
    hard_float, float_abi = get_float_type()
    if hard_float == True:
        flags = [
            '-mcpu=cortex-m7',
            '-mhard-float',
        ]
    else:
        flags = [
            '-mcpu=cortex-m7+nofp',
            '-msoft-float',
        ]
    
    if float_abi == True:
        flags += ['-mfloat-abi=hard']
    else:
        flags += ['-mfloat-abi=soft']
    
    return flags


def get_c_predefined():
    flags = [
        '-nostdinc',
        '-Wno-unused-command-line-argument',
        '-D__MADMACHINE__'
    ]
    return flags


def get_gcc_include_path():
    sdk_path = util.get_sdk_path()

    flags = [
        #newlib header
        'usr/arm-none-eabi/include',

        #libstdc++ header
        #'usr/arm-none-eabi/include/c++/10.3.1',
        #'usr/arm-none-eabi/include/c++/10.3.1/arm-none-eabi/thumb' + sub_path,
        #'usr/arm-none-eabi/include/c++/10.3.1/backward',

        #libgcc header
        'usr/lib/gcc/arm-none-eabi/10.3.1/include',
        'usr/lib/gcc/arm-none-eabi/10.3.1/include-fixed',

        #clang compiler-rt header
        #'usr/lib/clang/17/include',
    ]

    flags = ['-I' + str(sdk_path / item) for item in flags] 
    return flags


def get_clang_include_path():
    sdk_path = util.get_sdk_path()

    flags = [
        #newlib header
        'usr/arm-none-eabi/include',

        #libstdc++ header
        #'usr/arm-none-eabi/include/c++/10.3.1',
        #'usr/arm-none-eabi/include/c++/10.3.1/arm-none-eabi/thumb' + sub_path,
        #'usr/arm-none-eabi/include/c++/10.3.1/backward',

        #libgcc header
        #'usr/lib/gcc/arm-none-eabi/10.3.1/include',
        #'usr/lib/gcc/arm-none-eabi/10.3.1/include-fixed',

        #clang compiler-rt header
        'usr/lib/clang/17/include',
    ]

    flags = ['-I' + str(sdk_path / item) for item in flags]
    return flags


def get_cc_flags(p_type):
    flags = []

    flags += get_c_arch()
    flags += get_c_predefined()

    #TODO, arm-2d needs the clang headers to be compiled!
    flags += get_gcc_include_path()
    #flags += get_clang_include_path()
    
    return flags


def get_swift_arch():
    triple = get_triple()
    hard_float, float_abi = get_float_type(True)

    flags = [
        '-target',
        triple
    ]

    if hard_float == True:
        flags += [
            '-target-cpu',
            'cortex-m7',
            '-Xcc',
            '-mhard-float',
        ]
    else:
        flags += [
            '-target-cpu',
            'cortex-m7+nofp',
            '-Xcc',
            '-msoft-float',
        ]

    if float_abi == True:
        flags += [
            '-Xcc',
            '-mfloat-abi=hard'
        ]
    else:
        flags += [
            '-Xcc',
            '-mfloat-abi=soft'
        ]

    return flags

def get_swift_predefined(p_type):
    flags = [
        #'-driver-print-jobs',
        '-Osize',
        '-wmo',
        '-enable-experimental-feature',
        'Embedded',
        '-Xfrontend',
        '-enable-experimental-feature',
        '-Xfrontend',
        'Extern',
        # '-Xfrontend',
        # '-disable-stack-protector',
        '-Xfrontend',
        '-gnone',
        '-Xfrontend',
        '-strict-concurrency=minimal',
        #'-static-stdlib',
        '-Xfrontend',
        '-function-sections',
        #'-Xfrontend',
        #'-data-sections',
        '-Xcc',
        '-D__MADMACHINE__',
        # '-Xfrontend',
        # '-disable-implicit-string-processing-module-import'
    ]

    # if p_type == 'executable':
    #     flags.append('-static-executable')
    # else:
    #     flags.append('-static')

    if p_type == 'executable':
        linker = '-use-ld=' + str(util.get_tool_path('ld'))
        flags += [
            # linker,
            # '-Xclang-linker',
            # '-fdriver-only',
            '-Xclang-linker',
            '-nostdlib',
            '-Xclang-linker',
            '-nostdlibinc',
            '-Xclang-linker',
            '-nostdinc',
            '-Xclang-linker',
            '-nostdinc++',
            '-Xclang-linker',
            '-nobuiltininc',
        ]

    board = get_board_name()
    if len(board) != 0:
        flags.append('-D' + board.upper())
    elif p_type == 'executable':
        log.die('The board is missing in Package.mmp')

    return flags


def get_swift_library():
    sdk_path = util.get_sdk_path()

    flags = [
        'lib/swift'
    ]

    flags = ['-I ' + str(sdk_path / item) for item in flags]
    flags = (' '.join(flags)).split(' ')

    #flags = ['-Xfrontend ' + item for item in flags]
    #flags = (' '.join(flags)).split(' ')

    return flags

def get_swift_gcc_header():
    #Used for newlib constants like errno.h

    sdk_path = util.get_sdk_path()

    flags = [
        #newlib header
        'usr/arm-none-eabi/include',

        #libstdc++ header
        #'usr/arm-none-eabi/include/c++/10.3.1',
        #'usr/arm-none-eabi/include/c++/10.3.1/arm-none-eabi/thumb' + sub_path,
        #'usr/arm-none-eabi/include/c++/10.3.1/backward',

        #libgcc header
        'usr/lib/gcc/arm-none-eabi/10.3.1/include',
        'usr/lib/gcc/arm-none-eabi/10.3.1/include-fixed',

        #clang compiler-rt header
        #'usr/lib/clang/17/include',
    ]

    flags = ['-I ' + str(sdk_path / item) for item in flags]
    flags = (' '.join(flags)).split(' ')

    flags = ['-Xcc ' + item for item in flags]
    flags = (' '.join(flags)).split(' ')
    return flags

def get_swift_clang_header():
    #Used for newlib constants like errno.h
    sdk_path = util.get_sdk_path()

    flags = [
        #newlib header
        'usr/arm-none-eabi/include',

        #libstdc++ header
        #'usr/arm-none-eabi/include/c++/10.3.1',
        #'usr/arm-none-eabi/include/c++/10.3.1/arm-none-eabi/thumb' + sub_path,
        #'usr/arm-none-eabi/include/c++/10.3.1/backward',

        #libgcc header
        #'usr/lib/gcc/arm-none-eabi/10.3.1/include',
        #'usr/lib/gcc/arm-none-eabi/10.3.1/include-fixed',

        #clang compiler-rt header
        #'usr/lib/clang/17/include',
    ]

    flags = ['-I ' + str(sdk_path / item) for item in flags]
    flags = (' '.join(flags)).split(' ')

    flags = ['-Xcc ' + item for item in flags]
    flags = (' '.join(flags)).split(' ')
    return flags


def get_swiftc_flags(p_type):
    flags = []

    flags += get_swift_arch()
    flags += get_swift_predefined(p_type)
    flags += get_swift_library()

    #TODO, arm-2d needs the clang headers to be compiled!
    flags += get_swift_gcc_header()
    #flags += get_swift_clang_header()

    return flags


def get_linker_config(build_path, p_name):
    map_path = str(str(build_path) + '/' + p_name + '.map')

    flags = [
        '-z',
        'muldefs',
        '-u,_OffsetAbsSyms',
        '-u,_ConfigAbsSyms',
        '-X',
        '-N',
        '--gc-sections',
        '--build-id=none',
        '--sort-common=descending',
        '--sort-section=alignment',
        #'--no-enum-size-warning',
        '--print-memory-usage',
        # '-Map',
        #  map_path
    ]
    #flags = ['-Xlinker ' + item for item in flags]
    #flags = (' '.join(flags)).split(' ')

    return flags

def get_linker_script():
    board = get_board_name()
    sdk_path = util.get_sdk_path()

    flags = [
        '-T',
        str(sdk_path / 'boards' / board / 'linker/sdram.ld')
    ]
    #flags = ['-Xlinker ' + item for item in flags]
    #flags = (' '.join(flags)).split(' ')

    return flags

def get_linker_search_path():
    sdk_path = util.get_sdk_path()
    hard_float, float_abi = get_float_type()

    if hard_float == True:
        if float_abi == True:
            sub_path = 'v7e-m+dp/hard'
        else:
            sub_path = 'v7e-m+dp/softfp'
    else:
        sub_path = 'v7e-m/nofp'
    
    flags = [
        'usr/lib/gcc/arm-none-eabi/10.3.1/thumb/' + sub_path,
        'usr/arm-none-eabi/lib/thumb/' + sub_path
    ]
    flags = ['-L' + str(sdk_path / item) for item in flags]
    flags = [item for item in flags]
    #flags = ['-Xlinker ' + item for item in flags]
    #flags = (' '.join(flags)).split(' ')

    return flags

def get_linker_board_library():
    sdk_path = util.get_sdk_path()
    board = get_board_name()
    hard_float, float_abi = get_float_type()

    if hard_float == True:
        if float_abi == True:
            sub_path = 'hard'
        else:
            sub_path = 'softfp'
    else:
        sub_path = 'nofp'

    libraries = ['--whole-archive']
    libraries += sorted((sdk_path / 'boards' / board / 'lib/thumbv7em' / sub_path / 'whole').glob('[a-z]*.obj'))
    libraries += sorted((sdk_path / 'boards' / board / 'lib/thumbv7em' / sub_path / 'whole').glob('[a-z]*.a'))

    libraries.append('--no-whole-archive')
    libraries += sorted((sdk_path / 'boards' / board / 'lib/thumbv7em' / sub_path / 'nowhole').glob('[a-z]*.obj'))
    libraries += sorted((sdk_path / 'boards' / board / 'lib/thumbv7em' / sub_path / 'nowhole').glob('[a-z]*.a'))

    flags = [str(item) for item in libraries]
    #flags = ['-Xlinker ' + str(item) for item in libraries]
    #flags = (' '.join(flags)).split(' ')

    #flags += ['-lswiftCore']

    return flags


def get_linker_library():
    sdk_path = util.get_sdk_path()
    swift_path = util.get_swift_path()
    triple = get_triple()
    hard_float, float_abi = get_float_type()
    
    if hard_float == True:
        if float_abi == True:
            sub_path = 'hard'
        else:
            sub_path = 'softfp'
    else:
        sub_path = 'nofp'

    libraries = sorted((sdk_path / 'lib/thumbv7em' / sub_path).glob('[a-z]*.a'))
    libraries.append('--whole-archive')
    libraries += sorted((swift_path / 'usr/lib/swift/embedded' / triple).glob('[a-z]*.a'))
    libraries.append('--no-whole-archive')

    flags = [str(item) for item in libraries]

    return flags


def get_linker_gcc_library():
    libraries = [
        '--start-group',
        '-lstdc++',
        '-lc',
        '-lg',
        '-lm',
        '-lgcc',
        '--end-group'
    ]

    flags = [str(item) for item in libraries]
    #flags = ['-Xlinker ' + str(item) for item in libraries]
    #flags = (' '.join(flags)).split(' ')

    return flags


def get_linker_flags(build_path, p_type, p_name):
    flags = []

    if p_type == 'executable':
        flags += get_linker_config(build_path, p_name)
        flags += get_linker_script()
        flags += get_linker_search_path()
        flags += get_linker_board_library()
        flags += get_linker_library()
        flags += get_linker_gcc_library()
    
    return flags


def get_destination(build_path, p_type, p_name):
    swift_root = str(util.get_swift_path())
    swift_bin = str(util.get_swift_path() / 'usr/bin')
    triple = get_triple()
    cc_flags = get_cc_flags(p_type)
    swiftc_flags = get_swiftc_flags(p_type)
    linker_flags = get_linker_flags(build_path, p_type, p_name)
    
    destination_dic = {
        'version': 2,
        'sdkRootDir': swift_root,
        'toolchainBinDir': swift_bin,
        'hostTriples': [],
        'targetTriples': [triple],
        'extraCCFlags': cc_flags,
        'extraCXXFlags': cc_flags,
        'extraSwiftCFlags': swiftc_flags,
        'extraLinkerFlags': linker_flags
    }

    js_text = json.dumps(destination_dic, indent = 4)

    return js_text


def create_destination(p_path, build_path, p_type, p_name):
    js_text = get_destination(build_path=build_path, p_type=p_type, p_name=p_name)
    (p_path / '.build').mkdir(exist_ok=True)
    destination = p_path / '.build/destination.json'
    destination.write_text(js_text, encoding='UTF-8')

    return destination


def get_sdk_info(name):
    sdk_version = version.__VERSION__

    info_dic = {
        'schemaVersion': '1.0',
        'artifacts': {
            name: {
                'variants': [
                    {
                        'path': name
                    }
                ],
                'type': 'swiftSDK',
                'version': sdk_version
            }
        }
    }

    js_text = json.dumps(info_dic, indent=2)
    log.dbg(js_text)

    return js_text

def get_swift_sdk():
    triple = get_triple()
    sdk_root = str(util.get_sdk_path())
    swift_lib_path = str(util.get_swift_path() / 'usr/lib/swift')
    swift_static_lib_path = str(util.get_swift_path() / 'usr/lib/swift_static')

    swift_sdk_dic = {
        'schemaVersion': '4.0',
        'targetTriples': {
            triple: {
                'sdkRootPath': sdk_root,
                'toolsetPaths': [
                    'toolset.json'
                ],
                'swiftResourcesPath': swift_lib_path,
                'swiftStaticResourcesPath': swift_static_lib_path
            }
        }
    }

    js_text = json.dumps(swift_sdk_dic, indent=2)
    log.dbg(js_text)

    return js_text


def get_toolset(build_path, p_type, p_name):
    cc_flags = get_cc_flags(p_type)
    swiftc_flags = get_swiftc_flags(p_type)
    linker_flags = get_linker_flags(build_path, p_type, p_name)
    linker_path = str(util.get_tool_path('ld'))

    toolset_dic = ''

    if p_type == 'executable':
        toolset_dic = {
            'schemaVersion': '1.0',
            'swiftCompiler': {
                'extraCLIOptions': swiftc_flags
            },
            'cCompiler': {
                'extraCLIOptions': cc_flags
            },
            'linker': {
                'path': linker_path,
                'extraCLIOptions': linker_flags
            }
        }
    else:
        toolset_dic = {
            'schemaVersion': '1.0',
            'swiftCompiler': {
                'extraCLIOptions': swiftc_flags
            },
            'cCompiler': {
                'extraCLIOptions': cc_flags
            }
        }

    js_text = json.dumps(toolset_dic, indent = 2)
    log.dbg(js_text)

    return js_text


def create_temp_sdk_des(p_path, build_path, p_type, p_name):
    (p_path / '.build' / util.ARTIFACT_PATH  / util.SDK_ID).mkdir(parents=True, exist_ok=True)
    info_path = p_path / '.build' / util.ARTIFACT_PATH / 'info.json'
    swift_sdk_path = p_path / '.build' / util.ARTIFACT_PATH  / util.SDK_ID / 'swift-sdk.json'
    toolset_path = p_path / '.build' / util.ARTIFACT_PATH  / util.SDK_ID / 'toolset.json'

    info_text = get_sdk_info(name=util.SDK_ID)
    swift_sdk_text = get_swift_sdk()
    toolset_text = get_toolset(build_path=build_path, p_type=p_type, p_name=p_name)

    info_path.write_text(info_text, encoding='UTF-8')
    swift_sdk_path.write_text(swift_sdk_text, encoding='UTF-8')
    toolset_path.write_text(toolset_text, encoding='UTF-8')


def clean(p_path):
    files = sorted((p_path / '.build' / 'release').glob('*.bin'))
    for file in files:
        file.unlink()

    files = sorted((p_path / '.build' / 'release').glob('*.img'))
    for file in files:
        file.unlink()


def create_binary(build_path, name):
    elf_path = build_path / name
    bin_path = build_path / (name + '.bin')

    flags = [
        util.get_tool('objcopy'),
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
        util.quote_string(elf_path),
        util.quote_string(bin_path)
    ]
    
    if util.command(flags):
        log.die('creating binary failed!')
    else:
        return bin_path