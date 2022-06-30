import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
# "packages": ["os"] is used as example only
build_exe_options = {'includes': ["tkinter"], "packages": ["os"], "optimize" : "1",
                     "include_files" : ["images/", "test_specs.txt", "Data files/"]}

# base="Win32GUI" should be used only for Windows GUI app
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name = "Char Application",
    version = "1.1.0",
    description = "Char Application for Honeywell Liquid Flow Sensor",
    options = {"build_exe": build_exe_options},
    executables = [Executable("main.py", base=base, targetName="Honeywell Liquid Flow Char Application", icon="images\Honeywell App Icon.ico")]
)