"""Beautiful terminal output using Rich."""

from typing import Optional

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.text import Text

from .speedtest import SpeedTestResult

console = Console()


def create_progress() -> Progress:
    """Create a progress bar for speed tests."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=40),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    )


def format_speed(speed: Optional[float], unit: str = "Mbps") -> Text:
    """Format speed with color based on value."""
    if speed is None:
        return Text("N/A", style="dim")
    
    # Color based on speed (for Mbps)
    if unit == "Mbps":
        if speed >= 100:
            style = "bold green"
        elif speed >= 25:
            style = "green"
        elif speed >= 10:
            style = "yellow"
        else:
            style = "red"
    else:
        style = "cyan"
    
    return Text(f"{speed:.2f} {unit}", style=style)


def format_latency(latency: Optional[float]) -> Text:
    """Format latency with color based on value."""
    if latency is None:
        return Text("N/A", style="dim")
    
    if latency < 20:
        style = "bold green"
    elif latency < 50:
        style = "green"
    elif latency < 100:
        style = "yellow"
    else:
        style = "red"
    
    return Text(f"{latency:.2f} ms", style=style)


def format_jitter(jitter: Optional[float]) -> Text:
    """Format jitter with color based on value."""
    if jitter is None:
        return Text("N/A", style="dim")
    
    if jitter < 5:
        style = "bold green"
    elif jitter < 15:
        style = "green"
    elif jitter < 30:
        style = "yellow"
    else:
        style = "red"
    
    return Text(f"{jitter:.2f} ms", style=style)


def format_quality_score(score: Optional[int]) -> Text:
    """Format quality score with color and label."""
    if score is None:
        return Text("N/A", style="dim")
    
    if score >= 90:
        style = "bold green"
        label = "Excellent"
    elif score >= 70:
        style = "green"
        label = "Good"
    elif score >= 50:
        style = "yellow"
        label = "Fair"
    elif score >= 30:
        style = "rgb(255,165,0)"  # Orange
        label = "Poor"
    else:
        style = "red"
        label = "Bad"
    
    return Text(f"{score}/100 ({label})", style=style)


def format_dns(dns_ms: Optional[float]) -> Text:
    """Format DNS lookup time with color."""
    if dns_ms is None:
        return Text("N/A", style="dim")
    
    if dns_ms < 20:
        style = "bold green"
    elif dns_ms < 50:
        style = "green"
    elif dns_ms < 100:
        style = "yellow"
    else:
        style = "red"
    
    return Text(f"{dns_ms:.2f} ms", style=style)


def format_change(value: float, is_improvement: bool, unit: str = "") -> Text:
    """Format a change value with appropriate color and arrow."""
    if is_improvement:
        arrow = "↑" if value > 0 else "↓"
        style = "green"
    else:
        arrow = "↑" if value > 0 else "↓"
        style = "red"
    
    return Text(f"{arrow} {abs(value):.2f}{unit}", style=style)


def display_result(result: SpeedTestResult) -> None:
    """Display a speed test result in a beautiful panel."""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Metric", style="bold")
    table.add_column("Value")
    
    # Quality score at the top if available
    if result.quality_score is not None:
        table.add_row("⭐ Quality Score", format_quality_score(result.quality_score))
        table.add_row("", "")  # Spacer
    
    # Speed metrics
    if result.download_mbps is not None:
        table.add_row("⬇  Download", format_speed(result.download_mbps))
    
    if result.upload_mbps is not None:
        table.add_row("⬆  Upload", format_speed(result.upload_mbps))
    
    table.add_row("", "")  # Spacer
    
    # Latency metrics
    if result.latency_ms is not None:
        table.add_row("⏱  Latency (idle)", format_latency(result.latency_ms))
    
    if result.loaded_latency_ms is not None and result.loaded_latency_ms > 0:
        table.add_row("⏱  Latency (loaded)", format_latency(result.loaded_latency_ms))
    
    if result.jitter_ms is not None:
        table.add_row("📊 Jitter", format_jitter(result.jitter_ms))
    
    if result.ttfb_ms is not None and result.ttfb_ms > 0:
        table.add_row("🚀 TTFB", format_latency(result.ttfb_ms))
    
    if result.dns_ms is not None and result.dns_ms > 0:
        table.add_row("🔍 DNS Lookup", format_dns(result.dns_ms))
    
    # Add server info
    table.add_row("", "")  # Spacer
    
    if result.server_location:
        table.add_row("🌐 Server", Text(result.server_location, style="cyan"))
    
    if result.client_ip:
        table.add_row("💻 Your IP", Text(result.client_ip, style="dim"))
    
    # Create panel
    panel = Panel(
        table,
        title="[bold cyan]Speed Test Results[/bold cyan]",
        subtitle=f"[dim]{result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}[/dim]",
        border_style="cyan",
    )
    
    console.print()
    console.print(panel)
    console.print()


def display_comparison(current: SpeedTestResult, comparison: dict) -> None:
    """Display current result with comparison to previous."""
    table = Table(show_header=True, box=None, padding=(0, 2))
    table.add_column("Metric", style="bold")
    table.add_column("Current")
    table.add_column("Previous", style="dim")
    table.add_column("Change")
    
    for key, data in comparison.items():
        current_val = data["current"]
        previous_val = data["previous"]
        
        # Format current value
        if "latency" in key or "jitter" in key:
            current_text = format_latency(current_val) if "latency" in key else format_jitter(current_val)
            previous_text = Text(f"{previous_val:.2f} ms", style="dim")
        else:
            current_text = format_speed(current_val)
            previous_text = Text(f"{previous_val:.2f} Mbps", style="dim")
        
        # Format change
        change_text = format_change(
            data["percent_change"],
            data["is_improvement"],
            "%"
        )
        
        table.add_row(
            f"{'⬇' if 'download' in key else '⬆' if 'upload' in key else '⏱' if 'latency' in key else '📊'}  {data['name']}",
            current_text,
            previous_text,
            change_text,
        )
    
    # Add server info
    table.add_row("", "", "", "")
    if current.server_location:
        table.add_row("🌐 Server", Text(current.server_location, style="cyan"), "", "")
    if current.client_ip:
        table.add_row("💻 Your IP", Text(current.client_ip, style="dim"), "", "")
    
    panel = Panel(
        table,
        title="[bold cyan]Speed Test Results (vs Previous)[/bold cyan]",
        subtitle=f"[dim]{current.timestamp.strftime('%Y-%m-%d %H:%M:%S')}[/dim]",
        border_style="cyan",
    )
    
    console.print()
    console.print(panel)
    console.print()


def display_history(results: list) -> None:
    """Display history in a table."""
    if not results:
        console.print("[yellow]No history found.[/yellow]")
        return
    
    table = Table(title="Speed Test History", box=None)
    table.add_column("Date", style="dim")
    table.add_column("Download", justify="right")
    table.add_column("Upload", justify="right")
    table.add_column("Latency", justify="right")
    table.add_column("Jitter", justify="right")
    table.add_column("Server", style="cyan")
    
    for result in results:
        table.add_row(
            result.timestamp.strftime("%Y-%m-%d %H:%M"),
            f"{result.download_mbps:.1f}" if result.download_mbps else "-",
            f"{result.upload_mbps:.1f}" if result.upload_mbps else "-",
            f"{result.latency_ms:.1f}" if result.latency_ms else "-",
            f"{result.jitter_ms:.1f}" if result.jitter_ms else "-",
            result.server_location or "-",
        )
    
    console.print()
    console.print(table)
    console.print()


def display_statistics(stats: dict) -> None:
    """Display statistics from history."""
    if not stats:
        console.print("[yellow]No statistics available. Run some tests first![/yellow]")
        return
    
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Stat", style="bold")
    table.add_column("Value")
    
    table.add_row("Total Tests", str(stats.get("total_tests", 0)))
    table.add_row("First Test", stats.get("first_test", "N/A")[:10])
    table.add_row("Last Test", stats.get("last_test", "N/A")[:10])
    table.add_row("", "")
    
    if "download_mbps_avg" in stats:
        table.add_row(
            "Download (avg/min/max)",
            f"{stats['download_mbps_avg']:.1f} / {stats['download_mbps_min']:.1f} / {stats['download_mbps_max']:.1f} Mbps"
        )
    
    if "upload_mbps_avg" in stats:
        table.add_row(
            "Upload (avg/min/max)",
            f"{stats['upload_mbps_avg']:.1f} / {stats['upload_mbps_min']:.1f} / {stats['upload_mbps_max']:.1f} Mbps"
        )
    
    if "latency_ms_avg" in stats:
        table.add_row(
            "Latency (avg/min/max)",
            f"{stats['latency_ms_avg']:.1f} / {stats['latency_ms_min']:.1f} / {stats['latency_ms_max']:.1f} ms"
        )
    
    if "jitter_ms_avg" in stats:
        table.add_row(
            "Jitter (avg/min/max)",
            f"{stats['jitter_ms_avg']:.1f} / {stats['jitter_ms_min']:.1f} / {stats['jitter_ms_max']:.1f} ms"
        )
    
    panel = Panel(
        table,
        title="[bold cyan]Speed Test Statistics[/bold cyan]",
        border_style="cyan",
    )
    
    console.print()
    console.print(panel)
    console.print()


def print_banner() -> None:
    """Print the check-cli banner."""
    banner = """
[bold cyan]
     _____ _               _    
    / ____| |             | |   
   | |    | |__   ___  ___| | __
   | |    | '_ \ / _ \/ __| |/ /
   | |____| | | |  __/ (__|   < 
    \_____|_| |_|\___|\___|_|\_\\
[/bold cyan]
    [dim]Internet Speed Test Tool[/dim]
"""
    console.print(banner)


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[bold red]Error:[/bold red] {message}")


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[bold green]✓[/bold green] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[bold blue]ℹ[/bold blue] {message}")
