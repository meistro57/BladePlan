from flask import Flask

app = Flask(__name__)

from . import cut_optimizer_app  # noqa: F401,E402
