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
3. `mm-sdk/usr/mm/mm get --info name` to get the project name. If this command returns error, then the project is broken. The IDE should alert and quit.


## Build a project

1. `cd` into the project directory
2. `mm-sdk/usr/mm/mm build`


## Download a project

1. `cd` into the project directory
2. `mm-sdk/usr/mm/mm download`