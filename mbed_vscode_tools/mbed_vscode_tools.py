import click
import pathlib
import json
import subprocess
from . import consts
from typing import Tuple, List


def parse_includes_and_defines(ninja_build_file: pathlib.Path) -> Tuple[List[str], List[str]]:
    """Parse include paths and defines from build.ninja file."""
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
    includes.append(str(ninja_build_file.parent / '_deps' / 'greentea-client-src' / 'include'))
    return (includes, defines)


def validate_vscode_conf_file(
        vscode_conf_file: pathlib.Path,
        vscode_conf_entry: str) -> dict:
    """Validate c_cpp_properties.json an return it as a dict."""
    with vscode_conf_file.open(mode='r') as file:
        vscode_conf = json.load(file)
    n = len(list(filter(
        lambda entry: entry['name'] == vscode_conf_entry,
        vscode_conf['configurations'])))
    if n < 1:  # No "Mbed" entry
        raise Exception(
            f'Could not find \"{vscode_conf_entry}\" config entry in your c_cpp_properties.json ({vscode_conf_file}).')
    elif n > 1:  # Prohibit more than two "Mbed" entries
        raise Exception(
            f'More than two \"{vscode_conf_entry}\" config entries found in <{vscode_conf_file}>. '
            f'Leave one \"{vscode_conf_entry}\" entry and remove the others.')
    return vscode_conf


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
    help='Path to your mbed program directory. '
         'If not specified, it\'s set to your current working directory.')
@click.option(
    '--vscode-conf-entry',
    type=str, default='Mbed', show_default=True,
    help='Specify the target config entry of your c_cpp_properties.json.')
@click.option(
    '--verbose', is_flag=True,
    help='Show complete message logs.')
def configure(
        mbed_toolchain: str, mbed_target: str, vscode_conf_file: pathlib.Path,
        mbed_profile: str, mbed_program_dir: pathlib.Path, vscode_conf_entry: str, verbose: bool) -> None:
    """Configure and save the build settings.

    [MBED_TOOLCHAIN] The toolchain you are using to build your mbed application.
    Choose \"GCC_ARM\" or \"ARM\".

    [MBED_TARGET] A build target for an mbed-enabled device (e.g. DISCO_L072CZ_LRWAN1).

    [VSCODE_CONF_FILE] Path to your c_cpp_properties.json.
    Make sure that your c_cpp_properties.json has an config entry whose name == --vscode-conf-entry in \"configurations\" field.
    The entry is managed and updated by this tool for correct vscode intellisense.
    """
    cmake_build_dir = \
        mbed_program_dir / \
        consts.CMAKE_ROOTDIR_NAME / \
        mbed_target / \
        mbed_profile / \
        mbed_toolchain
    cmake_conf_file = cmake_build_dir / consts.CMAKE_CONFFILE_NAME

    # Load c_cpp_properties.json
    with vscode_conf_file.open(mode='r') as file:
        vscode_conf = json.load(file)
    if verbose:
        click.echo(f'-- Your c_cpp_properties.json ({vscode_conf_file}) found and loaded.')

    # Check validity of c_cpp_properties.json
    vscode_conf = validate_vscode_conf_file(vscode_conf_file, vscode_conf_entry)
    if verbose:
        click.echo(f'-- No errros found in your c_cpp_properties.json')

    # Check if cmake build directory exists
    if not cmake_build_dir.exists():
        raise Exception(
            f'Could not find the cmake build directory ({cmake_build_dir}). '
            'Run \"$ mbed-tools configure\" first.')
    if verbose:
        click.echo(f'-- The cmake build directory ({cmake_build_dir}) found.')

    # Check if cmake configuration file exists
    if not cmake_conf_file.exists():
        raise Exception(
            f'Could not find the cmake config file ({cmake_conf_file}). '
            'Run \"$ mbed-tools configure\" first.')
    if verbose:
        click.echo(f'-- The cmake config file ({cmake_conf_file}) found.')

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
            f'Here\'s the error output from cmake >>\n{err}')
    if verbose:
        click.echo(f'-- Succeeded to generate build.ninja.')

    # Get "Mbed" entry
    conf_entry = next(filter(
        lambda entry: entry['name'] == vscode_conf_entry,
        vscode_conf['configurations']))

    # Update "Mbed" entry
    ninja_build_file = cmake_build_dir / consts.NINJA_BUILDFILE_NAME
    includes, defines = parse_includes_and_defines(ninja_build_file)
    conf_entry['includePath'] = includes
    conf_entry['defines'] = defines

    # Save c_cpp_properties.json
    with vscode_conf_file.open('w') as file:
        json.dump(vscode_conf, file, indent=consts.VSCODE_CONFFILE_INDENT_LENGTH)
    click.echo(f'-- Updated your c_cpp_properties.json.')

    # Save config json file
    tool_conf_file = mbed_program_dir / consts.TOOL_CONFFILE_NAME
    tool_conf = {  # TODO: convert to relative paths
        'mbed_toolchain': mbed_toolchain,
        'mbed_target': mbed_target,
        'mbed_profile': mbed_profile,
        'mbed_program_dir': str(mbed_program_dir),
        'cmake_build_dir': str(cmake_build_dir),
        'cmake_conf_file': str(cmake_conf_file),
        'vscode_conf_file': str(vscode_conf_file),
        'vscode_conf_entry': vscode_conf_entry,
        'ninja_build_file': str(ninja_build_file)}
    with tool_conf_file.open('w') as file:
        json.dump(tool_conf, file, indent=consts.TOOL_CONFFILE_INDENT_LENGTH)
    click.echo(f'-- Saved your tool config file as <{tool_conf_file}>.')

    # Success
    click.echo(click.style('[CONFIGURE DONE]', fg='green', bold=True))


@cmd.command()
@click.option(
    '--tool-conf-file',
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False,
        resolve_path=True, path_type=pathlib.Path),
    default=(pathlib.Path().cwd() / consts.TOOL_CONFFILE_NAME), show_default=True,
    help=f'Path to the tool config file ({consts.TOOL_CONFFILE_NAME}) generated by configure command. '
         f'If not specified, it\'s set to ./{consts.TOOL_CONFFILE_NAME}')
@click.option(
    '--verbose', is_flag=True,
    help='Show complete message logs.')
def update(tool_conf_file: pathlib.Path, verbose: bool) -> None:
    """Update your c_cpp_properties.json"""

    # Load tool config file
    if not tool_conf_file.exists():
        raise Exception(
            f'Could not find your tool config file at <{tool_conf_file}>.'
            'Set a correct path into \'--tool-conf-path\' option, or '
            'run \"$ mbed-vscode-tools configure\" if you haven\'t done yet.')
    with tool_conf_file.open('r') as file:
        tool_conf = json.load(file)
    if verbose:
        click.echo(f'-- Your tool config file ({tool_conf_file}) found and loaded.')

    # Check if build.ninja exists
    vscode_conf_file = pathlib.Path(tool_conf['vscode_conf_file'])
    ninja_build_file = pathlib.Path(tool_conf['ninja_build_file'])
    if not ninja_build_file.exists():
        raise Exception(
            f'Could not find build.ninja at <{ninja_build_file}>. '
            'Run \"$ mbed-vscode-tools configure\" first.')
    if verbose:
        click.echo(f'-- Found build.ninja at <{ninja_build_file}>.')

    # Parse build.ninja
    includes, defines = parse_includes_and_defines(ninja_build_file)
    if verbose:
        click.echo('-- ' + click.style(f'{len(includes)}', fg='white', bold=True) + ' include paths parsed.')
        click.echo('-- ' + click.style(f'{len(defines)}', fg='white', bold=True) + ' defines parsed.')

    # Load c_cpp_properties.json
    if not vscode_conf_file.exists():
        raise Exception(
            f'Could not find your c_cpp_properties.json at <{vscode_conf_file}>, '
            f'though the tool config file ({tool_conf_file}) points it. '
            'Run \"$ mbed-vscode-tools configure\" again to fix this problem.')
    with vscode_conf_file.open(mode='r') as file:
        vscode_conf = json.load(file)
    if verbose:
        click.echo(f'-- Your c_cpp_properties ({vscode_conf_file}) found and loaded.')

    # Get target config entry
    vscode_conf_entry = tool_conf['vscode_conf_entry']
    conf_entry = next(filter(
        lambda entry: entry['name'] == vscode_conf_entry,
        vscode_conf['configurations']))

    # Update target config entry
    conf_entry['includePath'] = includes
    conf_entry['defines'] = defines

    # Save c_cpp_properties.json
    with vscode_conf_file.open('w') as file:
        json.dump(vscode_conf, file, indent=consts.VSCODE_CONFFILE_INDENT_LENGTH)
    click.echo(f'-- Updated your c_cpp_properties.json.')

    # Success
    click.echo(click.style('[UPDATE DONE]', fg='green', bold=True))


def main():
    cmd()


if __name__ == '__main__':
    main()
