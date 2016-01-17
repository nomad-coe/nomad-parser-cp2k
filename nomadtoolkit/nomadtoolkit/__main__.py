"""
When this package is run on a folder with python -m nomadviewer, the current
directory is searched for calculation data. If a JSON output file is found, it
is used directly, otherwise the folder is parsed normally and the resulting
JSON file is saved and used.

After the data has been succesfully created/written a local django webserver is
created and a browser is opened. The calculation will now be browseable through
a web interface.
"""

import os
import webbrowser
from multiprocessing import Process
import argparse


def runserver():
    """Runs the django web server that will show the parsing results.
    """
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nomadtoolkit.metaviewer.mysite.settings")
    from django.core.management import call_command
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
    call_command('runserver',  url)


def openbrowser():
    """Opens a browser instance and shows the contents served by the dango
    server.
    """
    webbrowser.open("http://{}".format(url))

parser = argparse.ArgumentParser()
parser.add_argument('-v', help='Opens the browser based metainfoviewer.', action='store_true')
args = parser.parse_args()

# Run the server and open a browser
if args.v:
    url = "localhost:8000"
    p1 = Process(target=runserver)
    p1.start()
    p2 = Process(target=openbrowser)
    p2.start()
