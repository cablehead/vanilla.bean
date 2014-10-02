"""
Vanilla Bean;

Obligatory Sinatra style (but concurrent!) micro-web framework for Vanilla.
"""

import functools
import mimetypes
import urllib
import os

import routes


def __plugin__(hub):
    def bean(
            port=0,
            host='127.0.0.1',
            request_timeout=20000,
            base_path=None):
        return Bean(hub, host, port, base_path, request_timeout)
    return bean


class Bean(object):
    def __init__(self, hub, host, port, base_path, request_timeout):
        self.hub = hub
        self.base_path = base_path

        self.server = self.hub.http.listen(
            host=host,
            port=port,
            request_timeout=request_timeout,
            serve=self.serve)

        self.port = self.server.port

        self.routes = routes.Mapper()
        self.actions = {}

    def path(self, *a):
        # TODO: this isn't secure, use something like twisted.python.filepath
        if self.base_path is not None:
            a = [self.base_path] + list(a)
        return os.path.join(*a)

    def serve(self, request, response):
        path, query = urllib.splitquery(request.path)

        if request.headers.get('upgrade', '').lower() == 'websocket':
            environ = {'REQUEST_METHOD': 'WEBSOCKET'}
        else:
            environ = {'REQUEST_METHOD': request.method}
        match = self.routes.match(path, environ=environ)

        if not match:
            response.status = (404, 'Not Found')
            return 'Sorry chief, page not found.'

        f = match.pop('f')
        return f(request, response, **match)

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

        def upgrade(request, response):
            upgrade.handler(response.upgrade())

        self._add_route(path, {'function': match}, upgrade)
        return lambda f: setattr(upgrade, 'handler', f)

    def _static(self, target, request, response, filename=None):
        if filename:
            filename = self.path(target, filename)
        else:
            filename = self.path(target)

        typ_, encoding = mimetypes.guess_type(filename)
        response.headers['Content-Type'] = typ_ or 'text/plain'
        if encoding:
            response.headers['Content-Encoding'] = encoding

        try:
            fh = open(filename)
        except:
            # TODO:
            raise response.HTTP404

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
