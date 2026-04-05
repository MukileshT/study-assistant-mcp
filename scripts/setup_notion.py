"""
Script to set up Notion workspace with required databases.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from config.settings import get_settings
from src.storage import NotionClient
from src.utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


# -------------------------
# Database Schemas
# -------------------------
def notes_database_schema():
    return {
        "Title": {"title": {}},
        "Subject": {"rich_text": {}},
        "Date": {"date": {}},
        "Topics": {"multi_select": {"options": []}},
        "Status": {"select": {"options": []}},
        "Difficulty": {"select": {"options": []}},
        "Source": {"url": {}},
        "Word Count": {"number": {"format": "number"}}
    }


def study_plans_database_schema():
    return {
        "Title": {"title": {}},
        "Goal": {"rich_text": {}},
        "Deadline": {"date": {}},
        "Status": {"select": {"options": []}},
        "Priority": {"select": {"options": []}},
        "Tasks": {"multi_select": {"options": []}}
    }


# -------------------------
# Formatting helpers
# -------------------------
def redact_secret(value: str | None, visible: int = 4) -> str:
    if not value:
        return "[not set]"
    if len(value) <= visible:
        return "*" * len(value)
    return f"{value[:visible]}...{value[-visible:]}"


# -------------------------
# Helpers
# -------------------------
async def test_connection(client: NotionClient) -> bool:
    console.print("\n[cyan]Testing Notion API connection...[/cyan]")
    if await client.health_check():
        console.print("[green]✓[/green] Connection successful!")
        return True
    else:
        console.print("[red]✗[/red] Connection failed!")
        return False


async def check_database(client: NotionClient, db_id: str) -> bool:
    try:
        await client.get_database(db_id)
        return True
    except Exception as e:
        logger.debug(f"Database check failed: {str(e)}")
        return False


async def setup_databases(client: NotionClient):
    console.print("\n[bold cyan]Setting up Notion databases...[/bold cyan]")

    settings = get_settings()

    notes_db_exists = False
    plans_db_exists = False

    if settings.notion_database_id:
        notes_db_exists = await check_database(client, settings.notion_database_id)
        if notes_db_exists:
            console.print("[green]✓[/green] Notes database already exists")

    if settings.notion_plans_database_id:
        plans_db_exists = await check_database(client, settings.notion_plans_database_id)
        if plans_db_exists:
            console.print("[green]✓[/green] Study plans database already exists")

    if notes_db_exists and plans_db_exists:
        console.print("\n[green]All databases are set up![/green]")
        return

    console.print("\n[yellow]To create databases, we need a parent page ID.[/yellow]")
    parent_page_id = Prompt.ask("\nEnter parent page ID")

    try:
        if not notes_db_exists:
            console.print("\n[cyan]Creating notes database...[/cyan]")
            notes_db_id = await client.create_database(
                parent={"type": "page_id", "page_id": parent_page_id},
                title="Study Notes",
                schema=notes_database_schema(),
            )
            console.print(f"[green]✓[/green] Created notes database: {notes_db_id}")
            console.print(f"NOTION_DATABASE_ID={notes_db_id}")

        if not plans_db_exists:
            console.print("\n[cyan]Creating study plans database...[/cyan]")
            plans_db_id = await client.create_database(
                parent={"type": "page_id", "page_id": parent_page_id},
                title="Study Plans",
                schema=study_plans_database_schema(),
            )
            console.print(f"[green]✓[/green] Created study plans database: {plans_db_id}")
            console.print(f"NOTION_PLANS_DATABASE_ID={plans_db_id}")

        console.print("\n[green]Databases created successfully![/green]")

    except Exception as e:
        console.print(f"\n[red]Error creating databases: {str(e)}[/red]")


async def create_sample_note(client: NotionClient):
    if not Confirm.ask("\nCreate a sample note to test?", default=True):
        return

    console.print("\n[cyan]Creating sample note...[/cyan]")

    try:
        sample_content = """# Sample Note

This is a test note created by the setup script.

## Key Concepts
- Concept 1: This is an important concept
- Concept 2: Another important concept

## Summary
This note demonstrates the formatting capabilities of the system.

## Next Steps
- Review the material
- Practice problems
- Ask questions
"""

        page_id = await client.create_note_page(
            title="Sample Note - Setup Test",
            content=sample_content,
            subject="Other",
            date=datetime.now(),
            topics=["Setup", "Test"],
            status="Processed",
            difficulty="Easy",
            source="Self-Study",
        )

        console.print(f"[green]✓[/green] Sample note created! Page ID: {page_id}")

    except Exception as e:
        console.print(f"[red]Error creating sample note: {str(e)}[/red]")


async def main():
    console.print(Panel.fit(
        "[bold]Study Assistant MCP - Notion Setup[/bold]\n"
        "This script will help you set up Notion integration",
        border_style="blue"
    ))

    settings = get_settings()
    console.print(f"\nAPI Key: {redact_secret(settings.notion_api_key)}")
    console.print(f"Notes Database ID: {settings.notion_database_id or '[yellow]Not set[/yellow]'}")
    console.print(f"Plans Database ID: {settings.notion_plans_database_id or '[yellow]Not set[/yellow]'}")

    client = NotionClient()

    if not await test_connection(client):
        return 1

    await setup_databases(client)

    if settings.notion_database_id:
        await create_sample_note(client)

    console.print("\n" + "=" * 60)
    console.print("[bold green]Setup Complete![/bold green]")
    console.print("=" * 60)
    console.print("\nYour Notion workspace is ready!")

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
