"""Main CLI entry point for check-cli."""

import click
from rich.live import Live

from . import __version__
from .display import (
    console,
    create_progress,
    display_comparison,
    display_history,
    display_result,
    display_statistics,
    print_banner,
    print_error,
    print_info,
    print_success,
)
from .history import (
    clear_history,
    compare_results,
    get_last_n_results,
    get_last_result,
    get_statistics,
    save_result,
)
from .speedtest import (
    run_download_test,
    run_latency_test,
    run_speed_test,
    run_upload_test,
)


def run_with_progress(test_func, description: str):
    """Run a test function with a progress display."""
    progress = create_progress()
    tasks = {}
    
    def progress_callback(phase: str, value: float, detail: str = ""):
        task_names = {
            "info": "Getting server info",
            "latency": "Measuring latency",
            "download": "Testing download",
            "upload": "Testing upload",
        }
        
        task_name = task_names.get(phase, phase)
        if detail:
            task_name = f"{task_name} ({detail})"
        
        if phase not in tasks:
            tasks[phase] = progress.add_task(task_name, total=1.0)
        
        progress.update(tasks[phase], completed=value, description=task_name)
    
    with Live(progress, console=console, refresh_per_second=10):
        result = test_func(progress_callback)
    
    return result


@click.group(invoke_without_command=True)
@click.option("--version", "-v", is_flag=True, help="Show version and exit.")
@click.pass_context
def cli(ctx, version):
    """Check - A beautiful CLI tool to test your internet speed.
    
    Run 'check speed' for a full speed test, or use subcommands for specific tests.
    
    \b
    Examples:
      check speed      Full speed test (download, upload, latency, jitter)
      check download   Download speed only
      check upload     Upload speed only
      check latency    Latency and jitter only
      check history    View past results
      check stats      View statistics
    """
    if version:
        console.print(f"[cyan]check-cli[/cyan] version [bold]{__version__}[/bold]")
        return
    
    if ctx.invoked_subcommand is None:
        print_banner()
        console.print(ctx.get_help())


@cli.command()
@click.option("--no-save", is_flag=True, help="Don't save result to history.")
@click.option("--no-compare", is_flag=True, help="Don't compare with previous result.")
def speed(no_save, no_compare):
    """Run a full speed test (download, upload, latency, jitter).
    
    This is the most comprehensive test that measures all aspects of your
    internet connection.
    """
    print_banner()
    print_info("Starting full speed test...")
    console.print()
    
    try:
        result = run_with_progress(run_speed_test, "Running speed test")
        
        # Get previous result for comparison
        previous = get_last_result() if not no_compare else None
        
        # Save result
        if not no_save:
            save_result(result)
            print_success("Result saved to history")
        
        # Display result
        if previous and not no_compare:
            comparison = compare_results(result, previous)
            if comparison:
                display_comparison(result, comparison)
            else:
                display_result(result)
        else:
            display_result(result)
            
    except Exception as e:
        print_error(f"Speed test failed: {e}")
        raise click.Abort()


@cli.command()
@click.option("--no-save", is_flag=True, help="Don't save result to history.")
def download(no_save):
    """Test download speed only.
    
    Measures your download bandwidth by fetching files of various sizes
    from Cloudflare's servers.
    """
    print_banner()
    print_info("Testing download speed...")
    console.print()
    
    try:
        result = run_with_progress(run_download_test, "Testing download")
        
        if not no_save:
            save_result(result)
        
        display_result(result)
        
    except Exception as e:
        print_error(f"Download test failed: {e}")
        raise click.Abort()


@cli.command()
@click.option("--no-save", is_flag=True, help="Don't save result to history.")
def upload(no_save):
    """Test upload speed only.
    
    Measures your upload bandwidth by sending data to Cloudflare's servers.
    """
    print_banner()
    print_info("Testing upload speed...")
    console.print()
    
    try:
        result = run_with_progress(run_upload_test, "Testing upload")
        
        if not no_save:
            save_result(result)
        
        display_result(result)
        
    except Exception as e:
        print_error(f"Upload test failed: {e}")
        raise click.Abort()


@cli.command()
@click.option("--no-save", is_flag=True, help="Don't save result to history.")
def latency(no_save):
    """Test latency and jitter only.
    
    Measures network latency (ping) and jitter (variation in latency)
    to Cloudflare's servers.
    """
    print_banner()
    print_info("Testing latency and jitter...")
    console.print()
    
    try:
        result = run_with_progress(run_latency_test, "Testing latency")
        
        if not no_save:
            save_result(result)
        
        display_result(result)
        
    except Exception as e:
        print_error(f"Latency test failed: {e}")
        raise click.Abort()


@cli.command()
@click.option("--no-save", is_flag=True, help="Don't save result to history.")
def jitter(no_save):
    """Test jitter only (alias for latency command).
    
    Jitter is measured alongside latency, so this runs the same test
    as the latency command.
    """
    # Jitter is measured with latency
    print_banner()
    print_info("Testing jitter (and latency)...")
    console.print()
    
    try:
        result = run_with_progress(run_latency_test, "Testing jitter")
        
        if not no_save:
            save_result(result)
        
        display_result(result)
        
    except Exception as e:
        print_error(f"Jitter test failed: {e}")
        raise click.Abort()


@cli.command()
@click.option("-n", "--count", default=10, help="Number of results to show.")
def history(count):
    """View past speed test results.
    
    Shows a table of your previous speed tests with all metrics.
    """
    print_banner()
    results = get_last_n_results(count)
    display_history(results)


@cli.command()
def stats():
    """View statistics from your test history.
    
    Shows averages, minimums, and maximums for all metrics
    across your test history.
    """
    print_banner()
    statistics = get_statistics()
    display_statistics(statistics)


@cli.command("clear-history")
@click.confirmation_option(prompt="Are you sure you want to clear all history?")
def clear_history_cmd():
    """Clear all test history.
    
    This will permanently delete all saved test results.
    """
    clear_history()
    print_success("History cleared.")


@cli.command()
def quality():
    """Show connection quality score only.
    
    Runs a full test but emphasizes the overall quality score,
    which is calculated from download, upload, latency, and jitter.
    """
    print_banner()
    print_info("Calculating connection quality...")
    console.print()
    
    try:
        result = run_with_progress(run_speed_test, "Testing quality")
        save_result(result)
        
        # Show quality-focused output
        from rich.panel import Panel
        from rich.text import Text
        
        quality = result.quality_score or 0
        if quality >= 90:
            color = "green"
            verdict = "Excellent! Your connection is top-tier."
        elif quality >= 70:
            color = "green"
            verdict = "Good. Your connection handles most tasks well."
        elif quality >= 50:
            color = "yellow"
            verdict = "Fair. You may experience some issues with video calls or gaming."
        elif quality >= 30:
            color = "rgb(255,165,0)"
            verdict = "Poor. Consider troubleshooting your connection."
        else:
            color = "red"
            verdict = "Bad. Your connection needs attention."
        
        score_text = Text()
        score_text.append(f"\n  {quality}", style=f"bold {color}")
        score_text.append("/100\n\n", style="dim")
        score_text.append(f"  {verdict}\n", style=color)
        
        panel = Panel(
            score_text,
            title="[bold cyan]Connection Quality Score[/bold cyan]",
            border_style="cyan",
        )
        console.print(panel)
        console.print()
        
        # Also show the detailed results
        display_result(result)
        
    except Exception as e:
        print_error(f"Quality test failed: {e}")
        raise click.Abort()


@cli.command()
def dns():
    """Test DNS lookup time.
    
    Measures how long it takes to resolve speed.cloudflare.com.
    Fast DNS is important for browsing responsiveness.
    """
    print_banner()
    print_info("Testing DNS lookup time...")
    console.print()
    
    try:
        import asyncio
        from .speedtest import CloudflareSpeedTest
        
        tester = CloudflareSpeedTest()
        dns_time = asyncio.run(tester.measure_dns())
        
        from rich.panel import Panel
        from .display import format_dns
        
        panel = Panel(
            format_dns(dns_time),
            title="[bold cyan]DNS Lookup Time[/bold cyan]",
            border_style="cyan",
        )
        console.print(panel)
        console.print()
        
        # Provide context
        if dns_time < 20:
            print_success("Excellent DNS response time!")
        elif dns_time < 50:
            print_info("Good DNS response time.")
        elif dns_time < 100:
            console.print("[yellow]DNS is a bit slow. Consider using a faster DNS like 1.1.1.1 or 8.8.8.8[/yellow]")
        else:
            console.print("[red]DNS is slow. Try switching to Cloudflare DNS (1.1.1.1) or Google DNS (8.8.8.8)[/red]")
        
    except Exception as e:
        print_error(f"DNS test failed: {e}")
        raise click.Abort()


@cli.command()
def ttfb():
    """Test Time to First Byte (TTFB).
    
    Measures server response time - how quickly you receive
    the first byte of data after making a request.
    """
    print_banner()
    print_info("Testing Time to First Byte...")
    console.print()
    
    try:
        result = run_with_progress(run_latency_test, "Testing TTFB")
        
        from rich.panel import Panel
        from .display import format_latency
        
        panel = Panel(
            format_latency(result.ttfb_ms),
            title="[bold cyan]Time to First Byte (TTFB)[/bold cyan]",
            border_style="cyan",
        )
        console.print(panel)
        console.print()
        
    except Exception as e:
        print_error(f"TTFB test failed: {e}")
        raise click.Abort()


if __name__ == "__main__":
    cli()
