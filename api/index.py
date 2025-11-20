# Vercel serverless function entry point
# This imports the Flask app from the parent directory
import sys
import os

# Add parent directory to path to import the Flask app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stock_dashboard_backend import app

# Export the app for Vercel
__all__ = ['app']

