import click


@click.group()
def cmd():
    pass


@cmd.command()
def doctor():
    click.echo('doctor')


@cmd.command()
def update():
    click.echo('update')


def main():
    cmd()


if __name__ == '__main__':
    main()
