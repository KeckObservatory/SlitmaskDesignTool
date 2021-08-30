"""
Easy HTTP Handler
"""

import cgi
import sys
import threading
import datetime
import http.server
import socketserver
import traceback

try:
    from http import HTTPStatus
except:

    class HTTPStatus:
        def __new__(cls, value, phrase, desc=""):
            obj = int.__new__(cls, value)
            obj._value_ = value
            obj.phrase = phrase
            obj.description = desc

        NOT_FOUND = (404, "Not found")
        INTERNAL_SERVER_ERROR = (500, "Internal error")


from urllib.parse import urlparse, parse_qs


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


class EasyHTTPHandler(http.server.SimpleHTTPRequestHandler):
    """
    This class handles the HTTP request from clients.
    Only GET request is implemented.
    This class should be subclassed to extend the functionality.
    """

    PlainTextType = "text/plain; charset=utf-8"
    HTMLType = "text/html; charset=utf-8"
    DocRoot = "."
    logEnabled = False
    defaultFile = "index.html"

    def handleRequest(self, req, qs):
        try:
            res = self.callMethod(req, qs)
            if res:
                out, contype = res
                if not out:
                    return
                if isinstance(out, type("")):
                    out = bytes(out, "UTF-8")
                self.send_response(200, "OK")
                self.send_header("Expires", "Feb  1 17:17:37 HST 2016")
                self.send_header("Connection", "close")
                self.send_header("Content-type", contype)
                self.end_headers()
                self.wfile.write(out)
                self.wfile.flush()
            else:
                # print ("server", qs)
                self.serveFile(req, qs)
                return
        except FileNotFoundError:
            traceback.print_exc()
            self.send_error(HTTPStatus.NOT_FOUND)
        except BrokenPipeError:
            # traceback.print_exc()
            self.log_message("Broken pipe")
            return
        except Exception as e:
            traceback.print_exc()
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)

    def end_headers (self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "*")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")

        return super(EasyHTTPHandler, self).end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parts = urlparse(self.path)
        qs = parse_qs(parts.query)
        req = parts.path[1:]
        self.handleRequest(req, qs)

    def do_POST(self):
        parts = urlparse(self.path)
        len1 = self.headers.get("Content-Length", None)
        length = None
        if len1 is not None:
            length = int(len1)
        contType = self.headers.get("content-type", None)

        ctype, pdict = None, {}
        if contType is not None:
            ctype, pdict = cgi.parse_header(contType)
        if length is not None:
            pdict["CONTENT-LENGTH"] = length

        boundary = pdict.get("boundary")

        if boundary:
            pdict["boundary"] = bytes(boundary, "UTF-8")
            qs = cgi.parse_multipart(fp=self.rfile, pdict=pdict)
        else:
            qs = parse_qs(bytes.decode(self.rfile.read(length), "UTF-8"))
        req = parts.path[1:]
        self.handleRequest(req, qs)

    def address_string(self):
        host, port = self.client_address[:2]
        return host

    def translate_path(self, p):
        return p

    def serveFile(self, req, qs):
        sfile = req if len(req) > 0 else self.defaultFile
        self.path = self.DocRoot + "/" + sfile
        f = self.send_head()
        if f:
            try:
                self.copyfile(f, self.wfile)
            finally:
                f.close()
        return None, ""

    def log_message(self, format, *args):
        if self.logEnabled:
            super().log_message(format, *args)
        return

    def getDefValue(self, qstr, name, defValue):
        try:
            return qstr[name][0]
        except:
            return defValue

    def intVal(self, qstr, name, defValue=0):
        return int(self.floatVal(qstr, name, defValue))

    def boolVal(self, qstr, name):
        return 1 if qstr[name][0] == "true" else 0

    def floatVal(self, qstr, name, defValue=0):
        return float(self.getDefValue(qstr, name, str(defValue)))

    def response(self, resp, contType):
        if isinstance(resp, type("")):
            resp = bytes(resp, "UTF-8")
        return resp, contType

    def callMethod(self, req, qstr):
        try:
            if req == "":
                return False
            req = req.replace("/", "_")
            # print (req, qstr)
            fn = getattr(self, req)
            if fn:
                return fn(req, qstr)
        except Exception as e:
            return False
        return False


class EasyHTTPServerThreaded(ThreadedTCPServer):
    def __init__(self, ipnp, hdl):
        super(EasyHTTPServerThreaded, self).__init__(ipnp, hdl)

    def run4ever(self):
        try:
            self.serve_forever()
            self.shutdown()
        except Exception as e:
            traceback.print_exc()
            print("HTTPD terminated")


try:

    class EasyHTTPServer(socketserver.ForkingTCPServer):
        def __init__(self, ipnp, hdl):
            super(EasyHTTPServer, self).__init__(ipnp, hdl)

        def run4ever(self):
            try:
                self.serve_forever()
                self.shutdown()
            except Exception as e:
                traceback.print_exc()
                print("HTTPD terminated")


except:

    class EasyHTTPServer:
        def __init__(self, *kwd):
            raise Exception("EasyHTTPServer is not available on Windows")

    pass

ThreadedTCPServer.allow_reuse_address = True
socketserver.TCPServer.allow_reuse_address = True
