import socketserver
import logging
import sys

# Configure a basic logger for the patch
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Patches")

def apply_spark_patches():
    """Apply forceful patches for Spark to run on Windows."""
    # Force UnixStreamServer to TCPServer to bypass Windows limitation
    logger.info("Applying global socketserver.UnixStreamServer patch for Windows.")
    socketserver.UnixStreamServer = socketserver.TCPServer
    socketserver.UnixDatagramServer = socketserver.UDPServer
    
    # Ensure any already imported copies of socketserver (if any) are updated
    if 'socketserver' in sys.modules:
        sys.modules['socketserver'].UnixStreamServer = socketserver.TCPServer
        sys.modules['socketserver'].UnixDatagramServer = socketserver.UDPServer
