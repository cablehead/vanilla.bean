"""
Vanilla Bean;

Obligatory Sinatra style (but concurrent!) micro-web framework for Vanilla.
"""

import functools
import mimetypes
import urllib
import os

import routes

import vanilla.http


def __plugin__(hub):
    def bean(
            port=0,
            host='127.0.0.1',
            base_path=None):
        return Bean(hub, host, port, base_path)
    return bean


class HTTPStatus(Exception):
    def __init__(self, status):
        self.status = status


class Bean(object):
    def __init__(self, hub, host, port, base_path):
        self.hub = hub
        self.base_path = base_path
        self.routes = routes.Mapper()
        self.actions = {}

        self.server = self.hub.http.listen(host=host, port=port)
        self.port = self.server.port

        @self.server.consume
        def _(conn):
            @self.hub.spawn
            def _():
                for request in conn:
                    self.serve(request)

    def path(self, *a):
        # TODO: this isn't secure, use something like twisted.python.filepath
        if self.base_path is not None:
            a = [self.base_path] + list(a)
        return os.path.join(*a)

    class Request(vanilla.http.HTTPServer.Request):
        def reply(self, status=None, headers=None):
            if not status:
                status = vanilla.http.Status(200)
            if not headers:
                headers = {}
            sender, recver = self.server.hub.pipe()
            super(Bean.Request, self).reply(status, headers, recver)
            self.response = sender
            return sender

        def ResponseStatus(self, code):
            status = vanilla.http.Status(code)
            return HTTPStatus(status)

    def serve(self, request):
        path, query = urllib.splitquery(request.path)

        if request.headers.get('upgrade', '').lower() == 'websocket':
            environ = {'REQUEST_METHOD': 'WEBSOCKET'}
        else:
            environ = {'REQUEST_METHOD': request.method}
        match = self.routes.match(path, environ=environ)

        if not match:
            status = vanilla.http.Status(404)
            request.reply(status, {}, status[1])
            return

        f = match.pop('f')

        if environ['REQUEST_METHOD'] == 'WEBSOCKET':
            f(request.upgrade())
            return

        request.__class__ = Bean.Request
        request.response = None

        status = vanilla.http.Status(200)

        try:
            body = f(request, **match)
        except HTTPStatus, e:
            status = e.status
            body = status[1]

        if request.response:
            request.response.close()
            return

        super(Bean.Request, request).reply(status, {}, body)

    def _add_route(self, path, conditions, f):
        def wrap(*a, **kw):
            target = self.actions[f]
            return target(*a, **kw)

        f.action = f
        self.actions[f] = f

        if conditions:
            self.routes.connect(path, f=wrap, conditions=conditions)
        else:
            self.routes.connect(path, f=wrap)
        return f

    def route(self, path):
        return functools.partial(self._add_route, path, None)

    def get(self, path):
        return functools.partial(self._add_route, path, {'method': ['GET']})

    def post(self, path):
        return functools.partial(self._add_route, path, {'method': ['POST']})

    def put(self, path):
        return functools.partial(self._add_route, path, {'method': ['PUT']})

    def websocket(self, path):
        def match(environ, match_dict):
            return environ.get('REQUEST_METHOD') == 'WEBSOCKET'
        return functools.partial(self._add_route, path, {'function': match})

    def _static(self, target, request, filename=None):
        if filename:
            filename = self.path(target, filename)
        else:
            filename = self.path(target)

        typ_, encoding = mimetypes.guess_type(filename)

        headers = {}
        headers['Content-Type'] = typ_ or 'text/plain'
        if encoding:
            headers['Content-Encoding'] = encoding

        try:
            fh = open(filename)
        except:
            raise request.ResponseStatus(404)

        response = request.reply(headers=headers)

        while True:
            data = fh.read(16*1024)
            if not data:
                break
            response.send(data)
            # give other coroutines a chance to run
            self.hub.sleep(0)

        fh.close()

    def static(self, path, target):
        if os.path.isdir(self.path(target)):
            self.routes.connect(
                '%s/{filename:.*?}' % path,
                f=functools.partial(self._static, target),
                conditions={'method': ['GET']})
        else:
            self.routes.connect(
                path,
                f=functools.partial(self._static, target),
                conditions={'method': ['GET']})
