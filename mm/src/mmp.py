import toml, json
from zlib import crc32
from pathlib import Path
import util, log

SWIFTIO_BOARD = {'vid': '0x1fc9',
                'pid': '0x0093',
                'serial_number': '012345671FC90093',
                'sd_image_name': 'swiftio.bin',
                'usb2serial_device': 'DAPLink CMSIS-DAP'}

SWIFTIO_FEATHER = {'vid': '0x1fc9',
                    'pid': '0x0095',
                    'serial_number': '012345671FC90095',
                    'sd_image_name': 'feather.img',
                    'usb2serial_device': 'CP21'}


DEFAULT_MMP_MANIFEST = """# This is a MadMachine project file in TOML format
# This file holds those parameters that could not be managed by SwiftPM
# Edit this file would change the behavior of the building/downloading procedure
# Those project files in the dependent libraries would be IGNORED

# Specify the board name below
# There are "SwiftIOBoard" and "SwiftIOFeather" now
board = "{name}"

# Specifiy the target triple below
# There are "thumbv7em-unknown-none-eabi" and "thumbv7em-unknown-none-eabihf" now
# If your code use significant floating-point calculation,
# plz set it to "thumbv7em-unknown-none-eabihf"
triple = "{triple}"

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
    


def init_manifest(board, p_type, triple='thumbv7em-unknown-none-eabi'):    
    if p_type == 'library':
        board = ''

    content = DEFAULT_MMP_MANIFEST.format(name=board, triple=triple)
    return content


def get_board_name():
    board = TOML_CONTENT.get('board')

    if board is None:
        log.die('board is missing in Package.mmp')

    return board.strip()


def get_triple():
    triple = TOML_CONTENT.get('triple')

    if triple is None:
        float_type= TOML_CONTENT.get('float-type')
        if float_type == 'hard':
            triple = 'thumbv7em-unknown-none-eabihf'
        elif float_type == 'soft':
            triple = 'thumbv7em-unknown-none-eabi'
        else:
            log.die('unknown float-type')
    
    triple = triple.strip()

    if len(triple) == 0:
        log.die('missing triple config in Package.mmp')

    if (triple != 'thumbv7em-unknown-none-eabi') and (triple != 'thumbv7em-unknown-none-eabihf'):
        log.die('unknown triple: ' + triple)

    return triple

def get_board_info(info):
    board = TOML_CONTENT.get('board')
    if board == 'SwiftIOBoard':
        dic = SWIFTIO_BOARD
    elif board == 'SwiftIOFeather':
        dic = SWIFTIO_FEATHER
    else:
        log.die('unknown board')
    
    return dic.get(info)


def get_c_arch():
    triple = get_triple()
    if triple == 'thumbv7em-unknown-none-eabihf':
        flags = [
            '-mcpu=cortex-m7',
            '-mhard-float',
            '-mfloat-abi=hard'
        ]
    else:
        flags = [
            '-mcpu=cortex-m7+nofp',
            '-msoft-float',
            '-mfloat-abi=soft'
        ]
    
    return flags

def get_c_predefined():
    flags = [
        '-nostdinc',
        '--rtlib=libgcc',
        '-Wno-unused-command-line-argument',
        '-D__MADMACHINE__',
        '-D_POSIX_THREADS',
        '-D_POSIX_READER_WRITER_LOCKS',
        '-D_UNIX98_THREAD_MUTEX_ATTRIBUTES'
    ]
    return flags

def get_gcc_include_path():
    triple = get_triple()
    sdk_path = util.get_sdk_path()

    if triple == 'thumbv7em-unknown-none-eabihf':
        sub_path = '/v7e-m+dp/hard'
    else:
        sub_path = '/v7e-m/nofp'

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
        #'usr/lib/clang/13.0.0/include',
    ]

    flags = ['-I' + str(sdk_path / item) for item in flags] 
    return flags

def get_clang_include_path():
    triple = get_triple()
    sdk_path = util.get_sdk_path()

    if triple == 'thumbv7em-unknown-none-eabihf':
        sub_path = '/v7e-m+dp/hard'
    else:
        sub_path = '/v7e-m/nofp'

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
        'usr/lib/clang/13.0.0/include',
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
    if triple == 'thumbv7em-unknown-none-eabihf':
        flags = [
            '-target',
            'thumbv7em-unknown-none-eabihf',
            '-target-cpu',
            'cortex-m7',
            '-Xcc',
            '-mhard-float',
            '-Xcc',
            '-mfloat-abi=hard'
        ]
    else:
        flags = [
            '-target',
            'thumbv7em-unknown-none-eabi',
            '-target-cpu',
            'cortex-m7+nofp',
            '-Xcc',
            '-msoft-float',
            '-Xcc',
            '-mfloat-abi=soft'
        ]
    
    return flags

def get_swift_predefined(p_type):
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

    if p_type == 'executable':
        flags.append('-static-executable')
    else:
        flags.append('-static')


    board = get_board_name()
    if len(board) != 0:
        flags.append('-D' + board.upper())
    elif p_type == 'executable':
        log.wrn('board is missing in Package.mmp')

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
        #'usr/lib/clang/13.0.0/include',
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
        'usr/lib/clang/13.0.0/include',
    ]

    flags = ['-I ' + str(sdk_path / item) for item in flags]
    flags = (' '.join(flags)).split(' ')

    flags = ['-Xcc ' + item for item in flags]
    flags = (' '.join(flags)).split(' ')
    return flags

def get_swift_linker_config(path, p_name):
    map_path = str(path) + '/' + p_name + '.map'

    flags = [
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
        '-Map',
         map_path
    ]
    flags = ['-Xlinker ' + item for item in flags]
    flags = (' '.join(flags)).split(' ')

    return flags

def get_swift_linker_script():
    board = get_board_name()
    sdk_path = util.get_sdk_path()

    flags = [
        '-T',
        str(sdk_path / 'Boards' / board / 'linker/sdram.ld')
    ]
    flags = ['-Xlinker ' + item for item in flags]
    flags = (' '.join(flags)).split(' ')

    return flags

def get_swift_link_search_path():
    sdk_path = util.get_sdk_path()
    triple = get_triple()
    if triple == 'thumbv7em-unknown-none-eabihf':
        sub_path = '/v7e-m+dp/hard'
    else:
        sub_path = '/v7e-m/nofp'
    
    flags = [
        'usr/lib/gcc/arm-none-eabi/10.3.1/thumb' + sub_path,
        'usr/arm-none-eabi/lib/thumb' + sub_path
    ]
    flags = ['-L' + str(sdk_path / item) for item in flags]

    return flags

def get_swift_board_library():
    sdk_path = util.get_sdk_path()
    board = get_board_name()
    triple = get_triple()
    if triple == 'thumbv7em-unknown-none-eabihf':
        sub_path = 'eabihf'
    else:
        sub_path = 'eabi'

    libraries = ['--whole-archive']
    libraries += sorted((sdk_path / 'Boards' / board / 'lib/thumbv7em' / sub_path / 'whole').glob('[a-z]*.obj'))
    libraries += sorted((sdk_path / 'Boards' / board / 'lib/thumbv7em' / sub_path / 'whole').glob('[a-z]*.a'))

    libraries.append('--no-whole-archive')
    libraries += sorted((sdk_path / 'Boards' / board / 'lib/thumbv7em' / sub_path / 'nowhole').glob('[a-z]*.obj'))
    libraries += sorted((sdk_path / 'Boards' / board / 'lib/thumbv7em' / sub_path / 'nowhole').glob('[a-z]*.a'))

    flags = ['-Xlinker ' + str(item) for item in libraries]
    flags = (' '.join(flags)).split(' ')

    #flags += ['-lswiftCore']

    return flags


def get_swift_gcc_library():
    libraries = [
        '--start-group',
        '-lstdc++',
        '-lc',
        '-lg',
        '-lm',
        '-lgcc',
        '--end-group'
    ]

    flags = ['-Xlinker ' + str(item) for item in libraries]
    flags = (' '.join(flags)).split(' ')

    return flags

def get_swiftc_flags(p_type, path, p_name):
    flags = []

    flags += get_swift_arch()
    flags += get_swift_predefined(p_type)
    
    #TODO, arm-2d needs the clang headers to be compiled!
    flags += get_swift_gcc_header()
    #flags += get_swift_clang_header()

    # Need to add '-nostdlib++' in static-executable-args.lnk
    # Or '-lclang_rt.builtins-thumbv7em' will be insearted into link command
    if p_type == 'executable':
        flags += get_swift_linker_config(path, p_name)
        flags += get_swift_linker_script()
        flags += get_swift_link_search_path()
        flags += get_swift_board_library()
        flags += get_swift_gcc_library()


    return flags

def get_destination(p_type, path, p_name):
    cc_flags = get_cc_flags(p_type)
    swiftc_flags = get_swiftc_flags(p_type, path, p_name)
    sdk = str(util.get_sdk_path())
    target = get_triple()
    bin_dir = str(util.get_bin_path())

    destination_dic = {
        'extra-cc-flags': cc_flags,
        'extra-cpp-flags': cc_flags,
        'extra-swiftc-flags': swiftc_flags,
        'sdk': sdk,
        'target': target,
        'toolchain-bin-dir': bin_dir,
        'version': 1
    }

    js_text = json.dumps(destination_dic, indent = 4)

    return js_text

def clean(p_path):
    #triple = get_triple()
    files = sorted((p_path / '.build' / 'release').glob('*.bin'))
    for file in files:
        file.unlink()

def create_binary(path, name):
    elf_path = path / name
    bin_path = path / (name + '.bin')

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