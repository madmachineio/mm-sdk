import os, sys, argparse
from pathlib import Path
import log, util, spm

PROJECT_PATH=''

def init_project(args):
    mmp = Path(PROJECT_PATH / 'Package.mmp')
    manifest = Path(PROJECT_PATH / 'Package.swift')

    if mmp.is_file():
        log.die('a Package.mmp already exists in this directory')

    if not manifest.is_file():
        init_type = args.type
        if args.name:
            init_name = args.name
        else:
            init_name = PROJECT_PATH.name
        spm.init_manifest(p_name=init_name, p_type=init_type, pos=manifest)
    else:
        log.wrn('a Package.swift already exists, ignoring init type and name')
        init_name = spm.get_project_name()
        init_type = spm.get_project_type()

    board_name = args.board
    if board_name is None and init_type == 'executable':
        log.die('board name is required to initialize an executable')


def build_project(args):
    log.inf('build')


def download_project(args):
    log.inf('download')


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