"""
Validation script to check system setup and configuration.
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from config.settings import get_settings
from src.core import StudyAssistantAgent
from src.utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


class ValidationResult:
    """Store validation results."""
    
    def __init__(self):
        self.checks = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0
    
    def add_check(self, name: str, status: str, message: str = ""):
        """Add a check result."""
        self.checks.append({
            "name": name,
            "status": status,
            "message": message
        })
        
        if status == "pass":
            self.passed += 1
        elif status == "fail":
            self.failed += 1
        elif status == "warning":
            self.warnings += 1
    
    def print_results(self):
        """Print validation results."""
        table = Table(title="Validation Results")
        table.add_column("Check", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Message", style="dim")
        
        for check in self.checks:
            status_text = {
                "pass": "[green]✓ PASS[/green]",
                "fail": "[red]✗ FAIL[/red]",
                "warning": "[yellow]⚠ WARNING[/yellow]"
            }[check["status"]]
            
            table.add_row(
                check["name"],
                status_text,
                check["message"]
            )
        
        console.print(table)
        
        # Summary
        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"  Passed: [green]{self.passed}[/green]")
        console.print(f"  Failed: [red]{self.failed}[/red]")
        console.print(f"  Warnings: [yellow]{self.warnings}[/yellow]")
        
        return self.failed == 0


async def validate_environment():
    """Validate environment and configuration."""
    
    console.print(Panel.fit(
        "[bold]Study Assistant MCP - Setup Validation[/bold]\n"
        "Checking system configuration and dependencies",
        border_style="blue"
    ))
    
    result = ValidationResult()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        task = progress.add_task("Validating...", total=None)
        
        # Check Python version
        progress.update(task, description="Checking Python version...")
        import sys
        if sys.version_info >= (3, 11):
            result.add_check("Python Version", "pass", f"{sys.version_info.major}.{sys.version_info.minor}")
        else:
            result.add_check("Python Version", "fail", "Python 3.11+ required")
        
        # Check dependencies
        progress.update(task, description="Checking dependencies...")
        required_packages = [
            'google.generativeai',
            'groq',
            'notion_client',
            'PIL',
            'cv2',
            'pydantic',
        ]
        
        missing = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing.append(package)
        
        if not missing:
            result.add_check("Dependencies", "pass", "All packages installed")
        else:
            result.add_check("Dependencies", "fail", f"Missing: {', '.join(missing)}")
        
        # Check configuration
        progress.update(task, description="Checking configuration...")
        try:
            settings = get_settings()
            result.add_check("Config Loading", "pass", "Settings loaded successfully")
            
            # Check API keys
            if settings.google_api_key and "your_" not in settings.google_api_key:
                result.add_check("Gemini API Key", "pass", "Configured")
            else:
                result.add_check("Gemini API Key", "fail", "Not configured or placeholder")
            
            if settings.groq_api_key and "your_" not in settings.groq_api_key:
                result.add_check("Groq API Key", "pass", "Configured")
            else:
                result.add_check("Groq API Key", "fail", "Not configured or placeholder")
            
            if settings.notion_api_key and "secret_" in settings.notion_api_key:
                result.add_check("Notion API Key", "pass", "Configured")
            else:
                result.add_check("Notion API Key", "fail", "Not configured")
            
            if settings.notion_database_id:
                result.add_check("Notion Database", "pass", "ID configured")
            else:
                result.add_check("Notion Database", "warning", "ID not configured")
            
        except Exception as e:
            result.add_check("Config Loading", "fail", str(e))
        
        # Check directories
        progress.update(task, description="Checking directories...")
        try:
            settings = get_settings()
            
            for dir_name in ['cache_dir', 'uploads_dir', 'processed_dir']:
                dir_path = getattr(settings, dir_name)
                if dir_path.exists():
                    result.add_check(f"Directory: {dir_name}", "pass", str(dir_path))
                else:
                    result.add_check(f"Directory: {dir_name}", "warning", "Will be created")
        except Exception as e:
            result.add_check("Directories", "fail", str(e))
        
        # Test API connections
        progress.update(task, description="Testing API connections...")
        try:
            agent = StudyAssistantAgent()
            
            # Test Notion
            try:
                notion_ok = await agent.notion_client.health_check()
                if notion_ok:
                    result.add_check("Notion API", "pass", "Connection successful")
                else:
                    result.add_check("Notion API", "fail", "Connection failed")
            except Exception as e:
                result.add_check("Notion API", "fail", str(e))
            
            # Test Models
            try:
                model_health = await agent.model_manager.health_check_all()
                
                for provider, status in model_health.items():
                    if status:
                        result.add_check(f"Model API: {provider}", "pass", "Connection successful")
                    else:
                        result.add_check(f"Model API: {provider}", "fail", "Connection failed")
            except Exception as e:
                result.add_check("Model APIs", "fail", str(e))
                
        except Exception as e:
            result.add_check("API Testing", "fail", str(e))
        
        # Check database
        progress.update(task, description="Checking database...")
        try:
            from src.storage import DatabaseManager
            
            db_manager = DatabaseManager()
            await db_manager.initialize()
            
            result.add_check("Local Database", "pass", "Initialized successfully")
        except Exception as e:
            result.add_check("Local Database", "fail", str(e))
    
    console.print()
    return result


async def main():
    """Run validation."""
    
    result = await validate_environment()
    
    success = result.print_results()
    
    if success:
        console.print("\n[bold green]✓ System validation passed![/bold green]")
        console.print("You're ready to start using Study Assistant MCP.")
        return 0
    else:
        console.print("\n[bold red]✗ System validation failed[/bold red]")
        console.print("Please fix the issues above before proceeding.")
        console.print("\nQuick fixes:")
        console.print("  1. Install missing dependencies: pip install -r requirements.txt")
        console.print("  2. Configure API keys in .env file")
        console.print("  3. Run setup script: python scripts/setup_notion.py")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)