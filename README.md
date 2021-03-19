[![alt Discord](https://img.shields.io/discord/592743353049808899 "Discord")](https://madmachine.io/discord)

# MM SDK

The mm-sdk contains eveything you need to build a MadMachine project, either a library or an executable.

A MadMachine project is structured the same as a [Swift package](https://swift.org/package-manager).

Download the latest release depending on your OS on the [Releases page](https://github.com/madmachineio/mm-sdk/releases).

The latest features would be added to this SDK first and then integrated into the MadMachine IDE.

# What is inside the SDK

1. Boards
   * Board abstraction libraries based on [Zephyr](https://github.com/zephyrproject-rtos/zephyr)

2. mm
   * Python script which is used to help building the project

3. usr (This directory is only contained in the [release package](https://github.com/madmachineio/mm-sdk/releases), not in the git repo)
   * Clang, Swift compilier, SwiftPM tools etc.
   * Standard library and arch related libraries
   * Compiled Python build tool

# Usage (Take macOS and Linux for example)

Download and unzip the sdk to the directory `~`

`~/mm-sdk/usr/mm/mm -h` command for quick help.

`~/mm-sdk/usr/mm/mm init -h` command for quick help about initializing a project.

`~/mm-sdk/usr/mm build -h` command for quick help about building a project.

## Initialize a library `DemoLibrary` in `~/Documents`

```shell
cd ~/Documents
mkdir DemoLibrary
cd DemoLibrary
~/mm-sdk/usr/mm/mm init --type library
```

## Initialize an executable `DemoProgram` in `~/Documents`

```shell
cd ~/Documents
mkdir DemoProgram
cd DemoProgram
~/mm-sdk/usr/mm/mm init
```
## Add the local `DemoLibrary` as a dependency to `DemoProgram`

1. Open the `Package.swift` in `DemoProgram` directory by any text editor
2. Add `.package(path: "../DemoLibrary"),` in the `dependencies`
3. Add `"DemoLibrary"` to the target dependencies, the full code looks like below
```swift
// swift-tools-version:5.3
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "DemoProgram",
    dependencies: [
        // Dependencies declare other packages that this package depends on.
        .package(url: "https://github.com/madmachineio/SwiftIO.git", .branch("main")),
        .package(url: "https://github.com/madmachineio/MadBoards.git", .branch("main")),
        .package(path: "../DemoLibrary"),
    ],
    targets: [
        // Targets are the basic building blocks of a package. A target can define a module or a test suite.
        // Targets can depend on other targets in this package, and on products in packages this package depends on.
        .target(
            name: "DemoProgram",
            dependencies: ["SwiftIO", "MadBoards", "DemoLibrary"]),
        .testTarget(
            name: "DemoProgramTests",
            dependencies: ["DemoProgram"]),
    ]
)
```
4. Save and quit
5. Then you can `import DemoLibrary` in the source code


## Build a library

```shell
cd ~/Documents/DemoLibrary
~/mm-sdk/usr/mm/mm build -b SwiftIOBoard
```

## Build an executable

```shell
cd ~/Documents/DemoProgram
~/mm-sdk/usr/mm/mm build -b SwiftIOBoard
```

## Download an executable to the board

After a successful building, there would be `.build/release/swiftio.bin` in your project directory. Note that the `.build` directory is hiden by default.

Follow those steps to download the executable:

1. Insert SD card to the board and connect the it to your computer through an USB cable
2. Press the **Download** button and wait the onboard RGB LED turns to static **green**)
2. A USB disk drive should be mounted on your computer
3. Copy the `swiftio.bin` to the SD card root directory
4. Eject the USB drive and the program would run automatically

------

# Usage (Take Windows 10 for example)

Download and unzip the sdk to the directory `D:\`

Press `Win + R` keys on your keyboard, then type `cmd`, and press Enter on your keyboard or click OK to run a Command Prompt.

`D:\mm-sdk\usr\mm\mm -h` command for quick help.

`D:\mm-sdk\usr\mm\mm init -h` command for quick help about initializing a project.

`D:\mm-sdk\usr\mm build -h` command for quick help about building a project.

## Initialize a library `DemoLibrary` in `D:\`

```shell
D:
mkdir DemoLibrary
cd DemoLibrary
D:\mm-sdk\usr\mm\mm init --type library
```

## Initialize an executable `DemoProgram` in `D:\`

```shell
D:
mkdir DemoProgram
cd DemoProgram
D:\mm-sdk\usr\mm\mm init
```
## Add the local `DemoLibrary` as a dependency to `DemoProgram`

1. Open the `Package.swift` in `DemoProgram` directory by any text editor
2. Add `.package(path: "../DemoLibrary"),` in the `dependencies`
3. Add `"DemoLibrary"` to the target dependencies, the full code looks like below
```swift
// swift-tools-version:5.3
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "DemoProgram",
    dependencies: [
        // Dependencies declare other packages that this package depends on.
        .package(url: "https://github.com/madmachineio/SwiftIO.git", .branch("main")),
        .package(url: "https://github.com/madmachineio/MadBoards.git", .branch("main")),
        .package(path: "../DemoLibrary"),
    ],
    targets: [
        // Targets are the basic building blocks of a package. A target can define a module or a test suite.
        // Targets can depend on other targets in this package, and on products in packages this package depends on.
        .target(
            name: "DemoProgram",
            dependencies: ["SwiftIO", "MadBoards", "DemoLibrary"]),
        .testTarget(
            name: "DemoProgramTests",
            dependencies: ["DemoProgram"]),
    ]
)
```
4. Save and quit
5. Then you can `import DemoLibrary` in the source code


## Build a library

```shell
cd D:\DemoLibrary
D:\mm-sdk\usr\mm\mm build -b SwiftIOBoard
```

## Build an executable

```shell
cd D:\DemoProgram
D:\mm-sdk\usr\mm\mm build -b SwiftIOBoard
```

## Download an executable to the board

After a successful building, there would be `.build\release\swiftio.bin` in your project directory.

Follow those steps to download the executable:

1. Insert SD card to the board and connect the it to your computer through an USB cable
2. Press the **Download** button and wait the onboard RGB LED turns to static **green**)
2. A USB disk drive should be mounted on your computer
3. Copy the `swiftio.bin` to the SD card root directory
4. Eject the USB drive and the program would run automatically