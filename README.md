# ![Vanilla](docs/images/vanilla-logo.png) Welcome to Vanilla Bean!

Obligatory Sinatra style (but concurrent!) micro-web framework for [Vanilla][].

## Example

```python

    h = vanilla.Hub()
    b = h.bean(port=8000)

    @b.get('/')
    def index(request, response):
        response.send('Hello ')
        h.sleep(1000)
        return 'World.\n'
```

![terminal](docs/images/terminal.gif)

## Installation

```
    pip install vanilla.bean
```

[Vanilla]: https://github.com/cablehead/vanilla   "Vanilla"
