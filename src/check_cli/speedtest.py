"""Core speed test functionality using Cloudflare's speed test infrastructure."""

import asyncio
import socket
import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import httpx


@dataclass
class SpeedTestResult:
    """Results from a speed test."""

    timestamp: datetime = field(default_factory=datetime.now)
    download_mbps: Optional[float] = None
    upload_mbps: Optional[float] = None
    latency_ms: Optional[float] = None
    jitter_ms: Optional[float] = None
    loaded_latency_ms: Optional[float] = None  # Latency under load
    ttfb_ms: Optional[float] = None  # Time to first byte
    dns_ms: Optional[float] = None  # DNS lookup time
    quality_score: Optional[int] = None  # Overall quality 0-100
    server_location: Optional[str] = None
    server_ip: Optional[str] = None
    client_ip: Optional[str] = None
    isp: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert result to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "download_mbps": self.download_mbps,
            "upload_mbps": self.upload_mbps,
            "latency_ms": self.latency_ms,
            "jitter_ms": self.jitter_ms,
            "loaded_latency_ms": self.loaded_latency_ms,
            "ttfb_ms": self.ttfb_ms,
            "dns_ms": self.dns_ms,
            "quality_score": self.quality_score,
            "server_location": self.server_location,
            "server_ip": self.server_ip,
            "client_ip": self.client_ip,
            "isp": self.isp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SpeedTestResult":
        """Create result from dictionary."""
        data = data.copy()
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        # Handle older history entries that may not have new fields
        for field_name in ["loaded_latency_ms", "ttfb_ms", "dns_ms", "quality_score"]:
            if field_name not in data:
                data[field_name] = None
        return cls(**data)


class CloudflareSpeedTest:
    """Speed test using Cloudflare's infrastructure."""

    BASE_URL = "https://speed.cloudflare.com"
    DOWNLOAD_SIZES = [100_000, 1_000_000, 10_000_000, 25_000_000]  # 100KB, 1MB, 10MB, 25MB
    UPLOAD_SIZES = [100_000, 1_000_000, 10_000_000]  # 100KB, 1MB, 10MB
    LATENCY_SAMPLES = 20

    def __init__(self):
        self.result = SpeedTestResult()
        self._progress_callback = None

    def set_progress_callback(self, callback):
        """Set a callback function for progress updates."""
        self._progress_callback = callback

    def _report_progress(self, phase: str, progress: float, detail: str = ""):
        """Report progress to callback if set."""
        if self._progress_callback:
            self._progress_callback(phase, progress, detail)

    async def measure_dns(self) -> float:
        """Measure DNS lookup time."""
        try:
            start = time.perf_counter()
            socket.gethostbyname("speed.cloudflare.com")
            end = time.perf_counter()
            return round((end - start) * 1000, 2)
        except Exception:
            return 0.0

    async def get_server_info(self, client: httpx.AsyncClient) -> dict:
        """Get server and client information from Cloudflare."""
        try:
            # Get metadata from Cloudflare
            response = await client.get(
                f"{self.BASE_URL}/__down?bytes=0",
                headers={"Accept": "*/*"},
            )
            
            # Extract server info from headers
            cf_ray = response.headers.get("cf-ray", "")
            server_location = cf_ray.split("-")[-1] if "-" in cf_ray else "Unknown"
            
            # Get client IP from trace endpoint
            trace_response = await client.get("https://1.1.1.1/cdn-cgi/trace")
            trace_data = {}
            for line in trace_response.text.strip().split("\n"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    trace_data[key] = value
            
            return {
                "server_location": server_location,
                "client_ip": trace_data.get("ip", "Unknown"),
                "colo": trace_data.get("colo", server_location),
            }
        except Exception:
            return {
                "server_location": "Unknown",
                "client_ip": "Unknown",
                "colo": "Unknown",
            }

    async def measure_latency(self, client: httpx.AsyncClient) -> tuple[float, float, float]:
        """Measure latency, jitter, and TTFB using multiple samples."""
        latencies = []
        ttfb_values = []
        
        for i in range(self.LATENCY_SAMPLES):
            self._report_progress("latency", (i + 1) / self.LATENCY_SAMPLES)
            try:
                start = time.perf_counter()
                response = await client.get(
                    f"{self.BASE_URL}/__down?bytes=0",
                    headers={"Accept": "*/*", "Cache-Control": "no-cache"},
                )
                first_byte = time.perf_counter()
                # Consume response
                _ = response.content
                end = time.perf_counter()
                
                latencies.append((end - start) * 1000)  # Convert to ms
                ttfb_values.append((first_byte - start) * 1000)
            except Exception:
                continue
            
            # Small delay between samples
            await asyncio.sleep(0.05)
        
        if not latencies:
            return 0.0, 0.0, 0.0
        
        avg_latency = statistics.mean(latencies)
        avg_ttfb = statistics.mean(ttfb_values) if ttfb_values else 0.0
        
        # Calculate jitter as average difference between consecutive samples
        if len(latencies) > 1:
            differences = [abs(latencies[i] - latencies[i-1]) for i in range(1, len(latencies))]
            jitter = statistics.mean(differences)
        else:
            jitter = 0.0
        
        return round(avg_latency, 2), round(jitter, 2), round(avg_ttfb, 2)

    async def measure_download(self, client: httpx.AsyncClient) -> tuple[float, float]:
        """Measure download speed and loaded latency using multiple file sizes."""
        speeds = []
        loaded_latencies = []
        total_tests = len(self.DOWNLOAD_SIZES)
        
        for idx, size in enumerate(self.DOWNLOAD_SIZES):
            self._report_progress(
                "download", 
                (idx + 1) / total_tests,
                f"{size // 1_000_000}MB" if size >= 1_000_000 else f"{size // 1000}KB"
            )
            
            try:
                # Measure a small request during the download to get loaded latency
                start = time.perf_counter()
                response = await client.get(
                    f"{self.BASE_URL}/__down?bytes={size}",
                    headers={"Accept": "*/*", "Cache-Control": "no-cache"},
                )
                # Read all content
                _ = response.content
                end = time.perf_counter()
                
                duration = end - start
                if duration > 0:
                    # Calculate speed in Mbps
                    speed_mbps = (size * 8) / (duration * 1_000_000)
                    speeds.append(speed_mbps)
                    
                    # For larger downloads, measure loaded latency
                    if size >= 1_000_000:
                        # Quick ping during/after download
                        ping_start = time.perf_counter()
                        await client.get(
                            f"{self.BASE_URL}/__down?bytes=0",
                            headers={"Accept": "*/*", "Cache-Control": "no-cache"},
                        )
                        ping_end = time.perf_counter()
                        loaded_latencies.append((ping_end - ping_start) * 1000)
            except Exception:
                continue
        
        if not speeds:
            return 0.0, 0.0
        
        max_speed = round(max(speeds), 2)
        avg_loaded_latency = round(statistics.mean(loaded_latencies), 2) if loaded_latencies else 0.0
        
        return max_speed, avg_loaded_latency

    async def measure_upload(self, client: httpx.AsyncClient) -> float:
        """Measure upload speed using multiple payload sizes."""
        speeds = []
        total_tests = len(self.UPLOAD_SIZES)
        
        for idx, size in enumerate(self.UPLOAD_SIZES):
            self._report_progress(
                "upload",
                (idx + 1) / total_tests,
                f"{size // 1_000_000}MB" if size >= 1_000_000 else f"{size // 1000}KB"
            )
            
            # Generate random-ish data for upload
            data = b"x" * size
            
            try:
                start = time.perf_counter()
                await client.post(
                    f"{self.BASE_URL}/__up",
                    content=data,
                    headers={
                        "Content-Type": "application/octet-stream",
                        "Cache-Control": "no-cache",
                    },
                )
                end = time.perf_counter()
                
                duration = end - start
                if duration > 0:
                    speed_mbps = (size * 8) / (duration * 1_000_000)
                    speeds.append(speed_mbps)
            except Exception:
                continue
        
        if not speeds:
            return 0.0
        
        return round(max(speeds), 2)

    def calculate_quality_score(self) -> int:
        """Calculate an overall connection quality score (0-100).
        
        Based on:
        - Download speed (40% weight)
        - Upload speed (20% weight)
        - Latency (25% weight)
        - Jitter (15% weight)
        """
        score = 0.0
        
        # Download: 100+ Mbps = 100%, scales down
        if self.result.download_mbps:
            dl_score = min(100, (self.result.download_mbps / 100) * 100)
            score += dl_score * 0.40
        
        # Upload: 50+ Mbps = 100%, scales down
        if self.result.upload_mbps:
            ul_score = min(100, (self.result.upload_mbps / 50) * 100)
            score += ul_score * 0.20
        
        # Latency: <10ms = 100%, >200ms = 0%
        if self.result.latency_ms:
            if self.result.latency_ms <= 10:
                lat_score = 100
            elif self.result.latency_ms >= 200:
                lat_score = 0
            else:
                lat_score = 100 - ((self.result.latency_ms - 10) / 190 * 100)
            score += lat_score * 0.25
        
        # Jitter: <5ms = 100%, >50ms = 0%
        if self.result.jitter_ms:
            if self.result.jitter_ms <= 5:
                jit_score = 100
            elif self.result.jitter_ms >= 50:
                jit_score = 0
            else:
                jit_score = 100 - ((self.result.jitter_ms - 5) / 45 * 100)
            score += jit_score * 0.15
        
        return round(score)

    async def run_full_test(self) -> SpeedTestResult:
        """Run a complete speed test (download, upload, latency, jitter)."""
        # Measure DNS first (before HTTP client)
        self._report_progress("dns", 0, "Measuring DNS...")
        self.result.dns_ms = await self.measure_dns()
        self._report_progress("dns", 1, "Done")
        
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=10.0),
            http2=True,
            follow_redirects=True,
        ) as client:
            # Get server info
            self._report_progress("info", 0, "Getting server info...")
            server_info = await self.get_server_info(client)
            self.result.server_location = server_info["colo"]
            self.result.client_ip = server_info["client_ip"]
            self._report_progress("info", 1, "Done")
            
            # Measure idle latency and jitter
            self._report_progress("latency", 0, "Measuring latency...")
            latency, jitter, ttfb = await self.measure_latency(client)
            self.result.latency_ms = latency
            self.result.jitter_ms = jitter
            self.result.ttfb_ms = ttfb
            
            # Measure download and loaded latency
            self._report_progress("download", 0, "Testing download...")
            download_speed, loaded_latency = await self.measure_download(client)
            self.result.download_mbps = download_speed
            self.result.loaded_latency_ms = loaded_latency
            
            # Measure upload
            self._report_progress("upload", 0, "Testing upload...")
            self.result.upload_mbps = await self.measure_upload(client)
        
        # Calculate quality score
        self.result.quality_score = self.calculate_quality_score()
        
        return self.result

    async def run_latency_only(self) -> SpeedTestResult:
        """Run only latency/jitter test."""
        self.result.dns_ms = await self.measure_dns()
        
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            http2=True,
            follow_redirects=True,
        ) as client:
            server_info = await self.get_server_info(client)
            self.result.server_location = server_info["colo"]
            self.result.client_ip = server_info["client_ip"]
            
            latency, jitter, ttfb = await self.measure_latency(client)
            self.result.latency_ms = latency
            self.result.jitter_ms = jitter
            self.result.ttfb_ms = ttfb
        
        return self.result

    async def run_download_only(self) -> SpeedTestResult:
        """Run only download test."""
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=10.0),
            http2=True,
            follow_redirects=True,
        ) as client:
            server_info = await self.get_server_info(client)
            self.result.server_location = server_info["colo"]
            self.result.client_ip = server_info["client_ip"]
            
            download_speed, loaded_latency = await self.measure_download(client)
            self.result.download_mbps = download_speed
            self.result.loaded_latency_ms = loaded_latency
        
        return self.result

    async def run_upload_only(self) -> SpeedTestResult:
        """Run only upload test."""
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=10.0),
            http2=True,
            follow_redirects=True,
        ) as client:
            server_info = await self.get_server_info(client)
            self.result.server_location = server_info["colo"]
            self.result.client_ip = server_info["client_ip"]
            
            self.result.upload_mbps = await self.measure_upload(client)
        
        return self.result


def run_speed_test(progress_callback=None) -> SpeedTestResult:
    """Synchronous wrapper for running a full speed test."""
    tester = CloudflareSpeedTest()
    if progress_callback:
        tester.set_progress_callback(progress_callback)
    return asyncio.run(tester.run_full_test())


def run_latency_test(progress_callback=None) -> SpeedTestResult:
    """Synchronous wrapper for running a latency test."""
    tester = CloudflareSpeedTest()
    if progress_callback:
        tester.set_progress_callback(progress_callback)
    return asyncio.run(tester.run_latency_only())


def run_download_test(progress_callback=None) -> SpeedTestResult:
    """Synchronous wrapper for running a download test."""
    tester = CloudflareSpeedTest()
    if progress_callback:
        tester.set_progress_callback(progress_callback)
    return asyncio.run(tester.run_download_only())


def run_upload_test(progress_callback=None) -> SpeedTestResult:
    """Synchronous wrapper for running an upload test."""
    tester = CloudflareSpeedTest()
    if progress_callback:
        tester.set_progress_callback(progress_callback)
    return asyncio.run(tester.run_upload_only())
