import click
import pathlib
import json
import subprocess
import copy


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

    [VSCODE_CONF_FILE] Path to your c_cpp_properties.json.
    Create an \"Mbed\" entry in the file. It is inherited by
    \"MbedGenerated\" entry which will be automatically created by this tool.
    Use \"MbedGenerated\" entry for vscode intellisense.
    """

    click.echo('[Configure]')
    cmake_build_dir = \
        mbed_program_dir / \
        CMAKE_ROOTDIR_NAME / \
        mbed_target / \
        mbed_profile / \
        mbed_toolchain
    cmake_conf_file = cmake_build_dir / CMAKE_CONFFILE_NAME
    ninja_build_file = cmake_build_dir / NINJA_BUILDFILE_NAME

    # Load vscode configuration file
    with vscode_conf_file.open(mode='r') as file:
        vscode_conf = json.load(file)

    # Check validity of the specified c_cpp_properties.json
    n = len(list(filter(  # The number of "Mbed" entries
        lambda entry: entry['name'] == VSCODE_CONFENTRY_BASE,
        vscode_conf['configurations'])))
    if n < 1:  # No "Mbed" entries
        raise Exception(
            f'Could not find \"{VSCODE_CONFENTRY_BASE}\" entry in {vscode_conf_file} . '
            f'Create \"{VSCODE_CONFENTRY_BASE}\" entry first.')
    elif n > 1:  # Duplicated "Mbed" entries
        raise Exception(
            f'More than two \"{VSCODE_CONFENTRY_BASE}\" entries found in {vscode_conf_file} . '
            f'Leave one \"{VSCODE_CONFENTRY_BASE}\" entry and remove the others.')
    click.echo('---- VSCode c_cpp_properties.json check done.')

    # Check if cmake build directory exists
    if not cmake_build_dir.exists():
        raise Exception(
            f'Could not find the cmake build directory ({cmake_build_dir}). '
            'Run \'$ mbed-tools configure\' first if you haven\'t done yet.')
    click.echo('---- CMake build directory found.')

    # Check if cmake configuration file exists
    if not cmake_conf_file.exists():
        raise Exception(
            f'Could not find the cmake config file ({cmake_conf_file}). '
            'Run \'$ mbed-tools configure\' first if you haven\'t done yet.')
    click.echo('---- CMake config file found.')

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
            f'The error output generated from cmake >>\n{err}')
    click.echo('---- Generated build.ninja.')

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
    click.echo(f'---- The tool config file was saved at <{tool_conf_file}>.')
    click.echo('---- Configure succeeded!')


@cmd.command()
@click.option(
    '--tool-conf-file',
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False,
        resolve_path=True, path_type=pathlib.Path),
    default=(pathlib.Path().cwd() / TOOL_CONFFILE_NAME), show_default=True,
    help='Path to the tool configuration file (.mbed-vscode-tools-conf) generated by configure command. '
         'If not specified, it\'s set to ./.mbed-vscode-tools-conf')
@click.option(
    '--vscode-conf-file-indent-size',
    type=click.IntRange(1),
    default=4, show_default=True,
    help='Indent size of c_cpp_properties.json.')
def update(tool_conf_file: pathlib.Path, vscode_conf_file_indent_size: int) -> None:
    """Update your c_cpp_properties.json
    """

    click.echo('[Update]')

    # Check if tool configuration file exists
    if not tool_conf_file.exists():
        raise Exception(
            f'Could not find your tool configuration file at the specified path ({tool_conf_file}). '
            'Set a correct path into \'--tool-conf-path\' option if the path is incorrect, or '
            'run \'$ mbed-vscode-tools configure\' if you haven\'t done yet.')
    click.echo('---- Tool configuration file check done.')

    # Load tool configuration file
    with tool_conf_file.open('r') as file:
        tool_conf = json.load(file)
    mbed_program_dir = pathlib.Path(tool_conf['mbed_program_dir'])
    mbed_target = tool_conf['mbed_target']
    mbed_toolchain = tool_conf['mbed_toolchain']
    mbed_profile = tool_conf['mbed_profile']
    vscode_conf_file = pathlib.Path(tool_conf['vscode_conf_file'])
    cmake_build_dir = \
        mbed_program_dir / \
        CMAKE_ROOTDIR_NAME / \
        mbed_target / \
        mbed_profile / \
        mbed_toolchain

    # Check if build.ninja exists
    ninja_build_file = cmake_build_dir / NINJA_BUILDFILE_NAME
    if not ninja_build_file.exists():
        raise Exception(
            f'Could not find build.ninja at ({ninja_build_file}). '
            'Run \'$ mbed-vscode-tools configure\' first.')
    click.echo('---- build.ninja check done.')

    # Parse build.ninja
    defines, includes = [], []
    with ninja_build_file.open(mode='r') as file:
        lines = file.readlines()
        defines_done = False
        includes_done = False
        for line in lines:
            line = line.strip()

            # Parse defines
            if not defines_done and line.startswith('DEFINES = '):
                for define in line.split('-D')[1:]:  # Remove 'DEFINES = '
                    define = define.strip()
                    if define not in defines:
                        defines.append(define)
                defines_done = True

            # Parse includes
            if not includes_done and line.startswith('INCLUDES = '):
                for include in line.split('-I')[1:]:  # Remove 'INCLUDES = '
                    include = include.strip()[1:-1]  # Remove "" both side
                    if include not in includes:
                        includes.append(include)
                includes_done = True

            # Termination
            if defines_done and includes_done:
                break

    # Manually add one include
    # TODO: Should parse this automatically as well
    includes.append(str(cmake_build_dir / '_deps' / 'greentea-client-src' / 'include'))

    # Show parse results
    click.echo(f'---- {len(defines)} defines found.')
    click.echo(f'---- {len(includes)} include paths found.')

    # Load c_cpp_properties.json
    with vscode_conf_file.open(mode='r') as file:
        vscode_conf = json.load(file)

    # Get "Mbed" entry
    base = next(filter(
        lambda entry: entry['name'] == VSCODE_CONFENTRY_BASE,
        vscode_conf['configurations']))

    # Create "MbedGenerated" entry
    generated = copy.deepcopy(base)
    generated['name'] = VSCODE_CONFENTRY_GENERATED

    # Update includes
    if 'includePath' not in generated:
        generated['includePath'] = []
    generated['includePath'].extend(includes)

    # Update defines
    if 'defines' not in generated:
        generated['defines'] = []
    generated['defines'].extend(defines)

    # Create and save new c_cpp_properties.json
    entries = list(filter(lambda entry: entry['name'] != VSCODE_CONFENTRY_GENERATED, vscode_conf['configurations']))
    entries.append(generated)
    vscode_conf['configurations'] = entries
    with vscode_conf_file.open('w') as file:
        json.dump(vscode_conf, file, indent=vscode_conf_file_indent_size)
    click.echo(f'---- VSCode configuration file updated ({vscode_conf_file}).')

    # Parse includes in build.ninja
    click.echo('---- Update finished!')


def main():
    cmd()


if __name__ == '__main__':
    main()
