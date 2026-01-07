"""
Script to test API connections and model clients.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from config.settings import get_settings
from src.models import GeminiClient, GroqClient, ModelManager
from src.utils.logger import get_logger

console = Console()
logger = get_logger(__name__)


async def test_gemini():
    """Test Gemini API connection."""
    console.print("\n[bold cyan]Testing Gemini API...[/bold cyan]")
    
    try:
        settings = get_settings()
        client = GeminiClient(
            api_key=settings.google_api_key,
            model_name=settings.vision_model,
        )
        
        # Test basic generation
        response = await client.generate(
            prompt="Say 'Hello from Gemini!' in exactly 5 words.",
            max_tokens=20,
        )
        
        if response.success:
            console.print(f"[green]✓[/green] Gemini API working!")
            console.print(f"  Response: {response.content}")
            console.print(f"  Tokens used: {response.tokens_used}")
            return True
        else:
            console.print(f"[red]✗[/red] Gemini API failed: {response.error}")
            return False
            
    except Exception as e:
        console.print(f"[red]✗[/red] Gemini test error: {str(e)}")
        return False


async def test_groq():
    """Test Groq API connection."""
    console.print("\n[bold cyan]Testing Groq API...[/bold cyan]")
    
    try:
        settings = get_settings()
        client = GroqClient(
            api_key=settings.groq_api_key,
            model_name=settings.text_model,
        )
        
        # Test basic generation
        response = await client.generate(
            prompt="Say 'Hello from Groq!' in exactly 5 words.",
            max_tokens=20,
        )
        
        if response.success:
            console.print(f"[green]✓[/green] Groq API working!")
            console.print(f"  Response: {response.content}")
            console.print(f"  Tokens used: {response.tokens_used}")
            return True
        else:
            console.print(f"[red]✗[/red] Groq API failed: {response.error}")
            return False
            
    except Exception as e:
        console.print(f"[red]✗[/red] Groq test error: {str(e)}")
        return False


async def test_model_manager():
    """Test ModelManager."""
    console.print("\n[bold cyan]Testing ModelManager...[/bold cyan]")
    
    try:
        manager = ModelManager()
        
        # Test text generation
        response = await manager.generate(
            prompt="What is 2+2? Answer in one word.",
            task="text",
            max_tokens=10,
        )
        
        if response.success:
            console.print(f"[green]✓[/green] ModelManager working!")
            console.print(f"  Response: {response.content}")
            console.print(f"  Model: {response.provider}/{response.model}")
            return True
        else:
            console.print(f"[red]✗[/red] ModelManager failed: {response.error}")
            return False
            
    except Exception as e:
        console.print(f"[red]✗[/red] ModelManager test error: {str(e)}")
        return False


async def test_all_models():
    """Test all model capabilities."""
    console.print("\n[bold cyan]Testing All Model Capabilities...[/bold cyan]")
    
    manager = ModelManager()
    
    # Test different tasks
    tasks = [
        ("text", "Explain photosynthesis in one sentence."),
        ("analyze", "List 3 key concepts in machine learning."),
        ("format", "Format this as markdown: Title, bullet 1, bullet 2"),
    ]
    
    results = []
    
    for task, prompt in tasks:
        try:
            response = await manager.generate(
                prompt=prompt,
                task=task,
                max_tokens=100,
            )
            
            results.append({
                "task": task,
                "success": response.success,
                "model": f"{response.provider}/{response.model}",
                "tokens": response.tokens_used,
            })
            
        except Exception as e:
            results.append({
                "task": task,
                "success": False,
                "model": "N/A",
                "tokens": 0,
                "error": str(e)
            })
    
    # Display results table
    table = Table(title="Model Task Tests")
    table.add_column("Task", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Model", style="yellow")
    table.add_column("Tokens", justify="right")
    
    for result in results:
        status = "✓" if result["success"] else "✗"
        table.add_row(
            result["task"],
            status,
            result["model"],
            str(result["tokens"])
        )
    
    console.print(table)
    
    return all(r["success"] for r in results)


async def main():
    """Run all API tests."""
    console.print(Panel.fit(
        "[bold]Study Assistant MCP - API Testing[/bold]\n"
        "Testing all API connections and model clients",
        border_style="blue"
    ))
    
    results = {}
    
    # Test each component
    results["Gemini"] = await test_gemini()
    results["Groq"] = await test_groq()
    results["ModelManager"] = await test_model_manager()
    results["All Tasks"] = await test_all_models()
    
    # Summary
    console.print("\n" + "=" * 60)
    console.print("[bold]Test Summary[/bold]")
    console.print("=" * 60)
    
    for name, success in results.items():
        status = "[green]PASSED[/green]" if success else "[red]FAILED[/red]"
        console.print(f"  {name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        console.print("\n[bold green]✓ All tests passed![/bold green]")
        console.print("Your API keys are configured correctly.")
        return 0
    else:
        console.print("\n[bold red]✗ Some tests failed[/bold red]")
        console.print("Please check your API keys in the .env file.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)