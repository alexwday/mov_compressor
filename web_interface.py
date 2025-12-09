#!/usr/bin/env python3
"""
Web interface for video compression
"""

import os
import json
import tempfile
import shutil
import re
import logging
import argparse
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse, quote
import mimetypes
from compress_video import VideoCompressor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MAX_FILE_SIZE = 4 * 1024 * 1024 * 1024  # 4GB max upload
VALID_PRESETS = {'high', 'medium', 'low', 'web'}
VALID_CODECS = {'h264', 'h265'}

class CompressionHandler(SimpleHTTPRequestHandler):
    """HTTP request handler for video compression"""
    
    def do_GET(self):
        """Serve HTML interface"""
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()

            html_path = Path(__file__).parent / 'index.html'
            if html_path.exists():
                with open(html_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.wfile.write(b"<html><body><h1>index.html not found</h1></body></html>")
        else:
            super().do_GET()

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal and encoding issues"""
        # Get only the basename (removes any path components)
        filename = Path(filename).name
        # Remove any null bytes
        filename = filename.replace('\x00', '')
        # Replace problematic characters with underscores
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Ensure it's not empty
        if not filename:
            filename = 'uploaded_video'
        return filename

    def _ascii_safe_filename(self, filename: str) -> str:
        """Convert filename to ASCII-safe version for HTTP headers"""
        # Replace non-ASCII characters with underscores
        return ''.join(c if ord(c) < 128 else '_' for c in filename)
    
    def _send_error_response(self, code: int, message: str):
        """Send a JSON error response"""
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        error_json = json.dumps({'error': message}, ensure_ascii=True)
        self.wfile.write(error_json.encode('utf-8'))

    def do_POST(self):
        """Handle compression requests"""
        if self.path == '/compress':
            # Check content length
            content_length_header = self.headers.get('Content-Length')
            if not content_length_header:
                self._send_error_response(400, 'Content-Length header required')
                return

            try:
                content_length = int(content_length_header)
            except ValueError:
                self._send_error_response(400, 'Invalid Content-Length')
                return

            # Check file size limit
            if content_length > MAX_FILE_SIZE:
                self._send_error_response(413, f'File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024*1024)}GB')
                return

            post_data = self.rfile.read(content_length)
            logger.info(f"Received upload of {content_length} bytes")

            # Parse multipart form data
            content_type = self.headers.get('Content-Type', '')
            if 'boundary=' not in content_type:
                self._send_error_response(400, 'Invalid multipart form data')
                return

            boundary = content_type.split('boundary=')[1]
            # Handle quoted boundary values
            if boundary.startswith('"') and boundary.endswith('"'):
                boundary = boundary[1:-1]

            parts = post_data.split(f'--{boundary}'.encode())

            file_data = None
            filename = None
            settings = {}

            for part in parts:
                if b'Content-Disposition' not in part:
                    continue

                if b'name="file"' in part:
                    # Extract filename and file data
                    header_end = part.find(b'\r\n\r\n')
                    if header_end == -1:
                        continue
                    headers = part[:header_end].decode('utf-8', errors='ignore')

                    # Get filename
                    if 'filename="' in headers:
                        filename = headers.split('filename="')[1].split('"')[0]
                        filename = self._sanitize_filename(filename)

                    # Get file data (skip headers and trailing CRLF)
                    file_data = part[header_end + 4:]
                    if file_data.endswith(b'\r\n'):
                        file_data = file_data[:-2]

                elif b'name="preset"' in part:
                    value = part.split(b'\r\n\r\n')[1].strip(b'\r\n')
                    preset_value = value.decode('utf-8', errors='ignore')
                    if preset_value in VALID_PRESETS:
                        settings['preset'] = preset_value
                    else:
                        settings['preset'] = 'medium'

                elif b'name="crf"' in part:
                    value = part.split(b'\r\n\r\n')[1].strip(b'\r\n')
                    try:
                        crf_val = int(value.decode('utf-8'))
                        if 0 <= crf_val <= 51:
                            settings['crf'] = crf_val
                    except (ValueError, UnicodeDecodeError):
                        pass

                elif b'name="scale"' in part:
                    value = part.split(b'\r\n\r\n')[1].strip(b'\r\n').decode('utf-8', errors='ignore')
                    if value and value != 'none':
                        # Validate scale format (e.g., 1920:-2)
                        if re.match(r'^\d+:-?\d+$', value):
                            settings['scale'] = value

                elif b'name="fps"' in part:
                    value = part.split(b'\r\n\r\n')[1].strip(b'\r\n')
                    try:
                        fps_val = int(value.decode('utf-8'))
                        if 1 <= fps_val <= 120:
                            settings['fps'] = fps_val
                    except (ValueError, UnicodeDecodeError):
                        pass

                elif b'name="codec"' in part:
                    value = part.split(b'\r\n\r\n')[1].strip(b'\r\n')
                    codec_value = value.decode('utf-8', errors='ignore')
                    if codec_value in VALID_CODECS:
                        settings['codec'] = codec_value
                    else:
                        settings['codec'] = 'h264'
            
            if file_data and filename:
                # Save uploaded file temporarily
                temp_dir = tempfile.mkdtemp()
                input_path = Path(temp_dir) / filename
                output_filename = f"{Path(filename).stem}_compressed.mp4"
                output_path = Path(temp_dir) / output_filename

                try:
                    # Write uploaded file
                    with open(input_path, 'wb') as f:
                        f.write(file_data)

                    logger.info(f"Processing file: {filename}, settings: {settings}")

                    # Compress video
                    compressor = VideoCompressor()
                    result = compressor.compress(
                        str(input_path),
                        str(output_path),
                        **settings
                    )

                    if result['success']:
                        # Send compressed file
                        with open(output_path, 'rb') as f:
                            compressed_data = f.read()

                        # Use ASCII-safe filename for headers
                        safe_filename = self._ascii_safe_filename(output_filename)

                        self.send_response(200)
                        self.send_header('Content-Type', 'application/octet-stream')
                        self.send_header('Content-Disposition',
                                       f'attachment; filename="{safe_filename}"')
                        # Use ensure_ascii=True to avoid encoding issues in headers
                        compression_info = json.dumps({
                            'original_size': result['input_size'],
                            'compressed_size': result['output_size'],
                            'ratio': result['compression_ratio']
                        }, ensure_ascii=True)
                        self.send_header('X-Compression-Info', compression_info)
                        self.send_header('Content-Length', str(len(compressed_data)))
                        self.end_headers()
                        self.wfile.write(compressed_data)

                        logger.info(f"Compression complete: {result['compression_ratio']} reduction")
                    else:
                        # Convert error to string safely
                        error_msg = result.get('error', 'Unknown error')
                        if isinstance(error_msg, bytes):
                            error_msg = error_msg.decode('utf-8', errors='replace')
                        logger.error(f"Compression failed: {error_msg}")
                        self._send_error_response(500, str(error_msg))

                except Exception as e:
                    logger.exception("Error during compression")
                    self._send_error_response(500, f"Server error: {str(e)}")

                finally:
                    # Clean up temp files
                    try:
                        shutil.rmtree(temp_dir)
                    except Exception as e:
                        logger.warning(f"Failed to clean up temp dir: {e}")
            else:
                self._send_error_response(400, 'No file uploaded')
        else:
            self.send_response(404)
            self.end_headers()

def start_server(port: int = 8080):
    """Start the web server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, CompressionHandler)

    print("\nVideo Compression Web Interface")
    print(f"   Open http://localhost:{port} in your browser")
    print("   Press Ctrl+C to stop\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description='Video Compression Web Interface')
    parser.add_argument('-p', '--port', type=int, default=8080,
                       help='Port to run the server on (default: 8080)')
    args = parser.parse_args()
    start_server(args.port)


if __name__ == '__main__':
    main()