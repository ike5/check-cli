"""Tests for check-cli."""

import pytest
from datetime import datetime

from check_cli.speedtest import SpeedTestResult
from check_cli.history import compare_results


class TestSpeedTestResult:
    """Tests for SpeedTestResult dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = SpeedTestResult(
            timestamp=datetime(2024, 1, 15, 12, 0, 0),
            download_mbps=100.0,
            upload_mbps=50.0,
            latency_ms=15.0,
            jitter_ms=2.0,
            server_location="SJC",
            client_ip="1.2.3.4",
        )
        
        data = result.to_dict()
        
        assert data["download_mbps"] == 100.0
        assert data["upload_mbps"] == 50.0
        assert data["latency_ms"] == 15.0
        assert data["jitter_ms"] == 2.0
        assert data["server_location"] == "SJC"
        assert data["client_ip"] == "1.2.3.4"

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "timestamp": "2024-01-15T12:00:00",
            "download_mbps": 100.0,
            "upload_mbps": 50.0,
            "latency_ms": 15.0,
            "jitter_ms": 2.0,
            "server_location": "SJC",
            "server_ip": None,
            "client_ip": "1.2.3.4",
            "isp": None,
        }
        
        result = SpeedTestResult.from_dict(data)
        
        assert result.download_mbps == 100.0
        assert result.upload_mbps == 50.0
        assert result.latency_ms == 15.0
        assert result.jitter_ms == 2.0
        assert result.server_location == "SJC"

    def test_round_trip(self):
        """Test to_dict -> from_dict round trip."""
        original = SpeedTestResult(
            timestamp=datetime(2024, 1, 15, 12, 0, 0),
            download_mbps=100.0,
            upload_mbps=50.0,
            latency_ms=15.0,
            jitter_ms=2.0,
            server_location="SJC",
        )
        
        data = original.to_dict()
        restored = SpeedTestResult.from_dict(data)
        
        assert original.download_mbps == restored.download_mbps
        assert original.upload_mbps == restored.upload_mbps
        assert original.latency_ms == restored.latency_ms
        assert original.jitter_ms == restored.jitter_ms


class TestCompareResults:
    """Tests for result comparison."""

    def test_compare_improvement(self):
        """Test comparison when metrics improve."""
        previous = SpeedTestResult(
            timestamp=datetime(2024, 1, 14, 12, 0, 0),
            download_mbps=100.0,
            upload_mbps=50.0,
            latency_ms=20.0,
            jitter_ms=5.0,
        )
        
        current = SpeedTestResult(
            timestamp=datetime(2024, 1, 15, 12, 0, 0),
            download_mbps=150.0,  # Better (higher)
            upload_mbps=75.0,     # Better (higher)
            latency_ms=15.0,      # Better (lower)
            jitter_ms=3.0,        # Better (lower)
        )
        
        comparison = compare_results(current, previous)
        
        assert comparison["download_mbps"]["is_improvement"] is True
        assert comparison["upload_mbps"]["is_improvement"] is True
        assert comparison["latency_ms"]["is_improvement"] is True
        assert comparison["jitter_ms"]["is_improvement"] is True

    def test_compare_degradation(self):
        """Test comparison when metrics degrade."""
        previous = SpeedTestResult(
            timestamp=datetime(2024, 1, 14, 12, 0, 0),
            download_mbps=150.0,
            upload_mbps=75.0,
            latency_ms=15.0,
            jitter_ms=3.0,
        )
        
        current = SpeedTestResult(
            timestamp=datetime(2024, 1, 15, 12, 0, 0),
            download_mbps=100.0,  # Worse (lower)
            upload_mbps=50.0,     # Worse (lower)
            latency_ms=20.0,      # Worse (higher)
            jitter_ms=5.0,        # Worse (higher)
        )
        
        comparison = compare_results(current, previous)
        
        assert comparison["download_mbps"]["is_improvement"] is False
        assert comparison["upload_mbps"]["is_improvement"] is False
        assert comparison["latency_ms"]["is_improvement"] is False
        assert comparison["jitter_ms"]["is_improvement"] is False

    def test_compare_percent_change(self):
        """Test percentage change calculation."""
        previous = SpeedTestResult(
            timestamp=datetime(2024, 1, 14, 12, 0, 0),
            download_mbps=100.0,
        )
        
        current = SpeedTestResult(
            timestamp=datetime(2024, 1, 15, 12, 0, 0),
            download_mbps=150.0,  # 50% increase
        )
        
        comparison = compare_results(current, previous)
        
        assert comparison["download_mbps"]["percent_change"] == 50.0


class TestCLI:
    """Tests for CLI commands."""

    def test_version(self):
        """Test --version flag."""
        from click.testing import CliRunner
        from check_cli.main import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        
        assert result.exit_code == 0
        assert "check-cli" in result.output or "1.0.0" in result.output

    def test_help(self):
        """Test help output."""
        from click.testing import CliRunner
        from check_cli.main import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        
        assert result.exit_code == 0
        assert "speed" in result.output
        assert "download" in result.output
        assert "upload" in result.output
        assert "latency" in result.output
