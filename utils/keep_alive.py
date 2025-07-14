"""
Keep-alive mechanism for Replit free hosting.
Creates a simple HTTP server to prevent the application from sleeping.
"""

import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class KeepAliveHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for keep-alive requests."""
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                'status': 'alive',
                'service': 'Employee Knowledge Bot',
                'timestamp': datetime.now().isoformat(),
                'message': 'Bot is running successfully!'
            }
            
            self.wfile.write(json.dumps(response, indent=2).encode())
            
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            health_response = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'uptime': 'unknown'
            }
            
            self.wfile.write(json.dumps(health_response, indent=2).encode())
            
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            error_response = {
                'error': 'Not Found',
                'timestamp': datetime.now().isoformat()
            }
            
            self.wfile.write(json.dumps(error_response, indent=2).encode())
    
    def log_message(self, format, *args):
        """Override to use our logger instead of default logging."""
        logger.debug(f"Keep-alive request: {format % args}")

def run_server():
    """Run the keep-alive server."""
    try:
        server = HTTPServer(('0.0.0.0', 3000), KeepAliveHandler)
        logger.info("Keep-alive server started on port 3000")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Keep-alive server error: {str(e)}")

def keep_alive():
    """Start the keep-alive server in a separate thread."""
    try:
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        logger.info("Keep-alive mechanism started")
    except Exception as e:
        logger.error(f"Failed to start keep-alive mechanism: {str(e)}")
