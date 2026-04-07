# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# PythonAnywhere WSGI configuration for Healthcare Analytics App
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import sys

# Add your project directory to the sys.path
path = '/home/fbv2ub/healthcare-analytics'
if path not in sys.path:
    sys.path.insert(0, path)

# Import the Flask app object
# This assumes your main file is 'app.py' and the Flask variable is 'app'
from app import app as application
