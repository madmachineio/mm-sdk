import json, shutil
from pathlib import Path
import util, log

DEFAULT_LIB_MANIFEST = """// swift-tools-version:5.3
// The swift-tools-version declares the minimum version of Swift required to build this package.
import PackageDescription
let package = Package(
    name: "{name}",
    products: [
        // Products define the executables and libraries a package produces, and make them visible to other packages.
        .library(
            name: "{name}",
            targets: ["{name}"]),
    ],
    dependencies: [
        // Dependencies declare other packages that this package depends on.
        .package(url: "https://github.com/madmachineio/SwiftIO.git", .upToNextMinor(from: "0.0.1")),
    ],
    targets: [
        // Targets are the basic building blocks of a package. A target can define a module or a test suite.
        // Targets can depend on other targets in this package, and on products in packages this package depends on.
        .target(
            name: "{name}",
            dependencies: ["SwiftIO"]),
        .testTarget(
            name: "{name}Tests",
            dependencies: ["{name}"]),
    ]
)
"""

DEFAULT_EXE_MANIFEST = """// swift-tools-version:5.3
// The swift-tools-version declares the minimum version of Swift required to build this package.
import PackageDescription
let package = Package(
    name: "{name}",
    dependencies: [
        // Dependencies declare other packages that this package depends on.
        .package(url: "https://github.com/madmachineio/SwiftIO.git", .upToNextMinor(from: "0.0.1")),
        .package(url: "https://github.com/madmachineio/MadBoards.git", .upToNextMinor(from: "0.0.1")),
        .package(url: "https://github.com/madmachineio/MadDrivers.git", .upToNextMinor(from: "0.0.1")),
    ],
    targets: [
        // Targets are the basic building blocks of a package. A target can define a module or a test suite.
        // Targets can depend on other targets in this package, and on products in packages this package depends on.
        .target(
            name: "{name}",
            dependencies: [
                "SwiftIO",
                "MadBoards",
                // use specific library would speed up the compile procedure
                .product(name: "MadDrivers", package: "MadDrivers")
            ]),
        .testTarget(
            name: "{name}Tests",
            dependencies: ["{name}"]),
    ]
)
"""

PKG_DESCRIBE_JSON = ''


def initialize():
    global PKG_DESCRIBE_JSON

    flags = [
        util.get_tool('swift-package'),
        'describe',
        '--type json'
    ]
    PKG_DESCRIBE_JSON = util.run_command(flags) 


def init_manifest(p_name, p_type):
    flags = [
        util.get_tool('swift-package'),
        'init',
        '--type ' + p_type,
        '--name ' + p_name
    ]

    ret = util.run_command(flags)
    log.inf(ret, level=log.VERBOSE_VERY)

    if p_type == 'library':
        content = DEFAULT_LIB_MANIFEST
    else:
        content = DEFAULT_EXE_MANIFEST
    
    return content.format(name=p_name)


def get_project_name():
    name = json.loads(PKG_DESCRIBE_JSON).get('name')

    return name


def get_project_type():
    project_name = json.loads(PKG_DESCRIBE_JSON).get('name')

    project_tpye = None

    products = json.loads(PKG_DESCRIBE_JSON).get('products')
    for product in products:
        if product.get('name') == project_name:
            product_tpye = product.get('type')
            if product_tpye.get('executable') is not None:
                project_tpye = 'executable'
                break
            elif product_tpye.get('library') is not None:
                project_tpye = 'library'
                break

    if project_tpye is None:
        targets = json.loads(PKG_DESCRIBE_JSON).get('targets')
        for target in targets:
            if target.get('name') == project_name:
                project_tpye = target.get('type')
                break

    if project_tpye is None:
        project_tpye = 'library'
    
    return project_tpye


def build(destination, p_type):
    flags = [
        util.get_tool('swift-build'),
        '-c release',
        '--destination',
        util.quote_string(destination)
    ]

    if p_type == 'executable':
        log.inf('Building executable...')
    else:
        log.inf('Building library...')

    if util.command(flags):
        log.die('compile failed')


def clean():
    flags = [
        util.get_tool('swift-package'),
        'clean'
    ]
    ret = util.command(flags)

    return ret


def get_mock_revision():
    flags = [
        'git clone',
        '-b mock',
        'https://github.com/madmachineio/SwiftIO.git'
    ]
    if util.command(flags):
        log.die('Git clone SwiftIO mock branch failed')

    flags = [
        'git',
        '--git-dir=./SwiftIO/.git',
        '--work-tree=./SwiftIO',
        'rev-parse',
        'mock'
    ]
    revision = util.run_command(flags).strip()

    repo = Path('./SwiftIO')
    if repo.exists():
        shutil.rmtree(repo)

    return revision


def edit_package(package, revision):
    flags = [
        util.get_tool('swift-package'),
        'edit',
        package,
        '--revision',
        revision
    ]

    if util.command(flags):
        log.die('Checkout to mock revision failed')


def host_test():
    flags = [
        util.get_tool('swift-test')
    ]

    if(util.command(flags)):
        log.die('host swift test failed')