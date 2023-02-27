from .ewsgi import JrWsgiServer


class App(JrWsgiServer):
    def __init__(self):
        super().__init__()

    def url__(self):
        return "hello world from ewsgi"


app = App()
