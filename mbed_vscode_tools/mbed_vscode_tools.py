from decimal import Subnormal
import click
import pathlib
import json
import subprocess


TOOL_CONFFILE_NAME = '.mbed-vscode-tools.json'
TOOL_CONFFILE_INDENT_LENGTH = 4
CMAKE_ROOTDIR_NAME = 'cmake_build'
CMAKE_CONFFILE_NAME = 'mbed_config.cmake'
NINJA_BUILDFILE_NAME = 'build.ninja'


@click.group()
def cmd():
    pass


@cmd.command()
@click.argument('mbed-toolchain', type=click.Choice(['GCC_ARM', 'ARM']))
@click.argument('mbed-target', type=str)
@click.option(
    '--mbed-profile',
    type=click.Choice(['debug', 'develop', 'release']),
    default='develop', show_default=True,
    help='Choose an mbed build profile.')
@click.option(
    '--mbed-program-path',
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True,
        resolve_path=True, path_type=pathlib.Path),
    default=pathlib.Path().cwd(), show_default=True,
    help='Path to an mbed program directory. '
    'If not specified, it\'s set to your working directory.')
def configure(
        mbed_toolchain: str, mbed_target: str,
        mbed_profile: str, mbed_program_path: pathlib.Path) -> None:
    """Configure build settings.

    [MBED_TOOLCHAIN] The toolchain you are using to build your mbed application.
    Choose \'GCC_ARM\' or \'ARM\'.

    [MBED_TARGET] A build target for an mbed-enabled device (e.g. DISCO_L072CZ_LRWAN1).
    """

    click.echo('[Configure]')
    cmake_build_dir = mbed_program_path / CMAKE_ROOTDIR_NAME / mbed_target / mbed_profile / mbed_toolchain
    cmake_conf_file = cmake_build_dir / CMAKE_CONFFILE_NAME
    ninja_build_file = cmake_build_dir / NINJA_BUILDFILE_NAME

    # Check if cmake build directory exists
    if not cmake_build_dir.exists():
        raise Exception(
            f'Could not find the cmake build directory {cmake_build_dir} . '
            'Run \'$ mbed-tools configure\' properly first.')
    click.echo('---- CMake build directory check done.')

    # Check if cmake configuration file exists
    if not cmake_conf_file.exists():
        raise Exception(
            f'Could not find the cmake configuration file {cmake_conf_file} . '
            'Run \'$ mbed-tools configure\' properly first.')
    click.echo('---- Cmake configuration file check done.')

    # Generate build.ninja
    ret = subprocess.run([
        'cmake',
        '-S', str(mbed_program_path),
        '-B', str(cmake_build_dir),
        '-GNinja'], capture_output=True)
    if ret.returncode != 0:
        raise Exception(
            'Failed to generate build.ninja for some reasons. '
            'Below is the error output generated from cmake;\n%s' % ret.stderr.decode('utf-8'))
    click.echo(f'---- build.ninja generation done ({ninja_build_file}).')

    # Save config json file
    tool_conf_file = mbed_program_path / TOOL_CONFFILE_NAME
    conf = {
        'mbed_toolchain': mbed_toolchain,
        'mbed_target': mbed_target,
        'mbed_profile': mbed_profile,
        'program_path': str(mbed_program_path)}
    with tool_conf_file.open('w') as file:
        json.dump(conf, file, indent=TOOL_CONFFILE_INDENT_LENGTH)
    click.echo(f'---- Tool configuration file saved ({tool_conf_file})')
    click.echo(f'---- Configuration finished!')


@cmd.command()
def update():
    click.echo('update')


def main():
    cmd()


if __name__ == '__main__':
    main()
