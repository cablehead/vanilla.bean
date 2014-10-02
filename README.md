# ![Vanilla](docs/images/vanilla-logo.png) vanilla.bean!

Obligatory Sinatra style (but concurrent!) micro-web framework for [Vanilla][].

## Example

```python

    h = vanilla.Hub()
    b = h.bean(port=8000)

    @b.get('/')
    def index(request, response):
        return 'Hello World'
```

## Installation

```
    pip install vanilla.bean
```

