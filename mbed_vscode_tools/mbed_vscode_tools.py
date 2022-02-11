import click
import pathlib
import json


CONFFILE_NAME = '.mbed-vscode-tools-conf'
CONFFILE_INDENT_LENGTH = 4


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

    # Save config json file
    config = {
        'toolchain': toolchain,
        'mbed_target': mbed_target,
        'profile': profile,
        'program_path': str(program_path)}
    with (program_path / CONFFILE_NAME).open('w') as file:
        json.dump(config, file, indent=CONFFILE_INDENT_LENGTH)


@cmd.command()
def update():
    click.echo('update')


def main():
    cmd()


if __name__ == '__main__':
    main()
