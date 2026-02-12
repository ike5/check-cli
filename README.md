# Check CLI 🚀

A beautiful, cross-platform CLI tool to test your internet speed, latency, jitter, and more.

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

- ⬇️ **Download Speed** - Measure your download bandwidth
- ⬆️ **Upload Speed** - Measure your upload bandwidth
- ⏱️ **Latency** - Measure network latency (ping)
- 📊 **Jitter** - Measure latency variation
- 🌐 **Server Info** - See which Cloudflare server you're connected to
- 📈 **History** - Track your results over time
- 📊 **Statistics** - View averages, min/max across all tests
- 🎨 **Beautiful Output** - Colorful, easy-to-read terminal output
- 📊 **Progress Bars** - Real-time progress during tests

## Installation

### 🐍 Via pip/pipx (Recommended - Works Everywhere)

**Works on:** macOS, Linux, Windows, Chromebook (Linux), WSL

```bash
# Using pipx (recommended - isolated environment)
pipx install check-cli

# Or using pip
pip install check-cli
```

### 🍺 Via Homebrew (macOS/Linux)

```bash
brew tap yourusername/check-cli
brew install check-cli
```

### 📦 From Source

```bash
git clone https://github.com/yourusername/check-cli.git
cd check-cli
pip install -e .
```

## Quick Start

```bash
# Run a full speed test
check speed

# Test only download speed
check download

# Test only upload speed
check upload

# Test latency and jitter
check latency

# Get your connection quality score
check quality

# Test DNS lookup time
check dns

# Test Time to First Byte
check ttfb

# View test history
check history

# View statistics
check stats
```

## Usage

### Full Speed Test

Run a complete test measuring download, upload, latency, jitter, and more:

```bash
check speed
```

Output:
```
╭─────────────── Speed Test Results ───────────────╮
│                                                   │
│  ⭐ Quality Score  87/100 (Good)                 │
│                                                   │
│  ⬇  Download       156.42 Mbps                   │
│  ⬆  Upload          48.23 Mbps                   │
│                                                   │
│  ⏱  Latency (idle)   12.45 ms                    │
│  ⏱  Latency (loaded) 28.31 ms                    │
│  📊 Jitter            2.31 ms                    │
│  🚀 TTFB             11.23 ms                    │
│  🔍 DNS Lookup        8.45 ms                    │
│                                                   │
│  🌐 Server           SJC                          │
│  💻 Your IP          203.0.113.42                 │
│                                                   │
╰────────────── 2024-01-15 14:32:01 ───────────────╯
```

### Individual Tests

```bash
# Download only
check download

# Upload only
check upload

# Latency and jitter
check latency
check jitter  # alias for latency

# Connection quality score
check quality

# DNS lookup time
check dns

# Time to First Byte
check ttfb
```

### What Each Metric Means

| Metric | Description | Good Value |
|--------|-------------|------------|
| **Download** | How fast you receive data | >100 Mbps |
| **Upload** | How fast you send data | >50 Mbps |
| **Latency (idle)** | Response time when idle | <20 ms |
| **Latency (loaded)** | Response time under load | <50 ms |
| **Jitter** | Variation in latency | <5 ms |
| **TTFB** | Time to first byte | <20 ms |
| **DNS Lookup** | Domain resolution time | <20 ms |
| **Quality Score** | Overall connection quality | >70/100 |

### History & Statistics

```bash
# View last 10 results
check history

# View last 20 results
check history -n 20

# View statistics
check stats

# Clear history
check clear-history
```

### Options

```bash
# Don't save result to history
check speed --no-save

# Don't compare with previous result
check speed --no-compare

# Show version
check --version
```

## Chromebook Installation

Chromebooks can run Linux apps via Crostini. Here's how to set up:

1. **Enable Linux (Beta):**
   - Go to Settings → Advanced → Developers → Linux development environment
   - Click "Turn on" and follow the setup

2. **Install Python and pipx:**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv
   pip3 install pipx
   pipx ensurepath
   ```

3. **Install check-cli:**
   ```bash
   pipx install check-cli
   ```

4. **Run it:**
   ```bash
   check speed
   ```

## How It Works

Check CLI uses [Cloudflare's speed test infrastructure](https://speed.cloudflare.com), which is:

- **Free** - No API key required
- **Global** - Servers worldwide for accurate results
- **Reliable** - Enterprise-grade infrastructure
- **Private** - No data collection or accounts needed

## Data Storage

Test history is stored locally at:

- **macOS:** `~/Library/Application Support/check-cli/history.json`
- **Linux:** `~/.local/share/check-cli/history.json`
- **Windows:** `C:\Users\<user>\AppData\Local\check-cli\history.json`

## Requirements

- Python 3.8 or higher
- Internet connection

## Development

```bash
# Clone the repo
git clone https://github.com/yourusername/check-cli.git
cd check-cli

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/
ruff check src/
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Credits

- Uses [Cloudflare Speed Test](https://speed.cloudflare.com) infrastructure
- Built with [Click](https://click.palletsprojects.com/) for CLI
- Beautiful output with [Rich](https://rich.readthedocs.io/)
- HTTP requests via [httpx](https://www.python-httpx.org/)
