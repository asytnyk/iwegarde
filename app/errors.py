from flask import render_template
from app import app, db

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def not_found_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

__author__ = "Peter Senna Tschudin"
__copyright__ = "Copyright (C) 2018 Peter Senna Tschudin"
__license__ = "GPLv2"
