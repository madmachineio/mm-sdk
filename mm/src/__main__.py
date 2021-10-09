import argparse, log

def initProject(args):
    log.inf(f'hello', colorize=True)
    print(args)

def buildProject(args):
    print(args)

def downloadProject(args):
    print(args)


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    initParser = subparsers.add_parser('init', help = 'Initiaize a new project')
    initParser.add_argument('--type', type = str, choices = ['executable', 'library'], default = 'executable', help = 'Project type, default type is executable')
    initParser.add_argument('--name', type = str, help = 'Initiaize the new project with a specified name, otherwise the project name depends on the current directory name')
    initParser.add_argument('-b', '--board', type = str, choices =['SwiftIOBoard', 'SwiftIOFeather'], help = 'Generate MadMachine project file by passing this parameter')
    initParser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase output verbosity")
    initParser.add_argument('--nooverride', action = 'store_true', default = False, help = "Don't overwrite the Package.swift file with a common used template")
    initParser.set_defaults(func = initProject)

    buildParser = subparsers.add_parser('build', help = 'Build a project')
    buildParser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase output verbosity")
    buildParser.set_defaults(func = buildProject)

    downloadParser = subparsers.add_parser('download', help = 'Download a compiled executable to the board\'s SD card')
    downloadParser.add_argument('-v', '--verbose', action = 'store_true', help = "Increase output verbosity")
    downloadParser.set_defaults(func = downloadProject)

    args = parser.parse_args()
    d = vars(args)
    if d.get('func') is None:
        log.die('use \'mm --help\' to get more information')
    args.func(args)

if __name__ == "__main__":
    main()