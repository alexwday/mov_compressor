#!/usr/bin/env python3
"""
Video compression utility for .mov files
Supports both command-line and web interface
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import json

class VideoCompressor:
    """Handles video compression using ffmpeg"""
    
    PRESETS = {
        'high': {
            'crf': 18,
            'preset': 'slow',
            'description': 'High quality, larger file'
        },
        'medium': {
            'crf': 23,
            'preset': 'medium',
            'description': 'Balanced quality and size'
        },
        'low': {
            'crf': 28,
            'preset': 'fast',
            'description': 'Lower quality, smaller file'
        },
        'web': {
            'crf': 25,
            'preset': 'medium',
            'scale': '1280:-2',
            'description': 'Optimized for web (720p)'
        }
    }
    
    def __init__(self):
        self.check_ffmpeg()
    
    def check_ffmpeg(self):
        """Check if ffmpeg is installed"""
        try:
            subprocess.run(['ffmpeg', '-version'], 
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Error: ffmpeg is not installed or not in PATH")
            print("Install with: brew install ffmpeg (macOS) or apt-get install ffmpeg (Linux)")
            sys.exit(1)
    
    def compress(self, 
                input_file: str,
                output_file: Optional[str] = None,
                preset: str = 'medium',
                crf: Optional[int] = None,
                scale: Optional[str] = None,
                fps: Optional[int] = None,
                codec: str = 'h264') -> Dict[str, Any]:
        """
        Compress video file
        
        Args:
            input_file: Path to input .mov file
            output_file: Path to output file (optional)
            preset: Compression preset (high/medium/low/web)
            crf: Custom CRF value (0-51, lower = better quality)
            scale: Video scale (e.g., '1280:-2')
            fps: Target FPS
            codec: Video codec (h264/h265)
        
        Returns:
            Dict with compression results
        """
        input_path = Path(input_file)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        if not output_file:
            output_file = str(input_path.with_stem(f"{input_path.stem}_compressed"))
        
        # Get preset settings
        settings = self.PRESETS.get(preset, self.PRESETS['medium']).copy()
        
        # Override with custom values if provided
        if crf is not None:
            settings['crf'] = crf
        if scale:
            settings['scale'] = scale
        
        # Build ffmpeg command
        cmd = ['ffmpeg', '-i', input_file]
        
        # Video codec
        if codec == 'h265':
            cmd.extend(['-c:v', 'libx265'])
        else:
            cmd.extend(['-c:v', 'libx264'])
        
        # CRF value
        cmd.extend(['-crf', str(settings['crf'])])
        
        # Preset
        cmd.extend(['-preset', settings.get('preset', 'medium')])
        
        # Scale if specified
        if 'scale' in settings:
            cmd.extend(['-vf', f"scale={settings['scale']}"])
        
        # FPS if specified
        if fps:
            cmd.extend(['-r', str(fps)])
        
        # Audio codec (AAC)
        cmd.extend(['-c:a', 'aac', '-b:a', '128k'])
        
        # Output file
        cmd.extend(['-y', output_file])
        
        # Run compression
        print(f"Compressing {input_file}...")
        print(f"Settings: CRF={settings['crf']}, Preset={settings.get('preset')}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Get file sizes
            input_size = input_path.stat().st_size
            output_size = Path(output_file).stat().st_size
            compression_ratio = (1 - output_size / input_size) * 100
            
            return {
                'success': True,
                'input_file': input_file,
                'output_file': output_file,
                'input_size': input_size,
                'output_size': output_size,
                'compression_ratio': f"{compression_ratio:.1f}%",
                'settings': settings
            }
        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'error': e.stderr
            }


def main():
    """Command-line interface"""
    parser = argparse.ArgumentParser(
        description='Compress .mov video files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s video.mov                    # Compress with medium preset
  %(prog)s video.mov -p high            # High quality compression
  %(prog)s video.mov -p web             # Optimize for web (720p)
  %(prog)s video.mov --crf 20           # Custom quality (0-51)
  %(prog)s video.mov --scale 1920:-2    # Scale to 1080p
  %(prog)s video.mov --fps 30           # Set to 30 FPS
  %(prog)s --web                        # Start web interface
        '''
    )
    
    parser.add_argument('input', nargs='?', help='Input .mov file')
    parser.add_argument('-o', '--output', help='Output file path')
    parser.add_argument('-p', '--preset', 
                       choices=['high', 'medium', 'low', 'web'],
                       default='medium',
                       help='Compression preset')
    parser.add_argument('--crf', type=int, 
                       help='CRF value (0-51, lower = better quality)')
    parser.add_argument('--scale', 
                       help='Video scale (e.g., 1280:-2 for 720p)')
    parser.add_argument('--fps', type=int,
                       help='Target FPS')
    parser.add_argument('--codec', choices=['h264', 'h265'],
                       default='h264',
                       help='Video codec')
    parser.add_argument('--web', action='store_true',
                       help='Start web interface')
    parser.add_argument('--list-presets', action='store_true',
                       help='List available presets')
    
    args = parser.parse_args()
    
    # List presets
    if args.list_presets:
        print("\nAvailable presets:")
        for name, settings in VideoCompressor.PRESETS.items():
            print(f"  {name:8} - {settings['description']}")
            print(f"           CRF: {settings['crf']}, Preset: {settings['preset']}")
            if 'scale' in settings:
                print(f"           Scale: {settings['scale']}")
        return
    
    # Start web interface
    if args.web:
        from web_interface import start_server
        start_server()
        return
    
    # Compress file
    if not args.input:
        parser.print_help()
        return
    
    compressor = VideoCompressor()
    result = compressor.compress(
        args.input,
        args.output,
        args.preset,
        args.crf,
        args.scale,
        args.fps,
        args.codec
    )
    
    if result['success']:
        print("\nCompression complete!")
        print(f"  Output: {result['output_file']}")
        print(f"  Size: {result['input_size'] / 1024 / 1024:.1f}MB -> {result['output_size'] / 1024 / 1024:.1f}MB")
        print(f"  Reduction: {result['compression_ratio']}")
    else:
        print("\nCompression failed:")
        print(result['error'])
        sys.exit(1)


if __name__ == '__main__':
    main()