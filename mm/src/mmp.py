import util, log

DEFAULT_MMP_MANIFEST = """# This is a MadMachine project file in TOML format
# This file holds those parameters that could not be managed by SwiftPM
# Edit this file would change the behavior of the building/downloading procedure
# Those project files in the dependent libraries would be IGNORED
# Specify the board name below, there are "SwiftIOBoard" and "SwiftIOFeather" now
board = "{name}"
# Specifiy the floating-point type below, there are "soft" and "hard"
# If your code use significant floating-point calculation, plz set it to "hard"
float-type = "{float}"
# Reserved for future use 
version = 1
"""

