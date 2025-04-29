import click
from pathlib import Path
import logging
import sys
from .server import serve

@click.command()
@click.option("--endpoint", "-r", type=Path, help="")
@click.option("-v", "--verbose", count=True)
def main(endpoint: str | None, verbose: bool) -> None:
    """MCP Git Server - Git functionality for MCP"""
    import asyncio

    logging_level = logging.WARN
    if verbose == 1:
        logging_level = logging.INFO
    elif verbose >= 2:
        logging_level = logging.DEBUG

    logging.basicConfig(level=logging_level, stream=sys.stderr)
    asyncio.run(serve(endpoint))

if __name__ == "__main__":
    main()
