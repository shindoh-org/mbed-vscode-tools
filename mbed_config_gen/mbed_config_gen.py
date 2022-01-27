# coding: utf-8
# mbed_config_gen.py

import argparse
import json
import logging
import pathlib

from typing import Iterable, List, Tuple

from mbed_tools.build._internal.config.assemble_build_config \
    import Config, assemble_config
from mbed_tools.build._internal.config.source \
    import ConfigSetting
from mbed_tools.build.exceptions import MbedBuildError
from mbed_tools.lib.json_helpers import decode_json_file
from mbed_tools.project import MbedProgram
from mbed_tools.targets import get_target_by_name

logger = logging.getLogger(__name__)

def _parse_command_line_arguments():
    # Parse the command-line arguments
    # Refer to cli/configure.py in mbed_tools repository (v2.1.0)
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--toolchain", type=str, required=True,
                        choices=["ARM", "GCC_ARM"],
                        help="Toolchain to build the application " \
                             "(e.g., ARM, GCC_ARM)")
    parser.add_argument("-m", "--mbed-target", type=str, required=True,
                        help="Build target for an Mbed-enabled device " \
                             "(e.g., DISCO_L072CZ_LRWAN1)")
    parser.add_argument("-p", "--program-path", type=str, default=".",
                        help="Path to the Mbed program " \
                             "(e.g., the current working directory)")
    parser.add_argument("-b", "--profile", type=str, default="develop",
                        help="Build type (release, develop, or debug)")
    parser.add_argument("--mbed-os-path", type=str, default=None,
                        help="Path to the Mbed OS root (mbed-os directory)")
    parser.add_argument("--custom-targets-json", type=str, default=None,
                        help="Path to the custom_targets.json")
    parser.add_argument("--cmake-build-dir", type=str, default=None,
                        help="Path to the CMake build directory")
    parser.add_argument("--app-config", type=str, default=None,
                        help="Path to the application configuration file " \
                             "(e.g., mbed_app.json)")

    parser.add_argument("--output", type=str, required=True,
                        choices=["Header", "VSCode"],
                        help="Type of the generated file")
    parser.add_argument("--additional-macros-path", type=str, default=None,
                        help="Path to the file with additional macros")
    parser.add_argument("--vscode-config-path", type=str, default=None,
                        help="Path to the Visual Studio Code C/C++ " \
                             "properties file")
    parser.add_argument("--vscode-config-name", type=str, default=None,
                        help="Name of the updated configuration in the " \
                             "Visual Studio Code C/C++ properties file")
    parser.add_argument("--header-path", type=str, required=None,
                        help="Path to the generated C/C++ header file")

    args = parser.parse_args()

    return args

def _setup_mbed_program(args) -> MbedProgram:
    # Setup Mbed program
    # Refer to cli/configure.py in mbed_tools repository (v2.1.0)

    # Build a path to the CMake build outputs
    # E.g., DISCO_L072CZ_LRWAN1/develop/GCC_ARM
    cmake_build_subdir = pathlib.Path(args.mbed_target.upper(),
                                      args.profile.lower(),
                                      args.toolchain.upper())

    # Setup Mbed program information
    if args.mbed_os_path is None:
        program = MbedProgram.from_existing(
            pathlib.Path(args.program_path), cmake_build_subdir)
    else:
        program = MbedProgram.from_existing(
            pathlib.Path(args.program_path), cmake_build_subdir,
            pathlib.Path(args.mbed_os_path))

    # Override the path to the custom_targets.json
    if args.custom_targets_json is not None:
        program.files.custom_targets_json = \
            pathlib.Path(args.custom_targets_json)
    # Override the path to the CMake build directory
    if args.cmake_build_dir is not None:
        program.files.cmake_build_dir = pathlib.Path(args.cmake_build_dir)
    # Override the path to the application configuration file
    if args.app_config is not None:
        program.files.app_config_file = pathlib.Path(args.app_config)

    return program

def _load_raw_targets_data(program: MbedProgram):
    # Refer to build/config.py in mbed_tools repository (v2.1.0)
    # Read the targets.json in Mbed OS (mbed-os/targets/targets.json)
    targets_data = decode_json_file(program.mbed_os.targets_json_file)

    # Read the custom_targets.json if available
    if not program.files.custom_targets_json.exists():
        return targets_data

    custom_targets_data = decode_json_file(program.files.custom_targets_json)

    for custom_target in custom_targets_data:
        if custom_target in targets_data:
            raise MbedBuildError(
                f"Error found in {program.files.custom_targets_json}.\n"
                f"A target with the name `{custom_target}` already exists in "
                f"{program.mbed_os.targets_json_file}. Please give your "
                f"custom target a unique name so it can be identified.")

    targets_data.update(custom_targets_data)
    return targets_data

def _generate_config(target_name: str, program: MbedProgram) -> Config:
    # Generate configuration for the build target and Mbed program
    # Refer to build/config.py in mbed_tools repository (v2.1.0)

    # Read the targets.json and custom_targets.json
    targets_data = _load_raw_targets_data(program)
    # Get a dictionary of attributes for the build target
    target_build_attributes = get_target_by_name(target_name, targets_data)
    # Create a configuration for the build target and Mbed program
    mbed_lib_search_paths = [program.root, program.mbed_os.root]
    config = assemble_config(target_build_attributes, mbed_lib_search_paths,
                             program.files.app_config_file)

    return config

def _generate_config_for_cmake(config: Config, target_name: str,
                               toolchain_name: str) -> Config:
    # Create a configuration for the CMakeLists.txt
    # Refer to build/_internal/cmake_file.py in mbed_tools repository (v2.1.0)
    supported_c_libs = config["supported_c_libs"][toolchain_name.lower()]
    return { "target_name": target_name,
             "toolchain_name": toolchain_name,
             "supported_c_libs": list(supported_c_libs),
             **config }

def _load_additional_macros(additional_macros_path: str) -> List[str]:
    additional_macros_path = pathlib.Path(additional_macros_path)
    additional_macros = additional_macros_path.read_text().splitlines()
    additional_macros = [x.strip() for x in additional_macros]
    return additional_macros

def _sanitize_config(config: ConfigSetting) -> Tuple[str, str]:
    if type(config.value) is bool:
        config_value = str(int(config.value))
    else:
        config_value = str(config.value)

    if config.macro_name is not None:
        config_name = config.macro_name
    else:
        config_name = "MBED_CONF_{}_{}".format(
            config.namespace.upper().replace("-", "_"),
            config.name.upper().replace("-", "_"))

    return config_name, config_value

def _sanitize_macro(macro: str) -> Tuple[str, str]:
    return macro.split("=", 1) if "=" in macro else (macro, None)

def _extract_macro_name(entry_name: str):
    return entry_name.split("=", 1)[0] if "=" in entry_name else entry_name

def _generate_c_cpp_defines(mbed_config: Config, mbed_program: MbedProgram,
    additional_macros: Iterable[str]) -> List[Tuple[str, str]]:
    # Append Mbed configurations and macros to the defines
    c_cpp_defines = {}

    # Append definitions (e.g., MBED_CONF_*_PRESENT) from compile_time_defs.txt
    # generated by Mbed CMake toolchain
    # Open mbed-os/compile_time_defs.txt in CMake build directory if exists
    compile_time_defs_path = mbed_program.files.cmake_build_dir \
        / "mbed-os" / "compile_time_defs.txt"

    if compile_time_defs_path.is_file():
        logger.warning(
            f"Compile-time definitions {compile_time_defs_path} "
            f"generated by Mbed CMake toolchain is being used. Make sure "
            f"that `mbed-tools configure` is run before using this tool.")
        compile_defs = compile_time_defs_path.read_text()
        # Split by the beginning of the definition and one single quote
        compile_defs = compile_defs.split("'-D")
        # Remove whitespaces from the both sides
        compile_defs = [x.strip() for x in compile_defs]
        # Remove the rightmost occurrence of a single quote
        compile_defs = ["".join(x.rsplit("'", 1)) for x in compile_defs]
        # Remove empty strings
        compile_defs = [x for x in compile_defs if len(x) > 0]
        # Append the compile-time definitions
        macros = [_sanitize_macro(x) for x in compile_defs]
        macros = { k: v for k, v in macros }
        c_cpp_defines.update(macros)

    mbed_configs: Iterable[ConfigSetting] = mbed_config["config"]
    mbed_macros: Iterable[str] = mbed_config["macros"]

    for config in mbed_configs:
        if config.value is None:
            continue

        # Sanitize the configuration name and its corresponding value
        config_name, config_value = _sanitize_config(config)
        if config_name in c_cpp_defines and \
           c_cpp_defines[config_name] != config_value:
            logger.warning(f"Macro {config_name} will be overridden. "
                           f"Old value: {c_cpp_defines[config_name]}, "
                           f"New value: {config_value}")
        c_cpp_defines[config_name] = config_value

    for macro in mbed_macros:
        # Sanitize the macro name and its corresponding definition
        macro_name, macro_value = _sanitize_macro(macro)
        if macro_name in c_cpp_defines and \
           c_cpp_defines[macro_name] != macro_value:
            logger.warning(f"Macro {macro_name} will be overridden. "
                           f"Old value: {c_cpp_defines[macro_name]}, "
                           f"New value: {macro_value}")
        c_cpp_defines[macro_name] = macro_value

    for macro in additional_macros:
        # Sanitize the macro name and its corresponding definition
        macro_name, macro_value = _sanitize_macro(macro)
        if macro_name in c_cpp_defines and \
           c_cpp_defines[macro_name] != macro_value:
            logger.warning(f"Macro {macro_name} will be overridden. "
                           f"Old value: {c_cpp_defines[macro_name]}, "
                           f"New value: {macro_value}")
        c_cpp_defines[macro_name] = macro_value

    # Sort the definitions by names in an ascending order
    c_cpp_defines = sorted(c_cpp_defines.items(), key=lambda x: x[0])
    return c_cpp_defines

def _update_vscode_settings(mbed_config: Config, mbed_program: MbedProgram,
                            vscode_config_path: str, vscode_config_name: str,
                            additional_macros_path: str):
    # Check that c_cpp_properties.json exists
    if vscode_config_path is not None:
        vscode_config_path = pathlib.Path(vscode_config_path)
    else:
        vscode_config_path = mbed_program.root \
            / ".vscode" / "c_cpp_properties.json"

    if not vscode_config_path.exists():
        raise FileNotFoundError(
            f"{vscode_config_path} does not exist. "
            f"It should be first created in Visual Studio Code.")

    # Check that the specified configuration entry is not None
    if vscode_config_name is None:
        raise ValueError(
            f"Configuration name should be provided using "
            f"--vscode-config-name option")

    # Check that the configuration entry exists
    properties = json.loads(vscode_config_path.read_text())
    c_cpp_config = next((c for c in properties["configurations"] \
                         if c["name"] == vscode_config_name), None)

    if c_cpp_config is None:
        raise RuntimeError(
            f"Configuration `{vscode_config_name}` was not found in the "
            f"Visual Studio Code C/C++ properties file {vscode_config_path}.")

    # Read the predefined macros if available
    if additional_macros_path is not None:
        additional_macros = _load_additional_macros(additional_macros_path)
    else:
        additional_macros = []

    # Append Mbed configurations and macros to the defines
    # Refer to build/_internal/templates/mbed_config.tmpl
    # in mbed_tools repository (v2.1.0)
    c_cpp_defines = _generate_c_cpp_defines(
        mbed_config, mbed_program, additional_macros)

    # Update Mbed configurations and macros
    c_cpp_defines = [k if v is None else f"{k}={v}" for k, v in c_cpp_defines]
    c_cpp_config["defines"] = c_cpp_defines
    # Update the c_cpp_properties.json
    vscode_config_path.write_text(json.dumps(properties, indent=4))
    print(f"{vscode_config_path} has been successfully updated.")

def _generate_cpp_header(mbed_config: Config, mbed_program: MbedProgram,
                         header_path: str, additional_macros_path: str):
    # Check that the path is valid
    if header_path is not None:
        header_path = pathlib.Path(header_path)

        if header_path.exists() and not header_path.is_file():
            raise ValueError(
                f"Path {header_path} already exists and is not a file.")
    else:
        header_path = mbed_program.root / "mbed_config.h"

    # Read the predefined macros if available
    if additional_macros_path is not None:
        additional_macros = _load_additional_macros(additional_macros_path)
    else:
        additional_macros = []

    # Collect macros and their corresponding definitions
    c_cpp_defines = _generate_c_cpp_defines(
        mbed_config, mbed_program, additional_macros)

    # Generate the C/C++ header using Mbed configurations and macros
    include_guard = map(lambda x: x.upper() if x.isalnum() else "_",
                        header_path.name)
    include_guard = "".join(include_guard)
    header_content = f"\n" \
                     f"// {header_path.name}\n\n" \
                     f"// Automatically generated configuration file.\n" \
                     f"// Do not edit. Content may be overwritten.\n\n" \
                     f"#ifndef {include_guard}\n" \
                     f"#define {include_guard}\n\n"

    for macro_name, macro_value in c_cpp_defines:
        if macro_value is None:
            header_content += f"#define {macro_name}\n"
        else:
            header_content += f"#define {macro_name} {macro_value}\n"

    header_content += f"\n" \
                      f"#endif {include_guard}\n"

    # Generate the C/C++ header
    header_path.write_text(header_content)
    print(f"{header_path} has been successfully created.")

def main():
    # Parse the command-line arguments
    args = _parse_command_line_arguments()
    # Setup Mbed program
    program = _setup_mbed_program(args)

    # Generate the configuration for the Mbed program
    config = _generate_config(args.mbed_target.upper(), program)
    # Generate the configuration for CMake
    config = _generate_config_for_cmake(
        config, args.mbed_target.upper(), args.toolchain)

    if args.output == "Header":
        # Generate C/C++ header
        _generate_cpp_header(config, program,
                             args.header_path, args.additional_macros_path)
    elif args.output == "VSCode":
        # Update C/C++ settings for Visual Studio Code
        _update_vscode_settings(config, program,
                                args.vscode_config_path,
                                args.vscode_config_name,
                                args.additional_macros_path)

if __name__ == "__main__":
    main()
