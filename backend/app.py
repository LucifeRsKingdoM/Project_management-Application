from flask import Flask, Blueprint, render_template

def create_app():
    app = Flask(__name__, 
                static_folder='C:/Users/LUCIFER/OneDrive/Desktop/Task Management/frontend/static',
                template_folder='C:/Users/LUCIFER/OneDrive/Desktop/Task Management/frontend/templates')

    # Set the secret key
    app.secret_key = 'secure_2002'
    
    # Import blueprints here to avoid circular imports
    from routes.auth_routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # Define routes here
    @app.route('/')
    def index():
        return render_template('index.html')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

