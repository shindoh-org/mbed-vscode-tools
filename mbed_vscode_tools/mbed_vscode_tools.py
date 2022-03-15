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
                    include = include.strip()
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
        try:
            vscode_conf = json.load(file)
        except json.JSONDecodeError:
            raise Exception(
                f'Invalid json file: {vscode_conf_file}')
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
@click.argument(
    'mbed-build-dir',
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True,
        resolve_path=True))
@click.argument(
    'vscode-conf-file',
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False,
        resolve_path=True))
@click.option(
    '--mbed-program-dir',
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True,
        resolve_path=True),
    default=pathlib.Path().cwd(), show_default=True,
    help='Path to the mbed program directory root. '
         'If not specified, it\'s set to your current working directory.')
@click.option(
    '--vscode-conf-entry',
    type=str, default=consts.VSCODE_DEFAULT_CONFENTRY_NAME, show_default=True,
    help='Specify the target config entry of your c_cpp_properties.json.')
@click.option(
    '--verbose', is_flag=True,
    help='Show complete message logs.')
def update(
        mbed_build_dir: str,
        vscode_conf_file: str,
        mbed_program_dir: str,
        vscode_conf_entry: str,
        verbose: bool) -> None:
    """Update your c_cpp_properties.json.

    [MBED_BUILD_DIR] The build directory created by \"$ mbed-tools configure -t MBED_TOOLCHAIN -m MBED_TARGET -b MBED_PROFILE\".
    Normally the directory is <path-to-your-mbed-program-directory>/cmake_build/{MBED_TARGET}/{MBED_PROFILE}/{MBED_TOOLCHAIN}.

    [VSCODE_CONF_FILE] Path to your c_cpp_properties.json.
    Make sure that your c_cpp_properties.json has an config entry whose name == --vscode-conf-entry in \"configurations\" field.
    The entry is managed and updated by this tool for correct vscode intellisense.
    """
    mbed_build_dir: pathlib.Path = pathlib.Path(mbed_build_dir)
    vscode_conf_file: pathlib.Path = pathlib.Path(vscode_conf_file)
    mbed_program_dir: pathlib.Path = pathlib.Path(mbed_program_dir)

    # Check validity of c_cpp_properties.json
    vscode_conf = validate_vscode_conf_file(vscode_conf_file, vscode_conf_entry)
    if verbose:
        click.echo(f'-- No errros found in your c_cpp_properties.json')

    # Check if cmake configuration file exists
    cmake_conf_file = mbed_build_dir / consts.CMAKE_CONFFILE_NAME
    if not cmake_conf_file.exists():
        raise Exception(
            f'Could not find the cmake config file ({cmake_conf_file}). '
            'Run the \"configure\" command of mbed-tools first.')
    if verbose:
        click.echo(f'-- The cmake config file ({cmake_conf_file}) found.')

    # Generate build.ninja
    ret = subprocess.run([
        'cmake',
        '-S', str(mbed_program_dir),
        '-B', str(mbed_build_dir),
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
    includes, defines = parse_includes_and_defines(mbed_build_dir / consts.NINJA_BUILDFILE_NAME)
    conf_entry['includePath'] = includes
    conf_entry['defines'] = defines
    click.echo(f'-- {len(includes)} include paths parsed.')
    click.echo(f'-- {len(defines)} defines parsed.')

    # Save c_cpp_properties.json
    with vscode_conf_file.open('w') as file:
        json.dump(vscode_conf, file, indent=consts.VSCODE_CONFFILE_INDENT_LENGTH)
    click.echo(f'-- Updated your c_cpp_properties.json.')

    # Success
    click.echo(click.style('UPDATE DONE', fg='green', bold=True))


def main():
    cmd()


if __name__ == '__main__':
    main()
