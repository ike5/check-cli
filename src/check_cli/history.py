"""History management for speed test results."""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from platformdirs import user_data_dir

from .speedtest import SpeedTestResult


def get_history_path() -> Path:
    """Get the path to the history file."""
    data_dir = Path(user_data_dir("check-cli", "check-cli"))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "history.json"


def load_history() -> List[SpeedTestResult]:
    """Load history from file."""
    history_path = get_history_path()
    
    if not history_path.exists():
        return []
    
    try:
        with open(history_path, "r") as f:
            data = json.load(f)
        return [SpeedTestResult.from_dict(item) for item in data]
    except (json.JSONDecodeError, KeyError, TypeError):
        return []


def save_result(result: SpeedTestResult, max_history: int = 100) -> None:
    """Save a result to history, keeping only the last max_history results."""
    history = load_history()
    history.append(result)
    
    # Keep only the last max_history results
    if len(history) > max_history:
        history = history[-max_history:]
    
    history_path = get_history_path()
    with open(history_path, "w") as f:
        json.dump([r.to_dict() for r in history], f, indent=2)


def get_last_result() -> Optional[SpeedTestResult]:
    """Get the most recent result from history."""
    history = load_history()
    return history[-1] if history else None


def get_results_since(since: datetime) -> List[SpeedTestResult]:
    """Get all results since a given datetime."""
    history = load_history()
    return [r for r in history if r.timestamp >= since]


def get_last_n_results(n: int = 10) -> List[SpeedTestResult]:
    """Get the last n results."""
    history = load_history()
    return history[-n:] if history else []


def clear_history() -> None:
    """Clear all history."""
    history_path = get_history_path()
    if history_path.exists():
        history_path.unlink()


def compare_results(current: SpeedTestResult, previous: SpeedTestResult) -> dict:
    """Compare two results and return the differences."""
    comparison = {}
    
    metrics = [
        ("download_mbps", "Download", "Mbps", True),  # True = higher is better
        ("upload_mbps", "Upload", "Mbps", True),
        ("latency_ms", "Latency", "ms", False),  # False = lower is better
        ("jitter_ms", "Jitter", "ms", False),
    ]
    
    for attr, name, unit, higher_is_better in metrics:
        current_val = getattr(current, attr)
        previous_val = getattr(previous, attr)
        
        if current_val is not None and previous_val is not None and previous_val != 0:
            diff = current_val - previous_val
            pct_change = (diff / previous_val) * 100
            
            # Determine if change is good or bad
            if higher_is_better:
                is_improvement = diff > 0
            else:
                is_improvement = diff < 0
            
            comparison[attr] = {
                "name": name,
                "unit": unit,
                "current": current_val,
                "previous": previous_val,
                "difference": diff,
                "percent_change": pct_change,
                "is_improvement": is_improvement,
            }
    
    return comparison


def get_statistics() -> dict:
    """Get statistics from history."""
    history = load_history()
    
    if not history:
        return {}
    
    stats = {
        "total_tests": len(history),
        "first_test": history[0].timestamp.isoformat(),
        "last_test": history[-1].timestamp.isoformat(),
    }
    
    # Calculate averages for each metric
    metrics = ["download_mbps", "upload_mbps", "latency_ms", "jitter_ms"]
    
    for metric in metrics:
        values = [getattr(r, metric) for r in history if getattr(r, metric) is not None]
        if values:
            stats[f"{metric}_avg"] = round(sum(values) / len(values), 2)
            stats[f"{metric}_min"] = round(min(values), 2)
            stats[f"{metric}_max"] = round(max(values), 2)
    
    return stats
