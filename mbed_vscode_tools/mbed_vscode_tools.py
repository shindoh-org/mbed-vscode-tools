from decimal import Subnormal
import click
import pathlib
import json
import subprocess


TOOL_CONFFILE_NAME = '.mbed-vscode-tools.json'
TOOL_CONFFILE_INDENT_LENGTH = 4
BUILD_CMAKE_ROOTDIR_NAME = 'cmake_build'
BUILD_CMAKE_CONFFILE_NAME = 'mbed_config.cmake'
BUILD_NINJA_CONFFILE_NAME = 'build.ninja'


@click.group()
def cmd():
    pass


@cmd.command()
@click.argument('toolchain', type=click.Choice(['GCC_ARM', 'ARM']))
@click.argument('mbed-target', type=str)
@click.option(
    '--profile',
    type=click.Choice(['debug', 'develop', 'release']),
    default='develop', show_default=True,
    help='Choose a build profile.')
@click.option(
    '--program-path',
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True,
        resolve_path=True, path_type=pathlib.Path),
    default=pathlib.Path().cwd(), show_default=True,
    help='Path to an mbed program directory. '
    'If not specified, it\'s set to your working directory.')
def configure(
        toolchain: str, mbed_target: str,
        profile: str, program_path: pathlib.Path) -> None:
    """Configure build settings.

    [TOOLCHAIN] The toolchain you are using to build your mbed application.
    Choose \'GCC_ARM\' or \'ARM\'.

    [MBED_TARGET] A build target for an mbed-enabled device (e.g. DISCO_L072CZ_LRWAN1).
    """

    cmake_build_dir = program_path / BUILD_CMAKE_ROOTDIR_NAME / mbed_target / profile / toolchain
    cmake_conf = cmake_build_dir / BUILD_CMAKE_CONFFILE_NAME

    # Check if cmake build directory exists
    if not cmake_build_dir.exists():
        raise Exception(
            f'Could not find the cmake build directory {cmake_build_dir} . '
            f'Run \'$ mbed-tools configure\' properly first.')

    # Check if cmake configuration file exists
    if not cmake_conf.exists():
        raise Exception(
            f'Could not find the cmake configuration file {cmake_conf} . '
            f'Run \'$ mbed-tools configure\' properly first.')

    # Save config json file
    config = {
        'toolchain': toolchain,
        'mbed_target': mbed_target,
        'profile': profile,
        'program_path': str(program_path)}
    with (program_path / TOOL_CONFFILE_NAME).open('w') as file:
        json.dump(config, file, indent=TOOL_CONFFILE_INDENT_LENGTH)

    # Generate build.ninja
    ret = subprocess.run([
        'cmake',
        '-S', str(program_path),
        '-B', str(cmake_build_dir),
        '-GNinja'], capture_output=True)
    if ret.returncode != 0:
        raise Exception(
            'Failed to generate build.ninja for some reasons. '
            'Below is the error output generated from cmake;\n%s' % ret.stderr.decode('utf-8'))


@cmd.command()
def update():
    click.echo('update')


def main():
    cmd()


if __name__ == '__main__':
    main()
