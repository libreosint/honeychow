import asyncio

import aiohttp
from rich.status import Status

from ._cli import parse_args
from ._core import console, HoneyChow


async def main():
    args = parse_args()

    try:
        timeout = aiohttp.ClientTimeout(total=args.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            honeychow = HoneyChow(
                session=session, max_concurrent=args.workers, quiet=args.quiet
            )

            with Status(status="[dim]Initialising…[/dim]") as status:
                honeychow.check_updates(status=status)

                # Fetch sites from remote
                if not await honeychow.fetch_sites(status=status):
                    return

            # Handle --list-sites
            if args.list_sites:
                honeychow.list_sites()
                return

            # Handle --list-categories
            if args.list_categories:
                honeychow.list_categories()
                return

            # Require username for search
            if not args.username:
                console.print(
                    "[bold yellow]✘[/bold yellow] Username required for search"
                )
                console.print("Use --help for usage information")
                return

            found, not_found, failed = await honeychow.search(
                args.username,
                sites=args.sites,
                categories=args.categories,
                show_not_found=args.not_found,
                show_failed=args.failed,
            )

            honeychow.print_results(
                found=found,
                not_found=not_found,
                failed=failed,
                show_not_found=args.not_found,
                show_failed=args.failed,
            )
            honeychow.print_summary(
                username=args.username, found=found, not_found=not_found, failed=failed
            )

            # Export to CSV if requested
            if args.output:
                honeychow.export_csv(
                    filepath=args.output,
                    found=found,
                    not_found=not_found,
                    failed=failed,
                    include_all=args.output_all,
                )
    except KeyboardInterrupt:
        console.log(
            f"[bold yellow]✘[/bold yellow] User interruption detected ([bold yellow]CTRL+C[/bold yellow])"
        )


def start():
    asyncio.run(main())
