# #####################################################
# Its a modified oauth2client.tools to meet selenium
# requirements (webdriver instead of external
#  webbrowser). Also it was modified for python3 to
# work without six library
# #####################################################
import src.ef_connector
import http.server as BaseHTTPServer
import http.client as http_client
import urllib
import logging
import socket
from oauth2client import _helpers
from oauth2client import client
import sys

import src.ef_distribution


__all__ = ['argparser', 'run_flow', 'message_if_missing']

_CLIENT_SECRETS_MESSAGE = """WARNING: Please configure OAuth 2.0
To make this sample run you will need to populate the client_secrets.json file
found at:
   {file_path}
with information from the APIs Console <https://code.google.com/apis/console>.
"""

_FAILED_START_MESSAGE = """
Failed to start a local webserver listening on either port 8080
or port 8090. Please check your firewall settings and locally
running programs that may be blocking or using those ports.
Falling back to --noauth_local_webserver and continuing with
authorization.
"""

_BROWSER_OPENED_MESSAGE = """
Your browser has been opened to visit:
    {address}
If your browser is on a different machine then exit and re-run this
application with the command-line parameter
  --noauth_local_webserver
"""

_GO_TO_LINK_MESSAGE = """
Go to the following link in your browser:
    {address}
"""

def _CreateArgumentParser():
    try:
        import argparse
    except ImportError:  # pragma: NO COVER
        return None
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--auth_host_name', default='localhost',
                        help='Hostname when running a local web server.')
    parser.add_argument('--noauth_local_webserver', action='store_true',
                        default=False, help='Do not run a local web server.')
    parser.add_argument('--auth_host_port', default=[8080, 8090], type=int,
                        nargs='*', help='Port web server should listen on.')
    parser.add_argument(
        '--logging_level', default='ERROR',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Set the logging level of detail.')
    return parser


# argparser is an ArgumentParser that contains command-line options expected
# by tools.run(). Pass it in as part of the 'parents' argument to your own
# ArgumentParser.
argparser = _CreateArgumentParser()



class ClientRedirectServer(BaseHTTPServer.HTTPServer):
    """A server to handle OAuth 2.0 redirects back to localhost.

    Waits for a single request and parses the query parameters
    into query_params and then stops serving.
    """
    query_params = {}


class ClientRedirectHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    """A handler for OAuth 2.0 redirects back to localhost.

    Waits for a single request and parses the query parameters
    into the servers query_params and then stops serving.
    """

    def do_GET(self):
        """Handle a GET request.

        Parses the query parameters and prints a message
        if the flow has completed. Note that we can't detect
        if an error occurred.
        """
        self.send_response(http_client.OK)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        parts = urllib.parse.urlparse(self.path)
        query = _helpers.parse_unique_urlencoded(parts.query)
        self.server.query_params = query
        self.wfile.write(
            b'<html><head><title>Authentication Status</title></head>')
        self.wfile.write(
            b'<body><p>The authentication flow has completed.</p>')
        self.wfile.write(b'</body></html>')

    def log_message(self, format, *args):
        """Do not log messages to stdout while running as cmd. line program."""


#@_helpers.positional(8)
def run_flow(flow, storage, account_nr, proxy_host, proxy_port, proxy_type,
             proxy_user, proxy_pass, flags=None, http=None):
    """Core code for a command-line application.

    The ``run()`` function is called from your application and runs
    through all the steps to obtain credentials. It takes a ``Flow``
    argument and attempts to open an authorization server page in the
    user's default web browser. The server asks the user to grant your
    application access to the user's data. If the user grants access,
    the ``run()`` function returns new credentials. The new credentials
    are also stored in the ``storage`` argument, which updates the file
    associated with the ``Storage`` object.

    It presumes it is run from a command-line application and supports the
    following flags:

        ``--auth_host_name`` (string, default: ``localhost``)
           Host name to use when running a local web server to handle
           redirects during OAuth authorization.

        ``--auth_host_port`` (integer, default: ``[8080, 8090]``)
           Port to use when running a local web server to handle redirects
           during OAuth authorization. Repeat this option to specify a list
           of values.

        ``--[no]auth_local_webserver`` (boolean, default: ``True``)
           Run a local web server to handle redirects during OAuth
           authorization.

    The tools module defines an ``ArgumentParser`` the already contains the
    flag definitions that ``run()`` requires. You can pass that
    ``ArgumentParser`` to your ``ArgumentParser`` constructor::

        parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            parents=[tools.argparser])
        flags = parser.parse_args(argv)

    Args:
        flow: Flow, an OAuth 2.0 Flow to step through.
        storage: Storage, a ``Storage`` to store the credential in.
        proxy_host: obviously
        proxy_port: obviously
        proxy_type: obviously
        proxy_user: obviously
        proxy_pass: obviously
        flags: ``argparse.Namespace``, (Optional) The command-line flags. This
               is the object returned from calling ``parse_args()`` on
               ``argparse.ArgumentParser`` as described above. Defaults
               to ``argparser.parse_args()``.
        http: An instance of ``httplib2.Http.request`` or something that
              acts like it.

    Returns:
        Credentials, the obtained credential.
    """
    if flags is None:
        flags = argparser.parse_args()
    logging.getLogger().setLevel(getattr(logging, flags.logging_level))
    if not flags.noauth_local_webserver:
        success = False
        port_number = 0
        for port in flags.auth_host_port:
            port_number = port
            try:
                httpd = ClientRedirectServer((flags.auth_host_name, port),
                                             ClientRedirectHandler)
            except socket.error:
                pass
            else:
                success = True
                break
        flags.noauth_local_webserver = not success
        if not success:
            print(_FAILED_START_MESSAGE)

    if not flags.noauth_local_webserver:
        oauth_callback = 'http://{host}:{port}/'.format(
            host=flags.auth_host_name, port=port_number)
    else:
        oauth_callback = client.OOB_CALLBACK_URN
    flow.redirect_uri = oauth_callback
    authorize_url = flow.step1_get_authorize_url()

    if not flags.noauth_local_webserver:
        import webbrowser
        try:
            src.ef_connector.Connector().yt_login_automation(account_nr, authorize_url, proxy_host,
                                                             proxy_port, proxy_type, proxy_user, proxy_pass)
        finally:
            pass
        # replaces this
        # webbrowser.open(authorize_url, new=1, autoraise=True)
        print(_BROWSER_OPENED_MESSAGE.format(address=authorize_url))
    else:
        print(_GO_TO_LINK_MESSAGE.format(address=authorize_url))

    code = None
    credential = None
    if not flags.noauth_local_webserver:
        # Added to activate time out or it will hang here
        httpd.timeout = 30
        # Added try - finally
        try:
            httpd.handle_request()
        finally:
            if 'error' in httpd.query_params:
                sys.exit('Authentication request was rejected.')
            if 'code' in httpd.query_params:
                code = httpd.query_params['code']
            else:
                print('Failed to find "code" in the query parameters '
                      'of the redirect.')
                return credential
                #sys.exit('Try running with --noauth_local_webserver.')
    else:
        code = input('Enter verification code: ').strip()

    try:
        credential = flow.step2_exchange(code, http=http)
    except client.FlowExchangeError as e:
        sys.exit('Authentication has failed: {0}'.format(e))

    storage.put(credential)
    credential.set_store(storage)
    print('Authentication successful.')

    return credential


def message_if_missing(filename):
    """Helpful message to display if the CLIENT_SECRETS file is missing."""
    return _CLIENT_SECRETS_MESSAGE.format(file_path=filename)

