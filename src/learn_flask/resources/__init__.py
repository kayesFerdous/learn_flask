from flask import current_app


def services():
    # Looked up per request, not imported: the services belong to one app.
    return current_app.extensions["services"]
