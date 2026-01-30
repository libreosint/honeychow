import asyncio
import csv
import json
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import aiohttp
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
)
from rich.status import Status
from rich.table import Table
from update_checker import UpdateChecker

from . import console, __version__


@dataclass
class SiteResult:
    site_name: str
    category: str
    url: str
    exists: bool
    status_code: int
    confidence: int = 100
    error: Optional[str] = None


class HoneyChow:
    # Database sources in order of priority
    DATABASE_SOURCES = [
        # "https://codeberg.org/rly0nheart/honeychow/raw/branch/master/data/honeychow-sites.json",
        "https://raw.githubusercontent.com/libreosint/honeychow/refs/heads/master/data/honeychow-sites.json",
    ]

    def __init__(
        self,
        session: aiohttp.ClientSession,
        max_concurrent: int = 50,
        quiet: bool = False,
    ):
        self.session = session
        self.max_concurrent = max_concurrent
        self.quiet = quiet
        self.sites: list[dict] = []
        self.default_headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:147.0) Gecko/20100101 Firefox/147.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

    @staticmethod
    def check_updates(status: Optional[Status] = None):
        checker = UpdateChecker()
        status.update("[dim]Checking for updates…[/dim]")
        result = checker.check(package_name="honeychow", package_version=__version__)

        if result:
            console.print(result)

    async def database_from_remote(self, status: Optional[Status] = None) -> bool:
        """
        Fetch sites database from remote sources.
        Tries multiple sources in order until one succeeds.
        Returns True if successful, False otherwise.
        """
        for source_url in self.DATABASE_SOURCES:
            domain = urlparse(source_url).netloc
            if isinstance(status, Status):
                status.update(f"[dim]Fetching sites' database from {domain}…[/dim]")
            try:
                async with self.session.get(source_url) as response:
                    if response.status == 200:
                        data = await response.json(content_type=None)
                        self.sites = data.get("sites", [])
                        if not self.quiet:
                            if isinstance(status, Status):
                                status.stop()
                            console.print(
                                f"[[bold green]+[/bold green]] Loaded {len(self.sites)} sites from {domain}"
                            )
                        return True
            except (
                aiohttp.ClientError,
                asyncio.TimeoutError,
                json.JSONDecodeError,
            ) as e:
                if isinstance(status, Status):
                    status.stop()
                console.log(
                    f"[[bold red]✘[/bold red]] Failed to fetch database: {response.status} {e}"
                )
                continue

        console.print(
            "[[bold red]✘[/bold red]] Failed to fetch sites database from all sources"
        )
        return False

    def database_from_file(
        self, filepath: str, status: Optional[Status] = None
    ) -> bool:
        """
        Load sites database from a local JSON file.
        Returns True if successful, False otherwise.
        """
        if isinstance(status, Status):
            status.update(f"[dim]Loading sites' database from: {filepath}…[/dim]")

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.sites = data.get("sites", [])
                if not self.quiet:
                    if isinstance(status, Status):
                        status.stop()
                    console.print(
                        f"[[bold green]+[/bold green]] Loaded {len(self.sites)} sites from {filepath}"
                    )
                return True
        except FileNotFoundError:
            if isinstance(status, Status):
                status.stop()
            console.print(
                f"[[bold red]✘[/bold red]] Database file not found: {filepath}"
            )
            return False
        except json.JSONDecodeError as e:
            if isinstance(status, Status):
                status.stop()
            console.print(
                f"[[bold red]✘[/bold red]] Invalid JSON in database file: {e}"
            )
            return False
        except Exception as e:
            if isinstance(status, Status):
                status.stop()
            console.print(f"[[bold red]✘[/bold red]] Failed to load database: {e}")
            return False

    def list_sites(self):
        """List all available sites"""
        table = Table(
            show_header=False,
            show_edge=False,
            show_lines=False,
            title="Available Sites",
        )
        table.add_column("Name", style="cyan")
        table.add_column("Category", style="magenta")

        for site in sorted(self.sites, key=lambda x: x.get("name", "").lower()):
            table.add_row(site.get("name", "Unknown"), site.get("category", "unknown"))

        console.print(table)
        console.print(f"\n[bold]Total: {len(self.sites)} sites[/bold]")

    def list_categories(self):
        """List all available categories"""
        categories: dict[str, int] = {}
        for site in self.sites:
            category = site.get("category", "unknown")
            categories[category] = categories.get(category, 0) + 1

        table = Table(
            show_header=False,
            show_edge=False,
            show_lines=False,
            title="Available Categories",
        )
        table.add_column("Category", style="cyan")
        table.add_column("Sites", style="green", justify="right")

        for cat, count in sorted(categories.items()):
            table.add_row(cat, str(count))

        console.print(table)

    @staticmethod
    def _prepare_url(site: dict, username: str) -> str:
        """Prepare the check URL with username substitution"""
        url = site.get("uri_check", "")

        clean_username = username
        if strip_chars := site.get("strip_bad_char"):
            for char in strip_chars:
                clean_username = clean_username.replace(char, "")

        return url.replace("{account}", clean_username)

    @staticmethod
    def _prepare_pretty_url(site: dict, username: str) -> str:
        """Get the display URL"""
        url = site.get("uri_pretty") or site.get("uri_check", "")

        clean_username = username
        if strip_chars := site.get("strip_bad_char"):
            for char in strip_chars:
                clean_username = clean_username.replace(char, "")

        return url.replace("{account}", clean_username)

    def _prepare_headers(self, site: dict) -> dict:
        """Merge default headers with site-specific headers"""
        headers = self.default_headers.copy()
        site_headers = site.get("headers") or site.get("header") or {}
        headers.update(site_headers)
        return headers

    @staticmethod
    def _prepare_post_body(site: dict, username: str) -> Optional[str]:
        """Prepare POST body if needed"""
        if post_body := site.get("post_body"):
            clean_username = username
            if strip_chars := site.get("strip_bad_char"):
                for char in strip_chars:
                    clean_username = clean_username.replace(char, "")
            return post_body.replace("{account}", clean_username)
        return None

    @staticmethod
    def _check_exists(site: dict, status_code: int, text: str) -> tuple[bool, int]:
        """Check if account exists based on response."""
        hit_code = site.get("hit_code")
        hit_string = site.get("hit_string", "")
        miss_string = site.get("miss_string", "")
        miss_code = site.get("miss_code")

        # Check for explicit "miss" indicators first
        if miss_string and miss_string in text:
            return False, 100

        if miss_code and status_code == miss_code and not hit_string:
            return False, 90

        # Check for "exists" indicators
        if hit_code and status_code == hit_code:
            if hit_string:
                if hit_string in text:
                    return True, 100
                else:
                    return False, 80
            else:
                return True, 70

        if hit_code and status_code != hit_code:
            if hit_string and hit_string in text:
                return True, 60
            return False, 80

        return False, 50

    async def _check_site(
        self,
        session: aiohttp.ClientSession,
        site: dict,
        username: str,
        semaphore: asyncio.Semaphore,
    ) -> tuple[str, SiteResult]:
        """Check a single site for username. Returns (site_name, result)"""
        site_name = site.get("name", "Unknown")
        category = site.get("category", "unknown")

        async with semaphore:
            try:
                url = self._prepare_url(site, username)
                headers = self._prepare_headers(site)
                post_body = self._prepare_post_body(site, username)

                if post_body:
                    async with session.post(
                        url, headers=headers, data=post_body
                    ) as resp:
                        status = resp.status
                        text = await resp.text()
                else:
                    async with session.get(
                        url, headers=headers, allow_redirects=True
                    ) as resp:
                        status = resp.status
                        text = await resp.text()

                exists, confidence = self._check_exists(site, status, text)

                return site_name, SiteResult(
                    site_name=site_name,
                    category=category,
                    url=self._prepare_pretty_url(site, username),
                    exists=exists,
                    status_code=status,
                    confidence=confidence,
                )

            except asyncio.TimeoutError:
                return site_name, SiteResult(
                    site_name=site_name,
                    category=category,
                    url=self._prepare_pretty_url(site, username),
                    exists=False,
                    status_code=0,
                    confidence=0,
                    error="Timeout",
                )
            except Exception as e:
                return site_name, SiteResult(
                    site_name=site_name,
                    category=category,
                    url=self._prepare_pretty_url(site, username),
                    exists=False,
                    status_code=0,
                    confidence=0,
                    error=str(e)[:50],
                )

    async def search(
        self,
        username: str,
        sites: Optional[list[str]] = None,
        categories: Optional[list[str]] = None,
        show_not_found: bool = False,
        show_failed: bool = False,
    ) -> tuple[list[SiteResult], list[SiteResult], list[SiteResult]]:
        """
        Search for username across sites.
        Returns (found, not_found, failed) tuples.
        """
        sites_to_check = self.sites

        # Filter by specific site names
        if sites:
            sites_lower = [site.lower() for site in sites]
            sites_to_check = [
                site
                for site in self.sites
                if site.get("name", "").lower() in sites_lower
            ]
            if not sites_to_check:
                console.print(
                    f"[red]No matching sites found for: {', '.join(sites)}[/red]"
                )
                return [], [], []

        # Filter by categories
        if categories:
            categories_lower = [category.lower() for category in categories]
            sites_to_check = [
                site
                for site in sites_to_check
                if site.get("category", "").lower() in categories_lower
            ]

        if not self.quiet:
            console.print(
                f"[[bold blue]~[/bold blue]] Searching for '{username}' across {len(sites_to_check)} sites...\n"
            )

        semaphore = asyncio.Semaphore(self.max_concurrent)
        found: list[SiteResult] = []
        not_found: list[SiteResult] = []
        failed: list[SiteResult] = []

        tasks = [
            self._check_site(self.session, site, username, semaphore)
            for site in sites_to_check
        ]

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("•"),
            TextColumn("[cyan]{task.fields[current_site]}[/cyan]"),
            TextColumn("•"),
            TextColumn("[green]found={task.fields[found]}[/green],"),
            TextColumn("[yellow]not_found={task.fields[not_found]}[/yellow],"),
            TextColumn("[red]failed={task.fields[failed]}[/red]"),
            TimeRemainingColumn(),
            console=console,
            disable=self.quiet,
            transient=True,
        ) as progress:
            task = progress.add_task(
                "Checking",
                total=len(tasks),
                current_site="Initialising...",
                found=0,
                not_found=0,
                failed=0,
            )

            for coroutine in asyncio.as_completed(tasks):
                site_name, result = await coroutine

                progress.update(task, advance=1, current_site=site_name)

                if result.error:
                    failed.append(result)
                    progress.update(task, failed=len(failed))
                    if show_failed and not self.quiet:
                        progress.console.print(
                            f"[[bold red]✘[/bold red]] {result.site_name}: {result.error}"
                        )
                elif result.exists:
                    found.append(result)
                    progress.update(task, found=len(found))
                    if not self.quiet:
                        progress.console.print(
                            f"[[bold green]✔[/bold green]] {result.site_name}: {result.url}"
                        )
                else:
                    not_found.append(result)
                    progress.update(task, not_found=len(not_found))
                    if show_not_found and not self.quiet:
                        progress.console.print(
                            f"[[bold yellow]✘[/bold yellow]] {result.site_name}: {result.status_code}"
                        )

        found.sort(key=lambda x: x.confidence, reverse=True)
        return found, not_found, failed

    def print_tables(
        self,
        found: list[SiteResult],
        not_found: Optional[list[SiteResult]] = None,
        failed: Optional[list[SiteResult]] = None,
        show_not_found: bool = False,
        show_failed: bool = False,
    ):
        """Pretty print results table"""
        if self.quiet:
            return

        if not found:
            console.print("\n[[bold yellow]✘[/bold yellow]] No accounts found.")
        else:
            table = Table(
                show_header=False,
                show_edge=False,
                show_lines=False,
                title=f"Found {len(found)} accounts",
                title_style="bold green",
                highlight=True,
            )
            table.add_column("Site")
            table.add_column("Category", style="yellow")
            table.add_column("URL")
            table.add_column("Confidence", justify="right")

            for result in found:
                confidence_style = "green" if result.confidence >= 80 else "yellow"
                table.add_row(
                    result.site_name,
                    result.category,
                    result.url,
                    f"[{confidence_style}]{result.confidence}%[/{confidence_style}]",
                )

            console.print(table)

        # Show not found sites if requested
        if show_not_found and not_found:
            table = Table(
                show_header=False,
                show_edge=False,
                show_lines=False,
                title=f"Not found on {len(not_found)} sites",
                title_style="bold yellow",
                highlight=True,
            )
            table.add_column("Site")
            table.add_column("Category", style="yellow")
            table.add_column("Status Code", justify="right")

            for result in not_found:
                table.add_row(
                    result.site_name, result.category, str(result.status_code)
                )

            console.print(table)

        # Show failed sites if requested
        if show_failed and failed:
            table = Table(
                show_header=False,
                show_edge=False,
                show_lines=False,
                title=f"Failed {len(failed)} sites",
                title_style="bold red",
                highlight=True,
            )
            table.add_column("Site")
            table.add_column("Category", style="yellow")
            table.add_column("Error", style="red")

            for result in failed:
                table.add_row(
                    result.site_name, result.category, result.error or "Unknown"
                )

            console.print(table)

    @staticmethod
    def print_summary(
        username: str,
        found: list[SiteResult],
        not_found: list[SiteResult],
        failed: list[SiteResult],
    ):
        """Print search summary"""
        total = len(found) + len(not_found) + len(failed)

        # Group found by category
        by_category: dict[str, int] = {}
        for result in found:
            by_category[result.category] = by_category.get(result.category, 0) + 1

        console.print("\n[bold]━━━━━━━━━━━━━ Summary ━━━━━━━━━━━━━[/bold]")
        console.print(f"[bold]Username:[/bold] '{username}'")
        console.print(f"[bold]Total sites checked:[/bold] {total}")
        console.print()
        console.print(f"[[bold green]✔[/bold green]] Found: {len(found)}")
        console.print(f"[[bold yellow]✘[/bold yellow]] Not found: {len(not_found)}")
        console.print(f"[[bold red]✘[/bold red]] Failed: {len(failed)}")
        console.print()

        success_rate = 100 * len(found) // max(1, total - len(failed))
        console.print(
            f"[bold]Success rate:[/bold] {success_rate}% ({len(found)}/{total - len(failed)})"
        )

        if by_category:
            console.print("\n[bold]Found by category:[/bold]")
            table = Table(
                show_header=False, show_edge=False, show_lines=False, highlight=True
            )
            table.add_column("Category", justify="right", style="yellow")
            table.add_column("Accounts", justify="left")
            for category, count in sorted(by_category.items(), key=lambda x: -x[1]):
                table.add_row(category, str(count))

            console.print(table)

    @staticmethod
    def export_csv(
        filepath: str,
        found: list[SiteResult],
        not_found: list[SiteResult],
        failed: list[SiteResult],
        include_all: bool = False,
    ):
        """Export results to CSV"""
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "site_name",
                    "category",
                    "url",
                    "status",
                    "status_code",
                    "confidence",
                    "error",
                ]
            )

            for result in found:
                writer.writerow(
                    [
                        result.site_name,
                        result.category,
                        result.url,
                        "found",
                        result.status_code,
                        result.confidence,
                        "",
                    ]
                )

            if include_all:
                for result in not_found:
                    writer.writerow(
                        [
                            result.site_name,
                            result.category,
                            result.url,
                            "not_found",
                            result.status_code,
                            result.confidence,
                            "",
                        ]
                    )

                for result in failed:
                    writer.writerow(
                        [
                            result.site_name,
                            result.category,
                            result.url,
                            "failed",
                            result.status_code,
                            result.confidence,
                            result.error,
                        ]
                    )

        console.print(f"[[bold green]+[/bold green]] Results exported to {filepath}")
