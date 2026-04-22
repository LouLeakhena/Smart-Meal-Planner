from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "mealplanner-dev-secret" 
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix="/")
    app.register_blueprint(auth, url_prefix="/")

    return app