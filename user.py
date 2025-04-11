from flask import Blueprint, render_template, session, redirect, url_for

user_bp = Blueprint('user', __name__)

@user_bp.route('/usuario')
def user_menu():
    if session.get('role') != 'user':
        return redirect(url_for('auth.login'))
    return render_template('user_menu.html')
