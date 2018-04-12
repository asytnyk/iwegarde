from app import app, db
from app.models import User, Post, Server, Activation

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post':Post, 'Server':Server, 'Activation':Activation}

__author__ = "Peter Senna Tschudin"
__copyright__ = "Copyright (C) 2018 Peter Senna Tschudin"
__license__ = "GPLv2"
