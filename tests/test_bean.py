import vanilla


class TestBean(object):
    def conn(self, app):
        return app.hub.http.connect('http://localhost:%s' % app.port)

    def test_basic(self):
        h = vanilla.Hub()
        app = h.bean()

        @app.route('/')
        def index(request, response):
            return 'index'

        response = self.conn(app).get('/').recv()
        assert response.status.code == 200
        assert response.consume() == 'index'

    def test_method(self):
        h = vanilla.Hub()
        app = h.bean()

        @app.get('/')
        def get(request, response):
            return request.method

        @app.post('/')
        def get(request, response):
            return request.consume()

        @app.websocket('/')
        def websocket(ws):
            while True:
                ws.send(ws.recv())

        conn = self.conn(app)
        response = conn.get('/').recv()
        assert response.status.code == 200
        assert response.consume() == 'GET'

        conn = self.conn(app)
        response = conn.post('/', data='toby').recv()
        assert response.status.code == 200
        assert response.consume() == 'toby'

        conn = self.conn(app)
        ws = conn.websocket('/')
        ws.send('toby')
        assert ws.recv() == 'toby'

    def test_static(self, tmpdir):
        fh = tmpdir.join('bar.html').open('w')
        fh.write('foo')
        fh.close()

        tmpdir.mkdir('static')
        fh = tmpdir.join('static', 'foo.html').open('w')
        fh.write('bar')
        fh.close()

        h = vanilla.Hub()
        app = h.bean(base_path=tmpdir.strpath)
        app.static('/', 'bar.html')
        app.static('/static', 'static')

        response = self.conn(app).get('/').recv()
        assert response.status.code == 200
        assert response.headers['Content-Type'] == 'text/html'
        assert response.consume() == 'foo'

        response = self.conn(app).get('/static/foo.html').recv()
        assert response.status.code == 200
        assert response.headers['Content-Type'] == 'text/html'
        assert response.consume() == 'bar'

        # test 404
        response = self.conn(app).get('/static/bar.html').recv()
        assert response.status.code == 404
