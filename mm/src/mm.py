import os, sys, platform, argparse, shutil
from pathlib import Path, PurePosixPath
import log, util, spm, mmp, download, version
import serial_download, image
import multiprocessing

PROJECT_PATH = ''

def init_project(args):
    mmp_manifest = Path(PROJECT_PATH / 'Package.mmp')
    spm_manifest = Path(PROJECT_PATH / 'Package.swift')

    if mmp_manifest.is_file():
        log.die('Package.mmp already exists, command ignored')

    board_name = args.board
    if not spm_manifest.is_file():
        init_type = args.type
        if args.name:
            init_name = args.name
        else:
            init_name = PROJECT_PATH.name
        if init_type == 'executable' and board_name is None:
            log.die('The board name is required to initialize an executable')
        content = spm.init_manifest(p_name=init_name, p_type=init_type)
        spm_manifest.write_text(content, encoding='UTF-8')
    else:
        log.wrn('Package.swift already exists, project type and name are ignored')
        spm.initialize()
        init_name = spm.get_project_name()
        init_type = spm.get_project_type()
        if init_type == 'executable' and board_name is None:
            log.die('The board name is required to initialize an executable')

    content = mmp.init_manifest(board=board_name, p_type=init_type)
    log.inf('Creating Package.mmp')
    mmp_manifest.write_text(content, encoding='UTF-8')


# def build_with_destination(build_path, p_type, p_name, destination):
#     spm.destination_build(p_type=p_type, destination=destination)

#     if p_type == 'executable' and (build_path / p_name).exists():
#         bin_path = mmp.create_binary(build_path=build_path, name=p_name)
#         image_name = mmp.get_board_info('image_name')
#         board_name = mmp.get_board_name()
#         if board_name == 'SwiftIOMicro':
#             image.create_image(bin_path, build_path, image_name)
#         elif board_name == 'SwiftIOBoard':
#             image.create_swiftio_bin(bin_path, build_path, image_name)
#         else:
#             log.die('Board name is not specified')

def build_with_sdk(build_path, p_type, p_name):
    spm.build(p_path=PROJECT_PATH, p_type=p_type)

    if p_type == 'executable' and (build_path / p_name).exists():
        bin_path = mmp.create_binary(build_path=build_path, name=p_name)
        image_name = mmp.get_board_info('image_name')
        board_name = mmp.get_board_name()
        if board_name == 'SwiftIOMicro':
            image.create_image(bin_path, build_path, image_name)
        elif board_name == 'SwiftIOBoard':
            image.create_swiftio_bin(bin_path, build_path, image_name)
        else:
            log.die('Board name is not specified') 


def build_project(args):
    mmp_manifest = Path(PROJECT_PATH / 'Package.mmp')
    mmp.initialize(mmp_manifest)

    mmp.clean(p_path=PROJECT_PATH)
    spm.initialize()
    p_name = spm.get_project_name()
    p_type = spm.get_project_type()

    build_path = ''
    triple = None

    if p_type == 'executable':
        triple = mmp.get_triple()
        build_path = PROJECT_PATH / '.build' / triple / 'release'

    mmp.create_temp_sdk_des(p_path=PROJECT_PATH, build_path=build_path, p_type=p_type, p_name=p_name)
    build_with_sdk(build_path=build_path, p_type=p_type, p_name=p_name)

    log.inf('Done!')


def download_file_to_partition(args):
    log.dbg('Partition: ' + str(args.partition))
    serial_download.load_to_partition(args.serial, args.file, args.partition)

    log.inf('Done!')


# Only for SwiftIOBoard
# Not recommended to use this function
# Please use 'mm copy' command instead
def download_file_to_sd(args):
    mmp_manifest = Path(PROJECT_PATH / 'Package.mmp')
    mmp.initialize(mmp_manifest)
    board_name = mmp.get_board_name()

    file_new_name = str(args.file.name)

    if board_name != 'SwiftIOBoard':
        log.wrn('Deprecated command, please use "mm copy" instead')
        serial_download.load_to_sdcard(args.serial, args.file, file_new_name)
    else:
        download.darwin_download(source=args.file)

    log.inf('Done!')


def download_file_to_ram(args):
    if args.address is None:
        log.die('Please specify the target RAM address')

    address = int(args.address, 16)
    log.inf('Download to RAM address: ' + str(address))

    serial_download.load_to_ram(args.serial, args.file, address)


def download_file(args):
    if args.file is None or args.serial is None:
        mmp_manifest = Path(PROJECT_PATH / 'Package.mmp')
        mmp.initialize(mmp_manifest)
        board_name = mmp.get_board_name()
        if board_name == 'SwiftIOBoard' and args.type == 'partition':
            log.die('Download to partition is not supported on SwiftIOBoard')

    if args.file is None:
        log.dbg('No file specified, using the default image file')
        args.file = mmp.get_default_image_path(PROJECT_PATH)

    args.file = Path(args.file)
    if not args.file.is_file():
        log.die('cannot find ' + str(args.file))

    if args.serial is None:
        log.dbg('No serial name specified, using the default serial name')
        args.serial = mmp.get_board_info('usb2serial_device')

    log.dbg('File: ' + str(args.file))
    log.dbg('Serial: ' + str(args.serial))

    if args.type == 'partition':
        download_file_to_partition(args)
    elif args.type == 'ram':
        download_file_to_ram(args)
    elif args.type == 'sd':
        download_file_to_sd(args)

def copy_resources(args):
    if args.serial is None:
        mmp_manifest = Path(PROJECT_PATH / 'Package.mmp')
        mmp.initialize(mmp_manifest)
        board_name = mmp.get_board_name()
        if board_name == 'SwiftIOBoard':
            log.die('copy command is not supported on SwiftIOBoard')
        args.serial = mmp.get_board_info('usb2serial_device')
        log.dbg('No serial name specified, using the default serial info: ' + args.serial)

    source = Path(args.source).resolve()
    if not source.exists():
        log.die(str(args.source) + ' not exists')

    # Path works differently on Windows and Unix-like systems
    # Use PurePosixPath here
    if not str(args.destination).startswith('/'):
        log.die('The destination is supposed be an absolute path, now it is: ' + str(destination))

    destination = PurePosixPath(args.destination)

    if args.mode == 'sync':
        delete_first = True
    else:
        delete_first = False

    # if source.is_dir() and source.is_absolute():
    #     log.die('Absolute directory path is not supported')

    log.dbg('Source: ' + str(args.source))
    log.dbg('Destination: ' + str(args.destination))
    log.dbg('Device: ' + str(args.serial))
    log.dbg('Mode: ' + str(args.mode))

    serial_download.copy_to_filesystem(args.serial, delete_first, source, destination)


def add_header(args):
    if args.file is None:
        log.die('Please specify the file path')

    if args.address is None:
        log.wrn('Using default image address: 0x80000000')
        address = 0x80000000
    else:
        address = int(args.address, 16)

    f = args.file
    if not f.is_file():
        log.die('open file ' + str(f) + ' failed!')

    current_path = Path('.')
    image.create_image(f, current_path, f.name + '.img', address, args.verify)    


def ci_build(args):
    spm.initialize()
    p_name = spm.get_project_name()
    p_type = spm.get_project_type()

    if p_type == 'executable':
        boards = ['SwiftIOMicro', 'SwiftIOBoard']
    else:
        boards = ['']

    #triples = ['thumbv7em-unknown-none-eabi', 'thumbv7em-unknown-none-eabihf']
    triple = 'armv7em-none-none-eabi'
    hard_float_abi = (#('true', 'true'),
                      ('true', 'false'),
                      ('false', 'false'))

    for board in boards:
        for hard_float, float_abi in hard_float_abi:
            log.inf('Building for ' + triple + ', hard-float = ' + hard_float + ', float_abi = ' + float_abi)
            if (PROJECT_PATH / '.build').exists():
                shutil.rmtree((PROJECT_PATH / '.build'))
            mmp_content = mmp.init_manifest(board=board, p_type=p_type, triple=triple, hard_float=hard_float, float_abi=float_abi)
            mmp.initialize(mmp_content)
            build_path = PROJECT_PATH / '.build' / triple / 'release'

            # destination = mmp.create_destination(p_path=PROJECT_PATH, build_path=build_path, p_type=p_type, p_name=p_name)
            # build_with_destination(build_path=build_path, p_type=p_type, p_name=p_name, destination=destination)

            mmp.create_temp_sdk_des(p_path=PROJECT_PATH, build_path=build_path, p_type=p_type, p_name=p_name)
            build_with_sdk(build_path=build_path, p_type=p_type, p_name=p_name)
            if p_type == 'executable' and (build_path / p_name).exists():
                float_type = ''
                if hard_float.startswith('true') and float_abi.startswith('true'):
                    float_type = 'hard'
                elif hard_float.startswith('true') and float_abi.startswith('false'):
                    float_type = 'softfp'
                else:
                    float_type = 'nofp'
                    
                log.inf('Building for ' + board)
                source = build_path / mmp.get_board_info('image_name')
                target = PROJECT_PATH / triple / float_type / board / p_name
                target.mkdir(parents=True, exist_ok=True)
                shutil.copy(source, target)
    
    log.inf('Done!')


def host_test(args):
    packages_dir = PROJECT_PATH / 'Packages'
    build_dir = PROJECT_PATH / '.build'
    resolved_file = PROJECT_PATH / 'Package.resolved'
    report_file = PROJECT_PATH / 'info.lcov'

    system = platform.system()

    spm.initialize()
    p_name = spm.get_project_name()
    # p_type = spm.get_project_type()

    if packages_dir.exists():
        shutil.rmtree(packages_dir)

    if build_dir.exists():
        shutil.rmtree(build_dir)

    if resolved_file.exists():
        resolved_file.unlink()
    
    if report_file.exists():
        report_file.unlink()
    
    revision = spm.get_mock_revision()
   
    spm.edit_package('SwiftIO', revision)
    spm.host_test()
    codecov_path = spm.get_codecov_path()

    test_result = ''
    if system != 'Darwin':
        test_result = str(codecov_path.parent / (p_name + 'PackageTests.xctest'))
    else:
        test_result = str(codecov_path.parent / (p_name + 'PackageTests.xctest') / 'Contents' / 'MacOS' / (p_name + 'PackageTests'))

    prof_path = str(codecov_path / 'default.profdata')

    spm.generate_code_report(test_result, prof_path)

    if packages_dir.exists():
        shutil.rmtree(packages_dir)

    if build_dir.exists():
        shutil.rmtree(build_dir)

    if resolved_file.exists():
        resolved_file.unlink()

    log.inf('OK!')


def clean_project(args):
    mmp.clean(p_path=PROJECT_PATH)
    if args.deep:
        spm.clean()


def get_info(args):
    if args.info == 'usb':
        mmp_manifest = Path(PROJECT_PATH / 'Package.mmp')
        if not mmp_manifest.is_file():
            log.die('Package.mmp is required to get usb status')
        system = platform.system()
        if system != 'Darwin':
            log.die(system + ' is not supported currently, please copy the bin file manually')
        content = mmp_manifest.read_text()
        mmp.initialize(content)
        board_name = mmp.get_board_name()
        mount_path = download.darwin_get_mount_point()
        if mount_path is None:
            log.inf(board_name + ' not connected')
        else:
            log.inf(board_name + ' ready')
    else:
        spm_manifest = Path(PROJECT_PATH / 'Package.swift')
        if not spm_manifest.is_file():
            log.die('Package.swift is required to get project name')
        spm.initialize()
        p_name = spm.get_project_name()
        log.inf(p_name)


def main():
    global PROJECT_PATH

    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action = 'store_true', help = "Show the MadMachine SDK version")

    subparsers = parser.add_subparsers()

    init_parser = subparsers.add_parser('init', help = 'Initialize a new project')
    init_parser.add_argument('--toolchain', type = Path, default = None, help = 'Set a specific Swift toolchain path, if not set, the default toolchain will be used')
    init_parser.add_argument('-t', '--type', type = str, choices = ['executable', 'library'], default = 'executable', help = 'Project type: The default type is executable')
    init_parser.add_argument('-b', '--board', type = str, choices =['SwiftIOBoard', 'SwiftIOMicro'], help = 'Pass this parameter to generate the MadMachine project file')
    init_parser.add_argument('--name', type = str, help = 'Initialize a new project with a specified name. If no name is provided, the project name will default to the name of the current directory')
    init_parser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase the verbosity of the output")
    init_parser.set_defaults(func = init_project)

    build_parser = subparsers.add_parser('build', help = 'Build a project')
    build_parser.add_argument('--toolchain', type = Path, default = None, help = 'Set a specific Swift toolchain path, if not set, the default toolchain will be used')
    build_parser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase the verbosity of the output")
    build_parser.set_defaults(func = build_project)

    download_parser = subparsers.add_parser('download', help = 'Download the target executable to the board\'s RAM, Flash, or SD card')
    download_parser.add_argument('-f', '--file', type = Path, default = None, help = 'Path to the image file')
    download_parser.add_argument('-t', '--type', type = str, choices = ['partition', 'ram', 'sd'], default = 'partition', help = "Download type: The default is Flash partition")
    download_parser.add_argument('-p', '--partition', type = str, default = 'user', help = "Target flash partition, the default is 'user'")
    download_parser.add_argument('-a', '--address', type = str, default = '0x80000000', help = "Target RAM address")
    download_parser.add_argument('--serial', type = str, default = None, help = "Name, description or hwid of the serial device")
    download_parser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase the verbosity of the output")
    download_parser.set_defaults(func = download_file)

    copy_parser = subparsers.add_parser('copy', help = 'Copy the resources to the Flash or SD card filesystem')
    copy_parser.add_argument('-m', '--mode', type = str, choices = ['sync', 'merge'], default = 'merge', help = "Copy the resources to the destination, the default mode is merge")
    copy_parser.add_argument('-s', '--source', type = Path, default = 'Resources', help = "Source path: The default path is 'Resources' within the project")
    copy_parser.add_argument('-d', '--destination', type = PurePosixPath, default = '/SD:', help = "Destination path: The default path is '/SD:'")
    copy_parser.add_argument('--serial', type = str, default = None, help = "Name, description or hwid of the serial device")
    copy_parser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase the verbosity of the output")
    copy_parser.set_defaults(func = copy_resources)

    clean_parser = subparsers.add_parser('clean', help = 'Clean project')
    clean_parser.add_argument('--deep', action = 'store_true', help = "Clean all compilation outputs")
    clean_parser.add_argument('--toolchain', type = Path, default = None, help = 'Set a specific Swift toolchain path, if not set, the default toolchain will be used')
    clean_parser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase the verbosity of the output")
    clean_parser.set_defaults(func = clean_project)

    get_parser = subparsers.add_parser('get', help = 'Retrieve specified information for use by the IDE')
    get_parser.add_argument('--info', type = str, choices =['name', 'usb'], help = 'Type of information')
    get_parser.add_argument('--toolchain', type = Path, default = None, help = 'Set a specific Swift toolchain path, if not set, the default toolchain will be used')
    get_parser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase the verbosity of the output")
    get_parser.set_defaults(func = get_info)

    ci_build_parser = subparsers.add_parser('ci-build', help = 'CI Build')
    ci_build_parser.add_argument('--toolchain', type = Path, default = None, help = 'Set a specific Swift toolchain path, if not set, the default toolchain will be used')
    ci_build_parser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase the verbosity of the output")
    ci_build_parser.set_defaults(func = ci_build)

    header_parser = subparsers.add_parser('add_header', help = 'Add a header to the binary file')
    header_parser.add_argument('-f', '--file', type = Path, default = None, help = "Path to the binary file")
    header_parser.add_argument('-a', '--address', type = str, default = None, help = "Target load address")
    header_parser.add_argument('--verify', type = str, choices =['crc32', 'sha256'], default = 'sha256', help = 'Type of verification')
    header_parser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase the verbosity of the output")
    header_parser.set_defaults(func = add_header)

    host_test_parser = subparsers.add_parser('host-test', help = 'Test a project on the host using the SwiftIO mock')
    host_test_parser.add_argument('--toolchain', type = Path, default = None, help = 'Set a specific Swift toolchain path, if not set, the default toolchain will be used')
    host_test_parser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase the verbosity of the output")
    host_test_parser.set_defaults(func = host_test)

    PROJECT_PATH = Path('.').resolve()
    sdk_path = Path(os.path.realpath(sys.argv[0])) / '../../..'
    sdk_path = sdk_path.resolve()

    args = parser.parse_args()
    if vars(args).get('version'):
        print(version.__VERSION__)
        sys.exit(0)

    if args.verbose:
        log.set_verbosity(log.VERBOSE_DBG)

    function = vars(args).get('func')
    if function is None:
        log.die('subcommand is required, use \'mm --help\' to get more information')

    toolchain_path = None
    if vars(args).get('toolchain') is not None:
        toolchain_path = vars(args).get('toolchain')

    if function == download_file or function == copy_resources or function == add_header:
        util.init_sdk_and_swift_path(sdk_path, toolchain_path, needSwiftToolchain=False)
    else:
        util.init_sdk_and_swift_path(sdk_path, toolchain_path, needSwiftToolchain=True)


    args.func(args)

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
