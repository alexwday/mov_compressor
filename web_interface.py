#!/usr/bin/env python3
"""
Web interface for video compression
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import mimetypes
from compress_video import VideoCompressor

class CompressionHandler(SimpleHTTPRequestHandler):
    """HTTP request handler for video compression"""
    
    def do_GET(self):
        """Serve HTML interface"""
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            
            html_path = Path(__file__).parent / 'index.html'
            if html_path.exists():
                with open(html_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                # Fallback if index.html doesn't exist
                self.wfile.write(b"<html><body><h1>index.html not found</h1></body></html>")
        else:
            super().do_GET()
    
    def do_POST(self):
        """Handle compression requests"""
        if self.path == '/compress':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Parse multipart form data
            boundary = self.headers['Content-Type'].split('boundary=')[1]
            parts = post_data.split(f'--{boundary}'.encode())
            
            file_data = None
            filename = None
            settings = {}
            
            for part in parts:
                if b'Content-Disposition' in part:
                    if b'name="file"' in part:
                        # Extract filename and file data
                        header_end = part.find(b'\r\n\r\n')
                        headers = part[:header_end].decode('utf-8', errors='ignore')
                        
                        # Get filename
                        if 'filename="' in headers:
                            filename = headers.split('filename="')[1].split('"')[0]
                        
                        # Get file data
                        file_data = part[header_end + 4:-2]  # Skip headers and trailing CRLF
                    
                    elif b'name="preset"' in part:
                        value = part.split(b'\r\n\r\n')[1].strip(b'\r\n')
                        settings['preset'] = value.decode('utf-8')
                    
                    elif b'name="crf"' in part:
                        value = part.split(b'\r\n\r\n')[1].strip(b'\r\n')
                        try:
                            settings['crf'] = int(value.decode('utf-8'))
                        except:
                            pass
                    
                    elif b'name="scale"' in part:
                        value = part.split(b'\r\n\r\n')[1].strip(b'\r\n').decode('utf-8')
                        if value and value != 'none':
                            settings['scale'] = value
                    
                    elif b'name="fps"' in part:
                        value = part.split(b'\r\n\r\n')[1].strip(b'\r\n')
                        try:
                            fps_val = int(value.decode('utf-8'))
                            if fps_val > 0:
                                settings['fps'] = fps_val
                        except:
                            pass
                    
                    elif b'name="codec"' in part:
                        value = part.split(b'\r\n\r\n')[1].strip(b'\r\n')
                        settings['codec'] = value.decode('utf-8')
            
            if file_data and filename:
                # Save uploaded file temporarily
                temp_dir = tempfile.mkdtemp()
                input_path = Path(temp_dir) / filename
                output_path = Path(temp_dir) / f"{Path(filename).stem}_compressed.mp4"
                
                try:
                    # Write uploaded file
                    with open(input_path, 'wb') as f:
                        f.write(file_data)
                    
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
                        
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/octet-stream')
                        self.send_header('Content-Disposition', 
                                       f'attachment; filename="{output_path.name}"')
                        self.send_header('X-Compression-Info', 
                                       json.dumps({
                                           'original_size': result['input_size'],
                                           'compressed_size': result['output_size'],
                                           'ratio': result['compression_ratio']
                                       }))
                        self.end_headers()
                        self.wfile.write(compressed_data)
                    else:
                        # Send error
                        self.send_response(500)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({'error': result['error']}).encode())
                    
                finally:
                    # Clean up temp files
                    shutil.rmtree(temp_dir, ignore_errors=True)
            else:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'No file uploaded'}).encode())
        else:
            self.send_response(404)
            self.end_headers()

def start_server(port=8080):
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

if __name__ == '__main__':
    start_server()