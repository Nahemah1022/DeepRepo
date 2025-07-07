import click
import logging
import sys
from pathlib import Path

from fmcp import mcp
from tools import register_tools

@click.command()
@click.option("--repository", "-r", type=Path, help="")
@click.option("-v", "--verbose", count=True)
def main(repository: Path | None, verbose: bool):
    register_tools(uri=repository.absolute().as_uri())
    mcp.run(transport="sse")
    logging_level = logging.WARN
    if verbose == 1:
        logging_level = logging.INFO
    elif verbose >= 2:
        logging_level = logging.DEBUG
    logging.basicConfig(level=logging_level, stream=sys.stderr)


if __name__ == "__main__":
    main()
