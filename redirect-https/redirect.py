#!/usr/bin/env python
"""
Based on: https://gist.github.com/shreddd/b7991ab491384e3c3331

Simple HTTP URL redirector
Shreyas Cholia 10/01/2015

usage: redirect.py [-h] [--port PORT] [--ip IP] redirect_url

HTTP redirect server

positional arguments:
  redirect_url

optional arguments:
  -h, --help            show this help message and exit
  --port PORT, -p PORT  port to listen on
  --ip IP, -i IP        host interface to listen on
"""
import SimpleHTTPServer
import SocketServer
import sys
import argparse

def redirect_handler_factory(url):
    """
    Returns a request handler class that redirects to supplied `url`
    """
    class RedirectHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
       def do_GET(self):
           self.send_response(301)
           self.send_header('Location', url)
           self.end_headers()

    return RedirectHandler
           

def main():
    redirect_url = "https://beta.iwe.cloud/"
    port = 5000
    host = '0.0.0.0'

    redirectHandler = redirect_handler_factory(redirect_url)
    
    handler = SocketServer.TCPServer((host, port), redirectHandler)
    handler.serve_forever()

if __name__ == "__main__":
    main()
