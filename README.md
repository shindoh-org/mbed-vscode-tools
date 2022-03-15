
# VSCode Intellisense For Your Mbed Projects

`mbed-vscode-tools` is made for software engineers who want to develop their mbed projects in vscode instead of mbed studio.
The tool offers a commandline interface to generate and update your c_cpp_properties.json for correct vscode intellisense.

## Notes

* This tool works in conjunction with the official cli tool (`mbed-tools`) provided by the mbed team.
* We assume that the users know how to use mbed-tools and its workflow. Otherwise see [the official docs](https://os.mbed.com/docs/mbed-os/v6.15/build-tools/use.html). 

## Dependencies

Python interpreter:

* python >= 3.6.0 (f strings are used in our code)

Python packages:

* 8.0.0 > click >= 7.0.0 (the latest mbed-tools requires click 7.x)

Other softwares:

* mbed-tools >= 7.0.0
* arm-none-eabi-gcc >= 9.0.0 or armcc >= 6.0.0
* cmake >= 3.19.0
* ninja >= 1.0.0

## Installation

```bash
$ pip install mbed-vscode-tools
```

Run `$ pip uninstall mbed-vscode-tools` to uninstall mbed-vscode-tools.

## Tutorial

### Create c_cpp_properties.json

Prepare your c_cpp_properties.json **that has \"Mbed\" configuration entry** like below:

```json
{
    "env": {},
    "configurations": [
        {
            // "Mbed" entry will be automatically managed and updated by this tool.
            "name": "Mbed",
            "compilerPath": "/usr/bin/arm-none-eabi-gcc",  // Path to an arm compiler executable to use
            "includePath": [],       // Leave empty
            "defines": [],           // Leave empty
            "cStandard": "c17",      // Set your favorite
            "cppStandard": "c++17",  // Set your favorite
            "intelliSenseMode": "gcc-arm"  // Depends on your compiler
        }
    ],
    "version": 4
}
```

### Configure build settings for your mbed project

Make sure you're at the mbed program directory root.

Run the following command:

```bash
$ mbed-tools configure -t MBED_TOOLCHAIN -m MBED_TARGET -b MBED_PROFILE
```

* `MBED_TOOLCHAIN` (required)  
  Set \"GCC_ARM\" if you like to use a gnu arm compiler. If use a paid official arm c/c++ compiler, set \"ARM\" instead.
* `MBED_TARGET` (required)  
  Set your mbed-enabled board identifier. You can easily find it by connecting your board via usb and run `$ mbed-tools detect`.  
  The \"Build target(s)\" field is what you are looking for.
* `MBED_PROFILE` (optional)  
  Choose an mbed build profile from \"debug\", \"develop\", or \"release\". The default parameter is \"develop\".

### Update your c_cpp_properties.json

Make sure you're at the mbed program directory root.

Run the following command to update your c_cpp_properties.json:

```bash
$ mbed-vscode-tools update ./cmake_build/{MBED_TARGET}/{MBED_PROFILE}/{MBED_TOOLCHAIN} VSCODE_CONF_FILE
```

* `VSCODE_CONF_FILE` (required)  
  Path to your c_cpp_properties.json.

If everything goes well, `includePath` and `defines` fields of your c_cpp_properties.json are automatically updated and your vscode intellisense works fine.

**Run this command right after every execution of the configure command of mbed-tools.**

## Documentation

### `update`

Update your c_cpp_properties.json.

```
$ mbed-vscode-tools update MBED_BUILD_DIR VSCODE_CONF_FILE [--mbed-program-dir str] [--vscode-conf-entry str] [--verbose store_true] [--help store_true]
```

**Positional arguments**:

* `MBED_BUILD_DIR`  
  The build directory created by the configure command of mbed-tools. If MBED_PROGRAM_DIR is the mbed program directory root,
  MBED_TOOLCHAIN is the mbed toolchain, MBED_PROFILE is the mbed build profile, and MBED_TARGET is your mbed-enabled board identifier,
  then the directory will be created as {MBED_PROGRAM_DIR}/cmake_build/{MBED_TARGET}/{MBED_PROFILE}/{MBED_TOOLCHAIN} by
  `$ mbed-tools configure -t MBED_TOOLCHAIN -m MBED_TARGET -b MBED_PROFILE -p MBED_PROGRAM_DIR`.
* `VSCODE_CONF_FILE`  
  Path to your c_cpp_properties.json.

**Options**

* `--mbed-program-dir`  
  Path to the mbed program directory root. If not specified, it\'s set to your current working directory.
* `--vscode-conf-entry`  
  Specify the target config entry of your c_cpp_properties.json.
  The default parameter is \"Mbed\".
* `--verbose`  
  Show complete message logs.
* `--help`  
  Show help messages.
