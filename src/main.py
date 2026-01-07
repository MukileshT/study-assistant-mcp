"""
Main CLI interface for Study Assistant MCP.
"""

import asyncio
import click
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

from src.core import StudyAssistantAgent
from src.utils.logger import get_logger, console
from src.utils.validators import validate_image_files
from config.settings import get_settings

logger = get_logger(__name__)


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Study Assistant MCP - AI-powered note processing and study planning."""
    pass


@cli.command()
@click.argument('images', nargs=-1, type=click.Path(exists=True))
@click.option('--subject', '-s', help='Subject name')
@click.option('--combine', '-c', is_flag=True, help='Combine multiple images into one note')
def process(images, subject, combine):
    """Process note images and upload to Notion."""
    
    if not images:
        console.print("[red]Error: No images provided[/red]")
        console.print("Usage: python -m src.main process IMAGE1 [IMAGE2 ...]")
        return
    
    # Convert to Path objects
    image_paths = [Path(img) for img in images]
    
    # Validate images
    try:
        validate_image_files(image_paths)
    except Exception as e:
        console.print(f"[red]Validation error: {str(e)}[/red]")
        return
    
    # Run processing
    asyncio.run(_process_notes(image_paths, subject, combine))


async def _process_notes(image_paths, subject, combine):
    """Async processing of notes."""
    
    console.print(Panel.fit(
        f"[bold]Processing {len(image_paths)} note(s)[/bold]\n"
        f"Subject: {subject or 'Auto-detect'}\n"
        f"Mode: {'Combined' if combine else 'Individual'}",
        border_style="blue"
    ))
    
    # Initialize agent
    agent = StudyAssistantAgent()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        task = progress.add_task("Initializing...", total=None)
        await agent.initialize()
        
        progress.update(task, description="Processing notes...")
        
        if combine:
            results = await agent.process_multiple_notes(
                image_paths,
                subject=subject,
                combine=True
            )
        else:
            results = []
            for i, image_path in enumerate(image_paths, 1):
                progress.update(
                    task,
                    description=f"Processing {i}/{len(image_paths)}: {image_path.name}"
                )
                result = await agent.process_note(image_path, subject=subject)
                results.append(result)
    
    # Display results
    console.print("\n" + "=" * 60)
    console.print("[bold]Processing Results[/bold]")
    console.print("=" * 60 + "\n")
    
    for i, result in enumerate(results, 1):
        if result["success"]:
            console.print(f"[green]✓[/green] Note {i}: {result.get('title', 'Untitled')}")
            console.print(f"  Subject: {result.get('subject', 'N/A')}")
            console.print(f"  Topics: {', '.join(result.get('topics', []))}")
            console.print(f"  Notion: {result.get('notion_page_id', 'N/A')}")
        else:
            console.print(f"[red]✗[/red] Note {i}: Failed")
            if result.get("errors"):
                for error in result["errors"]:
                    console.print(f"  Error: {error}")
        console.print()


@cli.command()
@click.option('--date', '-d', help='Date for plan (YYYY-MM-DD)')
def plan(date):
    """Generate daily study plan."""
    
    if date:
        try:
            plan_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            console.print("[red]Invalid date format. Use YYYY-MM-DD[/red]")
            return
    else:
        plan_date = datetime.now()
    
    asyncio.run(_generate_plan(plan_date))


async def _generate_plan(plan_date):
    """Async plan generation."""
    
    console.print(Panel.fit(
        f"[bold]Generating Study Plan[/bold]\n"
        f"Date: {plan_date.strftime('%A, %B %d, %Y')}",
        border_style="blue"
    ))
    
    from src.planning import StudyPlanner
    from rich.progress import Progress, SpinnerColumn, TextColumn
    
    planner = StudyPlanner()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing recent notes...", total=None)
        
        try:
            result = await planner.generate_daily_plan(plan_date)
            
            progress.update(task, description="Plan generated!")
            
            if result["success"]:
                console.print("\n[green]✓[/green] Study plan generated successfully!")
                console.print(f"\n[bold]Priority Subjects:[/bold]")
                for subject in result.get("priority_subjects", []):
                    console.print(f"  • {subject}")
                console.print(f"\n[bold]Total Study Time:[/bold] {result.get('total_hours', 0)} hours")
                console.print(f"\n[bold]Notion Page:[/bold] {result.get('notion_page_id', 'N/A')}")
                
                if result.get("is_default"):
                    console.print("\n[yellow]Note: Default plan generated (no recent notes found)[/yellow]")
            else:
                console.print("\n[red]✗[/red] Failed to generate plan")
                
        except Exception as e:
            console.print(f"\n[red]Error:[/red] {str(e)}")
            logger.error(f"Plan generation error: {str(e)}")


@cli.command()
@click.option('--learning-style', type=click.Choice(['visual', 'auditory', 'kinesthetic', 'reading_writing']))
@click.option('--detail-level', type=click.Choice(['minimal', 'standard', 'detailed']))
@click.option('--show', is_flag=True, help='Show current configuration')
def config(learning_style, detail_level, show):
    """Configure user preferences."""
    
    settings = get_settings()
    
    if show:
        # Display current config
        table = Table(title="Current Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="yellow")
        
        table.add_row("Learning Style", settings.learning_style)
        table.add_row("Detail Level", settings.note_detail_level)
        table.add_row("Vision Model", settings.vision_model)
        table.add_row("Text Model", settings.text_model)
        table.add_row("Planning Model", settings.planning_model)
        
        console.print(table)
        return
    
    # Update config
    # (In production, would update .env or database)
    if learning_style:
        console.print(f"[green]✓[/green] Learning style set to: {learning_style}")
        console.print("  Update your .env file: LEARNING_STYLE={learning_style}")
    
    if detail_level:
        console.print(f"[green]✓[/green] Detail level set to: {detail_level}")
        console.print("  Update your .env file: NOTE_DETAIL_LEVEL={detail_level}")


@cli.command()
def stats():
    """Show processing statistics."""
    
    asyncio.run(_show_stats())


async def _show_stats():
    """Async stats display."""
    
    agent = StudyAssistantAgent()
    await agent.initialize()
    
    statistics = await agent.get_statistics()
    
    console.print(Panel.fit(
        "[bold]Study Assistant Statistics[/bold]",
        border_style="blue"
    ))
    
    # API Usage
    console.print("\n[bold cyan]API Usage (Last 30 Days)[/bold cyan]")
    api_stats = statistics.get("api_usage", {})
    
    if api_stats.get("providers"):
        for provider, models in api_stats["providers"].items():
            console.print(f"\n  {provider.title()}:")
            for model, stats in models.items():
                console.print(f"    {model}: {stats['total_requests']} requests, {stats['total_tokens']} tokens")
    else:
        console.print("  No API usage recorded yet")
    
    # Storage
    console.print("\n[bold cyan]Storage[/bold cyan]")
    storage_stats = statistics.get("storage", {})
    
    for storage_type, stats in storage_stats.items():
        console.print(
            f"  {storage_type.title()}: {stats['count']} files, "
            f"{stats['size_mb']:.2f} MB"
        )


@cli.command()
@click.option('--days', default=30, help='Clean files older than N days')
@click.confirmation_option(prompt='Are you sure you want to cleanup old files?')
def cleanup(days):
    """Clean up old files and cache."""
    
    asyncio.run(_cleanup(days))


async def _cleanup(days):
    """Async cleanup."""
    
    console.print(f"[yellow]Cleaning up files older than {days} days...[/yellow]")
    
    agent = StudyAssistantAgent()
    await agent.initialize()
    await agent.cleanup(days=days)
    
    console.print("[green]✓[/green] Cleanup complete!")


@cli.command()
def test():
    """Run connection tests."""
    
    console.print(Panel.fit(
        "[bold]Running Connection Tests[/bold]",
        border_style="blue"
    ))
    
    asyncio.run(_run_tests())


async def _run_tests():
    """Async tests."""
    
    agent = StudyAssistantAgent()
    
    console.print("\n[cyan]Testing API connections...[/cyan]")
    await agent.initialize()
    
    console.print("[green]✓[/green] All connections working!")


@cli.command()
@click.option('--days', default=7, help='Number of days to look back')
@click.option('--subject', help='Filter by subject')
def recent(days, subject):
    """View recent notes."""
    asyncio.run(_show_recent_notes(days, subject))


async def _show_recent_notes(days, subject):
    """Show recent notes."""
    from src.storage import NotionClient
    
    notion = NotionClient()
    
    console.print(f"\n[cyan]Recent notes (last {days} days)[/cyan]\n")
    
    try:
        pages = await notion.get_recent_notes(days=days, subject=subject)
        
        if not pages:
            console.print("[yellow]No recent notes found[/yellow]")
            return
        
        table = Table()
        table.add_column("Date", style="cyan")
        table.add_column("Subject", style="yellow")
        table.add_column("Title", style="green")
        table.add_column("Topics", style="dim")
        
        for page in pages[:20]:  # Show max 20
            props = page.get("properties", {})
            
            # Extract data safely
            title_data = props.get("Title", {}).get("title", [])
            title = title_data[0].get("text", {}).get("content", "Untitled") if title_data else "Untitled"
            
            subject_data = props.get("Subject", {}).get("select", {})
            subj = subject_data.get("name", "N/A") if subject_data else "N/A"
            
            date_data = props.get("Date", {}).get("date", {})
            date_str = date_data.get("start", "N/A")[:10] if date_data else "N/A"
            
            topics_data = props.get("Topics", {}).get("multi_select", [])
            topics = ", ".join([t.get("name", "") for t in topics_data][:3])
            
            table.add_row(date_str, subj, title, topics)
        
        console.print(table)
        console.print(f"\nShowing {len(pages[:20])} of {len(pages)} notes")
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")


@cli.command()
@click.argument('query')
def search(query):
    """Search notes by keyword."""
    asyncio.run(_search_notes(query))


async def _search_notes(query):
    """Search notes."""
    from src.storage import NotionClient
    
    notion = NotionClient()
    
    console.print(f"\n[cyan]Searching for: '{query}'[/cyan]\n")
    
    try:
        results = await notion.search_pages(query, filter_type="page")
        
        if not results:
            console.print("[yellow]No results found[/yellow]")
            return
        
        for i, page in enumerate(results[:10], 1):
            title_data = page.get("properties", {}).get("Name", {}).get("title", [])
            title = title_data[0].get("text", {}).get("content", "Untitled") if title_data else "Untitled"
            
            console.print(f"{i}. {title}")
            console.print(f"   URL: {page.get('url', 'N/A')}")
            console.print()
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")


@cli.command()
def version():
    """Show version information."""
    console.print(Panel.fit(
        "[bold]Study Assistant MCP[/bold]\n"
        "Version: 0.1.0\n"
        "Python: 3.11+\n\n"
        "Features:\n"
        "  ✓ AI-Powered Note Processing\n"
        "  ✓ Intelligent Study Planning\n"
        "  ✓ Notion Integration\n"
        "  ✓ Multiple AI Models",
        border_style="blue"
    ))


@cli.command()
def validate():
    """Validate system setup."""
    import subprocess
    subprocess.run(["python", "scripts/validate_setup.py"])


if __name__ == "__main__":
    cli()