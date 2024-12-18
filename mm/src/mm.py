import os, sys, platform, argparse, shutil
from pathlib import Path
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
#         image_name = mmp.get_board_info('sd_image_name')
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
        image_name = mmp.get_board_info('sd_image_name')
        board_name = mmp.get_board_name()
        if board_name == 'SwiftIOMicro':
            image.create_image(bin_path, build_path, image_name)
        elif board_name == 'SwiftIOBoard':
            image.create_swiftio_bin(bin_path, build_path, image_name)
        else:
            log.die('Board name is not specified') 

# def build_project(args):
#     mmp_manifest = Path(PROJECT_PATH / 'Package.mmp')

#     if not mmp_manifest.is_file():
#         log.die('Package.mmp is required to build the project')

#     mmp_content = mmp_manifest.read_text()
#     mmp.initialize(mmp_content)

#     mmp.clean(p_path=PROJECT_PATH)
#     spm.initialize()
#     p_name = spm.get_project_name()
#     p_type = spm.get_project_type()

#     build_path = ''
#     triple = None

#     if p_type == 'executable':
#         triple = mmp.get_triple()
#         build_path = PROJECT_PATH / '.build' / triple / 'release'

#     mmp.create_temp_sdk_des(p_path=PROJECT_PATH, build_path=build_path, p_type=p_type, p_name=p_name)

#     destination = mmp.create_destination(p_path=PROJECT_PATH, build_path=build_path, p_type=p_type, p_name=p_name)
#     build_with_destination(build_path=build_path, p_type=p_type, p_name=p_name, destination=destination)

#     log.inf('Done!')


def build_project(args):
    mmp_manifest = Path(PROJECT_PATH / 'Package.mmp')

    if not mmp_manifest.is_file():
        log.die('Package.mmp is required to build the project')

    mmp_content = mmp_manifest.read_text()
    mmp.initialize(mmp_content)

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


def download_project_to_partition(partition):
    mmp_manifest = Path(PROJECT_PATH / 'Package.mmp')

    if not mmp_manifest.is_file():
        log.die('Package.mmp is required to download the project')

    content = mmp_manifest.read_text()
    mmp.initialize(content)

    board_name = mmp.get_board_name()
    if board_name is None or board_name == '':
        log.die('Board name is not specified')

    if board_name != 'SwiftIOMicro':
        log.die('Download to partition is not supported on SwiftIOBoard')

    file_name = mmp.get_board_info('sd_image_name')
    triple = mmp.get_triple()
    image = PROJECT_PATH / '.build' / triple / 'release' / file_name

    if not image.is_file():
        log.die('Cannot find ' + file_name)

    serial_name = mmp.get_board_info('usb2serial_device')

    if board_name == 'SwiftIOMicro':
        serial_download.load_to_partition(serial_name, image, partition)

    log.inf('Done!')


def download_project_to_sd():
    mmp_manifest = Path(PROJECT_PATH / 'Package.mmp')

    if not mmp_manifest.is_file():
        log.die('Package.mmp is required to download the project')
    
    content = mmp_manifest.read_text()
    mmp.initialize(content)

    board_name = mmp.get_board_name()
    if board_name is None:
        log.die('Board name is not specified')

    system = platform.system()
    if board_name == 'SwiftIOBoard' and system != 'Darwin':
        log.die(system + ' is not supported currently, please copy the image file manually')

    file_name = mmp.get_board_info('sd_image_name')
    triple = mmp.get_triple()
    image = PROJECT_PATH / '.build' / triple / 'release' / file_name

    if not image.is_file():
        log.die('Cannot find ' + file_name)
    
    serial_name = mmp.get_board_info('usb2serial_device')

    if board_name == 'SwiftIOMicro':
        serial_download.load_to_sdcard(serial_name, image, file_name)
    elif board_name == 'SwiftIOBoard':
        download.darwin_download(source=image)

    log.inf('Done!')


def download_to_sd_with_target_name(serial_name, image, file_name):
        serial_download.load_to_sdcard(serial_name, image, file_name)


def download_to_sd(args):
    if args.file is None:
        log.die('Please specify the file path')

    f = args.file
    if not f.is_file():
        log.die('open file ' + str(f) + ' failed!')

    path = Path(f)
    if path.suffix == '':
        file_name = path.stem
    else:
        file_name = path.name

    download_to_sd_with_target_name('wch', f, file_name)

def download_to_partition(args):
    if args.file is None or args.partition is None:
        log.die('Please specify the file path and target partition name')
    
    f = args.file
    if not f.is_file():
        log.die('open file ' + str(f) + ' failed!')

    serial_download.load_to_partition('wch', f, args.partition)

def download_to_ram(args):
    if args.file is None or args.address is None:
        log.die('Please specify the file path and target RAM address')

    address = int(args.address, 16)
    log.inf(address)

    f = args.file
    if not f.is_file():
        log.die('open file ' + str(f) + ' failed!')
    
    serial_download.load_to_ram('wch', f, address)


def download_img(args):
    if args.type == 'sd':
        if args.file is None:
            download_project_to_sd()
        else:
            download_to_sd(args)
    elif args.type == 'partition':
        if args.file is None:
            download_project_to_partition(args.partition)
        else:
            download_to_partition(args)
    elif args.type == 'ram':
        download_to_ram(args)


def copy_resources(args):
    source = Path(args.source)
    destination = Path(args.destination)
    delete_first = True

    if source.is_absolute():
        log.die('Absolute resource path is not supported at this time')

    if not destination.is_absolute():
        log.die('The destination must be an absolute path')

    if not source.is_dir():
        log.die(str(args.source) + ' directory not exist')

    log.dbg('Destination: ' + str(args.destination))

    files = []
    for item in list(source.glob('**/*')):
        if item.is_file():
            files.append(item)

    if len(files) == 0:
        log.die(str(args.source) + ' is empty')

    if args.mode == 'sync':
        delete_first = True
    else:
        delete_first = False

    serial_download.copy_to_filesystem('wch', delete_first, source, destination, files)

    for file in files:
        log.dbg(str(file))


def add_header(args):
    if args.file is None:
        log.die('Please specify the file path')

    if args.address is None:
        log.wrn('Image default address 0x80000000')
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
                source = build_path / mmp.get_board_info('sd_image_name')
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
    init_parser.add_argument('-t', '--type', type = str, choices = ['executable', 'library'], default = 'executable', help = 'Project type: The default type is executable')
    init_parser.add_argument('--name', type = str, help = 'Initialize a new project with a specified name. If no name is provided, the project name will default to the name of the current directory')
    init_parser.add_argument('-b', '--board', type = str, choices =['SwiftIOBoard', 'SwiftIOMicro'], help = 'Pass this parameter to generate the MadMachine project file')
    init_parser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase the verbosity of the output")
    init_parser.set_defaults(func = init_project)

    build_parser = subparsers.add_parser('build', help = 'Build a project')
    build_parser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase the verbosity of the output")
    build_parser.set_defaults(func = build_project)

    header_parser = subparsers.add_parser('add_header', help = 'Add a header to the binary file')
    header_parser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase the verbosity of the output")
    header_parser.add_argument('-f', '--file', type = Path, default = None, help = "Path to the binary file")
    header_parser.add_argument('-a', '--address', type = str, default = None, help = "Target load address")
    header_parser.add_argument('--verify', type = str, choices =['crc32', 'sha256'], default = 'crc32', help = 'Type of verification')
    header_parser.set_defaults(func = add_header)

    download_parser = subparsers.add_parser('download', help = 'Download the target executable to the board\'s RAM, Flash, or SD card')
    download_parser.add_argument('-t', '--type', type = str, choices = ['ram', 'partition', 'sd'], default = 'partition', help = "Download type: The default is Flash partition")
    download_parser.add_argument('-p', '--partition', type = str, default = 'user', help = "Target flash partition, the default is 'user'")
    download_parser.add_argument('-a', '--address', type = str, default = '0x80000000', help = "Target RAM address")
    download_parser.add_argument('-f', '--file', type = Path, default = None, help = "Path to the image file")
    download_parser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase the verbosity of the output")
    download_parser.set_defaults(func = download_img)

    sync_parser = subparsers.add_parser('copy', help = 'Copy the resources to the Flash or SD card filesystem')
    sync_parser.add_argument('-m', '--mode', type = str, choices = ['sync', 'merge'], default = 'merge', help = "Copy the resources to the destination, the default mode is merge")
    sync_parser.add_argument('-s', '--source', type = Path, default = 'Resources', help = "Source path: The default path is 'Resources' within the project")
    sync_parser.add_argument('-d', '--destination', type = Path, default = '/SD:', help = "Destination path: The default path is '/SD:'")
    sync_parser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase the verbosity of the output")
    sync_parser.set_defaults(func = copy_resources)

    clean_parser = subparsers.add_parser('clean', help = 'Clean project')
    clean_parser.add_argument('--deep', action = 'store_true', help = "Clean all compilation outputs")
    clean_parser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase the verbosity of the output")
    clean_parser.set_defaults(func = clean_project)

    get_parser = subparsers.add_parser('get', help = 'Retrieve specified information for use by the IDE')
    get_parser.add_argument('--info', type = str, choices =['name', 'usb'], help = 'Type of information')
    get_parser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase the verbosity of the output")
    get_parser.set_defaults(func = get_info)

    ci_build_parser = subparsers.add_parser('ci-build', help = 'CI Build')
    ci_build_parser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase the verbosity of the output")
    ci_build_parser.set_defaults(func = ci_build)

    host_test_parser = subparsers.add_parser('host-test', help = 'Test a project on the host using the SwiftIO mock')
    host_test_parser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase the verbosity of the output")
    host_test_parser.set_defaults(func = host_test)

    args = parser.parse_args()
    if vars(args).get('version'):
        print(version.__VERSION__)
        sys.exit(0)

    if vars(args).get('func') is None:
        log.die('subcommand is required, use \'mm --help\' to get more information')

    if args.verbose:
        log.set_verbosity(log.VERBOSE_DBG)

    sdk_path = Path(os.path.realpath(sys.argv[0])).parent.parent.parent
    system = platform.system()
    if system == 'Darwin':
        swift_path = Path('/Library/Developer/Toolchains/swift-latest.xctoolchain')
    elif system == 'Linux':
        swift_path = sdk_path

    util.set_sdk_path(swift_path, sdk_path)

    PROJECT_PATH = Path('.').resolve()
    args.func(args)

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
