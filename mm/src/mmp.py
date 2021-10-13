import toml, json
import struct
from zlib import crc32
from pathlib import Path
import util, log

SWIFTIO_BOARD = {'vid': '0x1fc9',
                'pid': '0x0093',
                'serial_number': '012345671FC90093',
                'target_file': 'swiftio.bin'}

SWIFTIO_FEATHER = {'vid': '0x1fc9',
                    'pid': '0x0095',
                    'serial_number': '012345671FC90095',
                    'target_file': 'feather.bin'}


DEFAULT_MMP_MANIFEST = """# This is a MadMachine project file in TOML format
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

TOML_CONTENT = None

def initialize(content):
    global TOML_CONTENT

    try:
        TOML_CONTENT = toml.loads(content)
    except:
        log.die('decoding Package.mmp failed!')
    


def init_manifest(board, p_type):
    if board is None and p_type == 'executable':
        log.die('board name is required to initialize an executable')
    
    if p_type == 'library':
        board = ''

    content = DEFAULT_MMP_MANIFEST.format(name=board, float='soft')
    return content


def get_board_name():
    board = TOML_CONTENT.get('board')
    if board is None:
        log.wrn('board is missing in Package.mmp')
    return board

def get_board_info(name, info):
    if name == 'SwiftIOBoard':
        board = SWIFTIO_BOARD
    else:
        board = SWIFTIO_FEATHER
    
    return board.get(info)

def get_triple():
    float_type = TOML_CONTENT.get('float-type')

    if float_type == 'soft':
        triple = 'thumbv7em-unknown-none-eabi'
    elif float_type == 'hard':
        triple = 'thumbv7em-unknown-none-eabihf'
    else:
        log.die('missing float-type config in Package.mmp')
    
    return triple

def get_c_arch():
    triple = get_triple()
    if triple == 'thumbv7em-unknown-none-eabihf':
        flags = [
            '-mcpu=cortex-m7',
            '-mfloat-abi=hard'
        ]
    else:
        flags = [
            '-mcpu=cortex-m7+nofp',
            '-mfloat-abi=soft'
        ]
    
    return flags

def get_c_predefined():
    flags = [
        '-nostdinc',
        '-D__MADMACHINE__',
        '-D_POSIX_THREADS',
        '-D_POSIX_READER_WRITER_LOCKS',
        '-D_UNIX98_THREAD_MUTEX_ATTRIBUTES'
    ]
    return flags

def get_c_include_path():
    triple = get_triple()
    sdk_path = util.get_sdk_path()

    if triple == 'thumbv7em-unknown-none-eabihf':
        sub_path = '/v7e-m+dp/hard'
    else:
        sub_path = '/v7e-m/nofp'

    flags = [
        'usr/arm-none-eabi/include/c++/10.3.1',
        'usr/arm-none-eabi/include/c++/10.3.1/arm-none-eabi/thumb' + sub_path,
        'usr/arm-none-eabi/include/c++/10.3.1/backward',
        'usr/lib/gcc/arm-none-eabi/10.3.1/include',
        'usr/lib/gcc/arm-none-eabi/10.3.1/include-fixed',
        'usr/arm-none-eabi/include',
    ]

    flags = ['-I' + str(sdk_path / item) for item in flags] 
    return flags

def get_cc_flags(p_type):
    flags = []

    flags += get_c_arch()
    flags += get_c_predefined()

    if p_type == 'executable':
        flags += get_c_include_path()
    
    return flags





def get_swift_arch():
    triple = get_triple()
    if triple == 'thumbv7em-unknown-none-eabihf':
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

def get_swift_predefined():
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

def get_swift_linker_config():
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
    flags = (' '.join(flags)).split(' ')

    return flags

def get_swift_linker_script():
    board = get_board_name()
    sdk_path = util.get_sdk_path()

    flags = [
        '-T',
        str(sdk_path / 'Boards' / board / 'linker/ram.ld')
    ]
    flags = ['-Xlinker ' + item for item in flags]
    flags = (' '.join(flags)).split(' ')

    return flags

def get_swift_sdk_search_path():
    sdk_path = util.get_sdk_path()
    triple = get_triple()
    if triple == 'thumbv7em-unknown-none-eabihf':
        sub_path = '/v7e-m+dp/hard'
    else:
        sub_path = '/v7e-m/nofp'
    
    flags = [
        'usr/lib/gcc/arm-none-eabi/10.3.1/thumb' + sub_path,
        'usr/lib/gcc/thumb' + sub_path,
        'usr/arm-none-eabi/lib/arm-none-eabi/10.3.1/thumb' + sub_path,
        'usr/arm-none-eabi/lib/thumb' + sub_path,
        'usr/arm-none-eabi/lib/arm-none-eabi/10.3.1/thumb' + sub_path,
        'usr/arm-none-eabi/lib/thumb' + sub_path,
        'usr/arm-none-eabi/usr/lib/arm-none-eabi/10.3.1/thumb' + sub_path,
        'usr/arm-none-eabi/usr/lib/thumb' + sub_path,
        'usr/lib/gcc/arm-none-eabi/10.3.1',
        'usr/lib/gcc',
        'usr/arm-none-eabi/lib/arm-none-eabi/10.3.1',
        'usr/arm-none-eabi/lib',
        'usr/arm-none-eabi/usr/lib/arm-none-eabi/10.3.1',
        'usr/arm-none-eabi/usr/lib',
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
    flags += [
        '-lswiftCore'
    ]

    flags = (' '.join(flags)).split(' ')

    return flags


def get_swift_sdk_library():
    flags = [
        '-lstdc++',
        '-lc',
        '-lg',
        '-lm',
        '-lgcc'
    ]

    return flags


def get_swiftc_flags(p_type):
    flags = []

    flags += get_swift_arch()
    flags += get_swift_predefined()
    
    if p_type == 'executable':
        flags += get_swift_linker_config()
        flags += get_swift_linker_script()
        flags += get_swift_sdk_search_path()
        flags += get_swift_board_library()
        flags += get_swift_sdk_library()
    
    return flags

def get_destination(p_type):
    cc_flags = get_cc_flags(p_type)
    swiftc_flags = get_swiftc_flags(p_type)
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
    triple = get_triple()
    files = sorted((p_path / '.build' / triple / 'release').glob('*.bin'))
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
    
    board = get_board_name()
    target_file = get_board_info(name=board, info='target_file')
    target_path = path / target_file

    data = bin_path.read_bytes()
    value = crc32(data)
    mask = (1 << 8) - 1
    list_dec = [(value >> k) & mask for k in range(0, 32, 8)]

    with open(target_path, 'wb') as file:
        file.write(data)
        for number in list_dec:
            byte = struct.pack('B', number)
            file.write(byte)