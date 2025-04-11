from flask import Blueprint, render_template, request, redirect, url_for, session
from db_config import get_db_connection
import bcrypt

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'].encode('utf-8')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Cliente WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and bcrypt.checkpw(password, user['contraseña'].encode('utf-8')):
            session['user_id'] = user['id_cliente']
            session['role'] = user.get('rol', 'user')  # Default role: 'user'

            if session['role'] == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('user.user_menu'))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        telefono = request.form['telefono']
        direccion = request.form['direccion']
        password = request.form['password'].encode('utf-8')

        # Hash the password
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            query = """
                INSERT INTO Cliente (nombre, email, telefono, direccion, contraseña, rol)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (nombre, email, telefono, direccion, hashed_password, 'user'))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('auth.login'))
        except Exception as e:
            return render_template('register.html', error=str(e))

    return render_template('register.html')



@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
