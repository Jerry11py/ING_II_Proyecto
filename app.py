
from flask import Flask, redirect, url_for
from auth import auth_bp
from shop import shop_bp
from admin import admin_bp
from user import user_bp


app = Flask(__name__)
app.secret_key = 'super_secret_key'

app.register_blueprint(auth_bp)
app.register_blueprint(shop_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(user_bp)

# Add this:
@app.route('/')
def index():
    return redirect(url_for('auth.login'))  # or 'shop.shop_home' if logged in



if __name__ == '__main__':
    app.run(debug=True)
