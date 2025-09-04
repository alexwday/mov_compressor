# MOV Compressor

A Python-based video compression tool specifically designed for `.mov` screen recordings. Features both command-line and web interfaces for easy video compression with various quality presets and advanced settings.

## Features

- 🎬 **Dual Interface**: Command-line tool and web-based GUI
- 📊 **Multiple Presets**: High, Medium, Low, and Web-optimized compression
- ⚙️ **Advanced Controls**: Custom CRF, resolution scaling, FPS adjustment
- 🎯 **Codec Support**: H.264 (compatibility) and H.265/HEVC (efficiency)
- 📁 **Drag & Drop**: Web interface with file drag-and-drop support
- 📈 **Real-time Stats**: Compression ratio and file size information

## Prerequisites

### Install FFmpeg

This tool requires FFmpeg to be installed on your system:

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH

### Python Requirements

- Python 3.6 or higher
- No external Python packages required (uses standard library only)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/alexwday/mov_compressor.git
cd mov_compressor
```

2. (Optional) Create and activate a virtual environment:
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

3. Make scripts executable (macOS/Linux):
```bash
chmod +x compress_video.py web_interface.py
```

## Usage

### Command-Line Interface

#### Basic compression with default settings:
```bash
python compress_video.py video.mov
# Or if made executable:
./compress_video.py video.mov
```

#### Using compression presets:
```bash
# High quality (larger file)
python compress_video.py video.mov -p high

# Balanced quality and size (default)
python compress_video.py video.mov -p medium

# Lower quality (smaller file)
python compress_video.py video.mov -p low

# Web optimized (720p resolution)
python compress_video.py video.mov -p web
```

#### Advanced options:
```bash
# Custom quality (CRF: 0-51, lower = better quality)
python compress_video.py video.mov --crf 20

# Scale to specific resolution
python compress_video.py video.mov --scale 1920:-2  # 1080p
python compress_video.py video.mov --scale 1280:-2  # 720p

# Change frame rate
python compress_video.py video.mov --fps 30

# Use H.265/HEVC codec for better compression
python compress_video.py video.mov --codec h265

# Combine multiple options
python compress_video.py video.mov -p high --scale 1920:-2 --fps 60

# Specify output file
python compress_video.py video.mov -o output_compressed.mp4
```

#### View available presets:
```bash
python compress_video.py --list-presets
```

### Web Interface

1. Start the web server:
```bash
python compress_video.py --web
# Or directly:
python web_interface.py
```

2. Open your browser and navigate to:
```
http://localhost:8080
```

3. Use the web interface to:
   - Drag and drop or select your .mov file
   - Choose a compression preset
   - Adjust advanced settings (optional)
   - Click "Compress Video" to process
   - Download will start automatically when complete

## Compression Presets

| Preset | CRF | Speed | Description | Best For |
|--------|-----|-------|-------------|----------|
| **High** | 18 | Slow | High quality, larger file | Archiving, high-quality presentations |
| **Medium** | 23 | Medium | Balanced quality and size | General use, sharing |
| **Low** | 28 | Fast | Lower quality, smaller file | Quick sharing, limited bandwidth |
| **Web** | 25 | Medium | 720p resolution, web-optimized | Web upload, streaming platforms |

## Advanced Settings

- **CRF (Constant Rate Factor)**: 0-51 scale, lower values = higher quality/larger files
- **Resolution Scaling**: Maintain aspect ratio while resizing (e.g., "1280:-2" for 720p)
- **Frame Rate**: Reduce FPS for smaller files (e.g., 60fps → 30fps)
- **Codec**: 
  - H.264: Better compatibility across devices
  - H.265/HEVC: Better compression ratio (25-50% smaller files)

## Tips for Best Results

1. **Screen Recordings**: Use the "web" preset for recordings you'll share online
2. **Large Files**: Start with "medium" preset and adjust based on results
3. **Archive Quality**: Use "high" preset or custom CRF of 15-18
4. **Email Attachments**: Use "low" preset or add `--scale 1280:-2` for smaller files
5. **Batch Processing**: Use command-line with shell scripts for multiple files

## Troubleshooting

### FFmpeg not found
Ensure FFmpeg is installed and in your system PATH:
```bash
ffmpeg -version
```

### Permission denied (macOS/Linux)
Make the scripts executable:
```bash
chmod +x compress_video.py web_interface.py
```

### Web interface not loading
- Check if port 8080 is available
- Try accessing `http://127.0.0.1:8080` instead of localhost
- Ensure no firewall is blocking the connection

## Examples

### Compress for email (< 25MB)
```bash
python compress_video.py large_recording.mov -p low --scale 1280:-2
```

### Prepare for YouTube upload
```bash
python compress_video.py tutorial.mov -p high --fps 60
```

### Quick share via Slack/Discord
```bash
python compress_video.py demo.mov -p web
```

### Maximum compression
```bash
python compress_video.py huge_file.mov --crf 30 --scale 854:-2 --fps 24 --codec h265
```

## License

MIT License - feel free to use and modify as needed.

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## Author

Created by Alex W Day

---

**Note**: This tool is optimized for `.mov` files (especially screen recordings from macOS), but it can also process other video formats supported by FFmpeg.