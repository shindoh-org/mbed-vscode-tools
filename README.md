
# VSCode Intellisense For Your Mbed Projects

`mbed-vscode-tools` is made for software engineers who want to develop their mbed projects in vscode instead of mbed studio.
The tool offers a commandline interface to generate and update your c_cpp_properties.json for correct vscode intellisense.

## Notes

* This tool works in conjunction with the official cli tool (`mbed-tools`) provided by the mbed team.
* Currently this tool supports only `arm-none-eabi-gcc` as the arm compiler.
* We assume that the reader knows how to use mbed-tools and its workflow; otherwise see [the official docs](https://os.mbed.com/docs/mbed-os/v6.15/build-tools/use.html). 

## Dependencies

Python interpreter:

* python >= 3.6.0 (f strings are used in the source)

Python packages:

* click >= 8.0.0

Other softwares:

* mbed-tools >= 7.0.0
* arm-none-eabi-gcc >= 9.0.0
* cmake >= 3.19.0
* ninja >= 1.0.0

## Installation

```bash
$ pip install mbed-vscode-tools
```

Run `$ pip uninstall mbed-vscode-tools` for uninstall.

## Quick Start

## Usage

```
Usage: mbed-vscode-tools [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  configure  Configure your build settings.
  generate   Generate a template of your c_cpp_properties.json for quick...
  update     Update your c_cpp_properties.json
```

### `generate`
### `configure`
### `update`

## Trouble Shooting
