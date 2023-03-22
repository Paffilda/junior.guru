import click

from juniorguru.cli import (cancel_previous_builds, check_bot, check_docs, check_links,
                            data, participant, screenshots, students, sync, web,
                            winners, backup)
from juniorguru.cli.dev import main as dev
from juniorguru.lib.cli import load_command


subcommands = click.Group(commands=dict(map(load_command, [
    backup,
    cancel_previous_builds,
    check_docs,
    check_links,
    check_bot,
    web,
    data,
    participant,
    screenshots,
    winners,
    students,
    sync,
])))


main = click.CommandCollection(sources=[dev, subcommands])
