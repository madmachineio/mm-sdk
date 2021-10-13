import json
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
        .package(url: "https://github.com/madmachineio/SwiftIO.git", from: "0.0.1"),
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
        .package(url: "https://github.com/madmachineio/SwiftIO.git", from: "0.0.1"),
        .package(url: "https://github.com/madmachineio/MadBoards.git", from: "0.0.1"),
        .package(url: "https://github.com/madmachineio/MadDrivers.git", from: "0.0.1"),
    ],
    targets: [
        // Targets are the basic building blocks of a package. A target can define a module or a test suite.
        // Targets can depend on other targets in this package, and on products in packages this package depends on.
        .target(
            name: "{name}",
            dependencies: [
                "SwiftIO",
                "MadBoards",
                "MadDrivers"]),
        .testTarget(
            name: "{name}Tests",
            dependencies: ["{name}"]),
    ]
)
"""

JSON_DATA = ''

def initialize():
    global JSON_DATA

    flags = [
        util.get_tool('swift-package'),
        'describe',
        '--type json'
    ]
    JSON_DATA = util.run_command(flags)


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
    name = json.loads(JSON_DATA).get('name')

    return name


def get_project_type():
    project_name = json.loads(JSON_DATA).get('name')

    project_tpye = None

    products = json.loads(JSON_DATA).get('products')
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
        targets = json.loads(JSON_DATA).get('targets')
        for target in targets:
            if target.get('name') == project_name:
                project_tpye = target.get('type')
                break

    if project_tpye is None:
        project_tpye = 'executable'
    
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