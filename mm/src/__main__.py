import os, sys, platform, argparse
from pathlib import Path
import log, util, spm, mmp, download

PROJECT_PATH = ''

def init_project(args):
    mmp_manifest = Path(PROJECT_PATH / 'Package.mmp')
    spm_manifest = Path(PROJECT_PATH / 'Package.swift')

    if mmp_manifest.is_file():
        log.die('Package.mmp already exists in this directory')

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
        log.wrn('Package.swift already exists, ignoring specified project type and project name')
        spm.initialize()
        init_name = spm.get_project_name()
        init_type = spm.get_project_type()
        if init_type == 'executable' and board_name is None:
            log.die('board name is required to initialize an executable')

    content = mmp.init_manifest(board=board_name, p_type=init_type)
    log.inf('Creating Package.mmp', level=log.VERBOSE_VERY)
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
        mmp.create_binary(path=path, name=p_name)
    
    log.inf('Done!')
    

def download_project(args):
    mmp_manifest = Path(PROJECT_PATH / 'Package.mmp')

    if not mmp_manifest.is_file():
        log.die('Package.mmp is required to download the project')

    system = platform.system()

    if system != 'Darwin':
        log.die('Windows and Linux are not supported currently, please copy the binary file manually')
    
    content = mmp_manifest.read_text()
    mmp.initialize(content)
    board_name = mmp.get_board_name()
    if board_name is None:
        log.die('Board name is not specified')

    file_name = mmp.get_board_info('target_file')
    source = PROJECT_PATH / '.build' / mmp.get_triple() / 'release' / file_name

    if not source.is_file():
        log.die('Cannot find ' + file_name)
    
    download.darwin_download(source=source)
    log.inf('Done!')


def clean_project(args):
    mmp.clean(p_path=PROJECT_PATH)
    if args.deep:
        spm.clean()


def main():
    global PROJECT_PATH

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    init_parser = subparsers.add_parser('init', help = 'Initiaize a new project')
    init_parser.add_argument('--type', type = str, choices = ['executable', 'library'], default = 'executable', help = 'Project type, default type is executable')
    init_parser.add_argument('--name', type = str, help = 'Initiaize the new project with a specified name, otherwise the project name depends on the current directory name')
    init_parser.add_argument('-b', '--board', type = str, choices =['SwiftIOBoard', 'SwiftIOFeather'], help = 'Generate MadMachine project file by passing this parameter')
    init_parser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase output verbosity")
    init_parser.set_defaults(func = init_project)

    build_parser = subparsers.add_parser('build', help = 'Build a project')
    build_parser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase output verbosity")
    build_parser.set_defaults(func = build_project)

    download_parser = subparsers.add_parser('download', help = 'Download a compiled executable to the board\'s SD card')
    download_parser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase output verbosity")
    download_parser.set_defaults(func = download_project)

    args = parser.parse_args()
    if vars(args).get('func') is None:
        log.die('subcommand is required, use \'mm --help\' to get more information')

    if args.verbose:
        log.set_verbosity(log.VERBOSE_VERY)

    sdk_path = Path(os.path.realpath(sys.argv[0])).parent.parent.parent
    util.set_sdk_path(sdk_path)
    
    PROJECT_PATH = Path('.').resolve()
    
    args.func(args)

if __name__ == "__main__":
    main()