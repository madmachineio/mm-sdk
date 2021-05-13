# IDE integration guide


## Create a new project

Create a new project **Hello** in `~/Documents/MadMachine/Projects`

1. If there is alrealy a directory or file named **Hello**, stop and alert the user!
2. `mkdir ~/Documents/MadMachine/Projects/Hello`
3. `cd ~/Documents/MadMachine/Projects/Hello`
4. `mm-sdk/usr/mm/mm init --type *** --board ***`

`***` needs to be replaced by user config

After these procedures, the project should be initialized correctlly


## Open an existing project

1. User need to double click the project file `Package.mmp` or open it in the IDE menu bar
2. `cd` into the project directory 
3. `mm-sdk/usr/mm/mm run --action get-name` to get the project name. If this command returns error, then the project is broken. The IDE should alert and quit.


## Get the SD card status and show the result in the IDE

This action should be done in a standalone thread periodically so it would not block the main thread, the interval should be tested

1. `cd` into the project directory
2. `mm-sdk/usr/mm/mm run --action get-status`


## Build a project

1. `cd` into the project directory
2. `mm-sdk/usr/mm/mm run --action build`


## Download a project

1. If the SD card status is not "*** ready", stop and alert.
2. Pause the SD card detecting thread
3. `cd` into the project directory
4. `mm-sdk/usr/mm/mm run --action download`
5. Resume the SD card detecting thread

