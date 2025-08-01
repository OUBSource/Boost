#!/usr/bin/env python3
"""
Simple static file server for Boost Messenger frontend.
Run this script to serve the static files locally.
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

def serve_static(port=8000):
    """Serve static files from the static directory"""
    
    # Change to the static directory
    static_dir = Path(__file__).parent / 'static'
    
    if not static_dir.exists():
        print(f"Error: Static directory not found at {static_dir}")
        sys.exit(1)
    
    os.chdir(static_dir)
    
    # Create server
    handler = http.server.SimpleHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"🚀 Serving Boost Messenger static files at http://localhost:{port}")
            print(f"📁 Serving from directory: {static_dir}")
            print(f"🔗 API should be running at: http://localhost:11436")
            print(f"📱 Open your browser and navigate to: http://localhost:{port}")
            print(f"⏹️  Press Ctrl+C to stop the server")
            print("-" * 60)
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Port {port} is already in use. Try a different port:")
            print(f"   python serve_static.py {port + 1}")
        else:
            print(f"❌ Error starting server: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Serve Boost Messenger static files')
    parser.add_argument('port', nargs='?', type=int, default=8000, 
                       help='Port to serve on (default: 8000)')
    
    args = parser.parse_args()
    serve_static(args.port) 