from decimal import Subnormal
from shutil import ExecError
import click
import pathlib
import json
import subprocess


TOOL_CONFFILE_NAME = '.mbed-vscode-tools.json'
TOOL_CONFFILE_INDENT_LENGTH = 4
CMAKE_ROOTDIR_NAME = 'cmake_build'
CMAKE_CONFFILE_NAME = 'mbed_config.cmake'
NINJA_BUILDFILE_NAME = 'build.ninja'
VSCODE_CONFFILE_NAME = 'c_cpp_properties.json'
VSCODE_CONFENTRY_BASE = 'Mbed'
VSCODE_CONFENTRY_GENERATED = 'MbedGenerated'


@click.group()
def cmd():
    pass


@cmd.command()
@click.argument('mbed-toolchain', type=click.Choice(['GCC_ARM', 'ARM']))
@click.argument('mbed-target', type=str)
@click.argument(
    'vscode-conf-file',
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False,
        resolve_path=True, path_type=pathlib.Path))
@click.option(
    '--mbed-profile',
    type=click.Choice(['debug', 'develop', 'release']),
    default='develop', show_default=True,
    help='Choose an mbed build profile.')
@click.option(
    '--mbed-program-dir',
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True,
        resolve_path=True, path_type=pathlib.Path),
    default=pathlib.Path().cwd(), show_default=True,
    help='Path to an mbed program directory. '
         'If not specified, it\'s set to your working directory.')
def configure(
        mbed_toolchain: str, mbed_target: str, vscode_conf_file: pathlib.Path,
        mbed_profile: str, mbed_program_dir: pathlib.Path) -> None:
    """Configure build settings.

    [MBED_TOOLCHAIN] The toolchain you are using to build your mbed application.
    Choose \'GCC_ARM\' or \'ARM\'.

    [MBED_TARGET] A build target for an mbed-enabled device (e.g. DISCO_L072CZ_LRWAN1).

    [VSCODE_CONFFILE] Path to your c_cpp_properties.json.
    Create \"Mbed\" configuration entry in the file then it will be inherited by
    \"MbedGenerated\" entry automatically created by this tool.
    Use \"MbedGenerated\" entry as the main configuration for vscode intellisense.
    """

    click.echo('[Configure]')
    cmake_build_dir = mbed_program_dir / CMAKE_ROOTDIR_NAME / mbed_target / mbed_profile / mbed_toolchain
    cmake_conf_file = cmake_build_dir / CMAKE_CONFFILE_NAME
    ninja_build_file = cmake_build_dir / NINJA_BUILDFILE_NAME

    # Check if c_cpp_properties.json exists
    if not vscode_conf_file.exists():
        raise ExecError(
            f'Could not find the specified c_cpp_properties.json ({vscode_conf_file}). '
            'Create the file first.')

    # Load c_cpp_properties
    with vscode_conf_file.open(mode='r') as file:
        vscode_conf = json.load(file)

    # Check if the specified c_cpp_properties has "Mbed" entry
    flag = False
    for entry in vscode_conf['configurations']:
        if entry['name'] == 'Mbed':
            flag = True
    if not flag:
        raise Exception(
            f'Could not find \"{VSCODE_CONFENTRY_BASE}\" entry '
            f'in your c_cpp_properties.json ({vscode_conf_file}). '
            f'This entry will be inherited by \"{VSCODE_CONFENTRY_GENERATED}\" entry automatically created by this tool. '
            f'Create \"{VSCODE_CONFENTRY_BASE}\" entry first.')
    click.echo('---- VSCode c_cpp_properties.json check done.')

    # Check if cmake build directory exists
    if not cmake_build_dir.exists():
        raise Exception(
            f'Could not find the cmake build directory ({cmake_build_dir}). '
            'Run \'$ mbed-tools configure\' properly first.')
    click.echo('---- CMake build directory check done.')

    # Check if cmake configuration file exists
    if not cmake_conf_file.exists():
        raise Exception(
            f'Could not find the cmake configuration file ({cmake_conf_file}). '
            'Run \'$ mbed-tools configure\' properly first.')
    click.echo('---- Cmake configuration file check done.')

    # Generate build.ninja
    ret = subprocess.run([
        'cmake',
        '-S', str(mbed_program_dir),
        '-B', str(cmake_build_dir),
        '-GNinja'], capture_output=True)
    if ret.returncode != 0:
        err = ret.stderr.decode('utf-8')
        raise Exception(
            'Failed to generate build.ninja for some reasons. '
            f'Below is the error output generated from cmake;\n{err}')
    click.echo(f'---- build.ninja generation done ({ninja_build_file}).')

    # Save config json file
    tool_conf_file = mbed_program_dir / TOOL_CONFFILE_NAME
    conf = {
        'mbed_toolchain': mbed_toolchain,
        'mbed_target': mbed_target,
        'mbed_profile': mbed_profile,
        'mbed_program_dir': str(mbed_program_dir),
        'vscode_conf_file': str(vscode_conf_file)}
    with tool_conf_file.open('w') as file:
        json.dump(conf, file, indent=TOOL_CONFFILE_INDENT_LENGTH)
    click.echo(f'---- Tool configuration file saved ({tool_conf_file}).')
    click.echo('---- Configuration finished!')


@cmd.command()
def update():
    click.echo('update')


def main():
    cmd()


if __name__ == '__main__':
    main()
