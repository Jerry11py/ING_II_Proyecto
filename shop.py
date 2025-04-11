from flask import Blueprint, render_template, session, redirect, url_for, request
from db_config import get_db_connection

shop_bp = Blueprint('shop', __name__)

@shop_bp.route('/shop')
def shop_home():
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Producto")
    productos = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('shop.html', productos=productos)

#ADD TO CARRITO STEP
@shop_bp.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    cantidad = int(request.form['cantidad'])
    user_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get or create carrito for the user
    cursor.execute("SELECT id_carrito FROM Carrito WHERE id_cliente = %s AND estado = 'abierto'", (user_id,))
    carrito = cursor.fetchone()

    if not carrito:
        cursor.execute("INSERT INTO Carrito (id_cliente, fecha_creacion, estado) VALUES (%s, NOW(), 'abierto')", (user_id,))
        conn.commit()
        carrito_id = cursor.lastrowid
    else:
        carrito_id = carrito[0]

    # Check if product already in carrito
    cursor.execute("SELECT * FROM Carrito_Producto WHERE id_carrito = %s AND id_producto = %s", (carrito_id, product_id))
    existing = cursor.fetchone()

    if existing:
        cursor.execute(
            "UPDATE Carrito_Producto SET cantidad = cantidad + %s WHERE id_carrito = %s AND id_producto = %s",
            (cantidad, carrito_id, product_id)
        )
    else:
        cursor.execute(
            "INSERT INTO Carrito_Producto (id_carrito, id_producto, cantidad) VALUES (%s, %s, %s)",
            (carrito_id, product_id, cantidad)
        )

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('shop.view_cart'))

# VIEW CART STEP
@shop_bp.route('/carrito')
def view_cart():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT cp.id_producto, p.nombre, p.precio, cp.cantidad, (p.precio * cp.cantidad) AS total
        FROM Carrito c
        JOIN Carrito_Producto cp ON c.id_carrito = cp.id_carrito
        JOIN Producto p ON cp.id_producto = p.id_producto
        WHERE c.id_cliente = %s AND c.estado = 'abierto'
    """, (session['user_id'],))

    items = cursor.fetchall()
    total = sum(item['total'] for item in items)

    cursor.close()
    conn.close()

    return render_template('carrito.html', items=items, total=total)

