import os, sys, platform, argparse, shutil
from pathlib import Path
import log, util, spm, mmp, download, version
import serial_download, image

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
            log.die('board name is required to initialize an executable')
        content = spm.init_manifest(p_name=init_name, p_type=init_type)
        spm_manifest.write_text(content, encoding='UTF-8')
    else:
        log.wrn('Package.swift already exists, project type and name are ignored')
        spm.initialize()
        init_name = spm.get_project_name()
        init_type = spm.get_project_type()
        if init_type == 'executable' and board_name is None:
            log.die('board name is required to initialize an executable')

    content = mmp.init_manifest(board=board_name, p_type=init_type)
    log.inf('Creating Package.mmp')
    mmp_manifest.write_text(content, encoding='UTF-8')


def build_project(args):
    mmp_manifest = Path(PROJECT_PATH / 'Package.mmp')

    if not mmp_manifest.is_file():
        log.die('Package.mmp is required to build the project')
    
    content = mmp_manifest.read_text()
    mmp.initialize(content)

    mmp.clean(p_path=PROJECT_PATH)
    spm.initialize()
    p_name = spm.get_project_name()
    p_type = spm.get_project_type()

    js_data = mmp.get_destination(p_type=p_type)
    (PROJECT_PATH / '.build').mkdir(exist_ok=True)
    destination = PROJECT_PATH / '.build/destination.json'
    destination.write_text(js_data, encoding='UTF-8')

    spm.build(destination=destination, p_type=p_type)

    triple = mmp.get_triple()
    path = PROJECT_PATH / '.build' / triple / 'release'

    if p_type == 'executable' and (path / p_name).exists():
        bin_path = mmp.create_binary(path=path, name=p_name)
        image.create_image(bin_path, path, p_name)
    
    log.inf('Done!')
    

def download_project_to_sd(args):
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
    image = PROJECT_PATH / '.build' / mmp.get_triple() / 'release' / file_name

    if not image.is_file():
        log.die('Cannot find ' + file_name)
    
    serial_name = mmp.get_board_info('usb2serial_device')

    if board_name == 'SwiftIOFeather':
        serial_download.load_to_sdcard(serial_name, image, file_name)
    elif board_name == 'SwiftIOBoard':
        download.darwin_download(source=image)

    log.inf('Done!')

def download_to_partition(args):
    if args.file is None or args.partition is None:
        log.die('Plz specify the file path and target partition name')
    
    f = args.file
    if not f.is_file():
        log.die('open file ' + str(f) + ' failed!')

    serial_download.load_to_partition('CP21', f, args.partition)

def download_to_ram(args):
    if args.file is None or args.address is None:
        log.die('Plz specify the file path and target RAM address')

    address = int(args.address, 16)
    log.inf(address)

    f = args.file
    if not f.is_file():
        log.die('open file ' + str(f) + ' failed!')
    
    serial_download.load_to_ram('CP21', f, address)


def download_img(args):
    if args.location == 'sd':
        download_project_to_sd(args)
    elif args.location == 'partition':
        download_to_partition(args)
    elif args.location == 'ram':
        download_to_ram(args)


def add_header(args):
    if args.file is None:
        log.die('Plz specify the file path')

    if args.address is None:
        log.wrn('Image default address 0x80000000')
        address = 0x80000000
    else:
        address = int(args.address, 16)

    f = args.file
    if not f.is_file():
        log.die('open file ' + str(f) + ' failed!')

    current_path = Path('.')
    image.create_image(f, current_path, f.name + '.img', address)    

def ci_build(args):
    spm.initialize()
    p_name = spm.get_project_name()
    p_type = spm.get_project_type()

    if p_type == 'executable':
        boards = ['SwiftIOFeather', 'SwiftIOBoard']
    else:
        boards = ['']

    triples = ['thumbv7em-unknown-none-eabi', 'thumbv7em-unknown-none-eabihf']

    for board in boards:
        for triple in triples:
            log.inf('Building for ' + triple)
            #(PROJECT_PATH / '.build').unlink(missing_ok=True)
            if (PROJECT_PATH / '.build').exists():
                shutil.rmtree((PROJECT_PATH / '.build'))
            content = mmp.init_manifest(board=board, p_type=p_type, triple=triple)
            mmp.initialize(content)
            js_data = mmp.get_destination(p_type=p_type)
            (PROJECT_PATH / '.build').mkdir(exist_ok=True)
            destination = PROJECT_PATH / '.build/destination.json'
            destination.write_text(js_data, encoding='UTF-8')

            spm.build(destination=destination, p_type=p_type)

            path = PROJECT_PATH / '.build' / triple / 'release'

            if p_type == 'executable' and (path / p_name).exists():
                log.inf('Building for ' + board)
                bin_path = mmp.create_binary(path, name)
                image.create_image(bin_path, path=path, name=p_name)
                source = path / mmp.get_board_info('sd_image_name')
                target = PROJECT_PATH / triple / board / p_name
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

    init_parser = subparsers.add_parser('init', help = 'Initiaize a new project')
    init_parser.add_argument('-t', '--type', type = str, choices = ['executable', 'library'], default = 'executable', help = 'Project type, default type is executable')
    init_parser.add_argument('--name', type = str, help = 'Initiaize the new project with a specified name, otherwise the project name depends on the current directory name')
    init_parser.add_argument('-b', '--board', type = str, choices =['SwiftIOBoard', 'SwiftIOFeather'], help = 'Generate MadMachine project file by passing this parameter')
    init_parser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase output verbosity")
    init_parser.set_defaults(func = init_project)

    build_parser = subparsers.add_parser('build', help = 'Build a project')
    build_parser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase output verbosity")
    build_parser.set_defaults(func = build_project)

    header_parser = subparsers.add_parser('add_header', help = 'Add header to bin file')
    header_parser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase output verbosity")
    header_parser.add_argument('-f', '--file', type = Path, default = None, help = "Binary file path")
    header_parser.add_argument('-a', '--address', type = str, default = None, help = "Target RAM address")
    header_parser.set_defaults(func = add_header)

    download_parser = subparsers.add_parser('download', help = 'Download the target executable to the board\'s SD card')
    download_parser.add_argument('-l', '--location', type = str, choices = ['ram', 'partition', 'sd'], default = 'sd', help = "Download type, default is sd card")
    download_parser.add_argument('-f', '--file', type = Path, default = None, help = "File path")
    download_parser.add_argument('-p', '--partition', type = str, default = None, help = "Target partition")
    download_parser.add_argument('-a', '--address', type = str, default = None, help = "Target RAM address")
    download_parser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase output verbosity")
    download_parser.set_defaults(func = download_img)

    clean_parser = subparsers.add_parser('clean', help = 'Clean project')
    clean_parser.add_argument('--deep', action = 'store_true', help = "Clean all compilation outputs")
    clean_parser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase output verbosity")
    clean_parser.set_defaults(func = clean_project)

    get_parser = subparsers.add_parser('get', help = 'Get specified information, used by IDE')
    get_parser.add_argument('--info', type = str, choices =['name', 'usb'], help = 'Information type')
    get_parser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase output verbosity")
    get_parser.set_defaults(func = get_info)

    ci_build_parser = subparsers.add_parser('ci-build', help = 'CI Build')
    ci_build_parser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase output verbosity")
    ci_build_parser.set_defaults(func = ci_build)

    host_test_parser = subparsers.add_parser('host-test', help = 'Test a project in host with SwiftIO mock')
    host_test_parser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase output verbosity")
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
    util.set_sdk_path(sdk_path)
    
    PROJECT_PATH = Path('.').resolve()
    
    args.func(args)

if __name__ == "__main__":
    main()
