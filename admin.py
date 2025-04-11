from flask import Blueprint, render_template, session, redirect, url_for, request
from db_config import get_db_connection

admin_bp = Blueprint('admin', __name__)

# Admin main menu
@admin_bp.route('/admin')
def dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
    return render_template('admin_menu.html')  # New menu page

# User management (was previously at /admin)
@admin_bp.route('/admin/users')
def dashboard_users():
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id_cliente, nombre, email, rol FROM Cliente")
    users = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('admin.html', users=users)

@admin_bp.route('/admin/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        rol = request.form['rol']

        update_query = '''
            UPDATE Cliente
            SET nombre = %s, email = %s, rol = %s
            WHERE id_cliente = %s
        '''
        cursor.execute(update_query, (nombre, email, rol, user_id))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('admin.dashboard_users'))

    cursor.execute("SELECT id_cliente, nombre, email, rol FROM Cliente WHERE id_cliente = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('edit_user.html', user=user)

@admin_bp.route('/admin/delete/<int:user_id>', methods=['POST'], endpoint='delete_user')
def delete_user(user_id):
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Cliente WHERE id_cliente = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('admin.dashboard_users'))

# productos ruta
@admin_bp.route('/admin/productos')
def admin_productos():
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))

    from db_config import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM Producto")
    productos = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('admin_productos.html', productos=productos)

#editar productos / gestionar productos 
# 

@admin_bp.route('/admin/productos/gestionar', methods=['GET', 'POST'])
@admin_bp.route('/admin/productos/gestionar/<int:id>', methods=['GET', 'POST'])
def gestionar_producto(id=None):
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        precio = float(request.form['precio'])
        stock = int(request.form['stock'])

        if id:  # EDIT
            cursor.execute("""
                UPDATE Producto
                SET nombre = %s, descripcion = %s, precio = %s, stock = %s
                WHERE id_producto = %s
            """, (nombre, descripcion, precio, stock, id))
        else:  # NEW
            cursor.execute("""
                INSERT INTO Producto (nombre, descripcion, precio, stock)
                VALUES (%s, %s, %s, %s)
            """, (nombre, descripcion, precio, stock))

        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('admin.admin_productos'))

    # GET request
    producto = None
    if id:
        cursor.execute("SELECT * FROM Producto WHERE id_producto = %s", (id,))
        producto = cursor.fetchone()

    cursor.close()
    conn.close()
    return render_template('gestionar_producto.html', producto=producto)


@admin_bp.route('/admin/productos/eliminar/<int:id>', methods=['POST'])
def eliminar_producto(id):
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Producto WHERE id_producto = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('admin.admin_productos'))
