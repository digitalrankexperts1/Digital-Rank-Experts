from flask import render_template, request, jsonify

from app.extensions import db


def register_error_handlers(app):

    @app.errorhandler(400)
    def bad_request_error(error):
        if _wants_json():
            return jsonify(error="Bad request"), 400
        return render_template("400.html"), 400

    @app.errorhandler(403)
    def forbidden_error(error):
        if _wants_json():
            return jsonify(error="Forbidden"), 403
        return render_template("403.html"), 403

    @app.errorhandler(404)
    def not_found_error(error):
        if _wants_json():
            return jsonify(error="Not found"), 404
        return render_template("404.html"), 404

    @app.errorhandler(429)
    def too_many_requests_error(error):
        if _wants_json():
            return jsonify(error="Too many requests"), 429
        return render_template("429.html"), 429

    @app.errorhandler(500)
    def internal_server_error(error):
        db.session.rollback()
        if _wants_json():
            return jsonify(error="Internal server error"), 500
        return render_template("500.html"), 500


def _wants_json():
    return (
        request.path.startswith("/api/")
        or request.accept_mimetypes.best == "application/json"
    )