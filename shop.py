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

# CHECKOUT ROUTE
@shop_bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get open carrito
    cursor.execute("SELECT * FROM Carrito WHERE id_cliente = %s AND estado = 'abierto'", (session['user_id'],))
    carrito = cursor.fetchone()

    if not carrito:
        cursor.close()
        conn.close()
        return redirect(url_for('shop.view_cart'))

    # Get available payment methods
    cursor.execute("SELECT * FROM Metodo_Pago")
    metodos_pago = cursor.fetchall()

    if request.method == 'POST':
        metodo_id = int(request.form['metodo_pago'])

        # Calculate total of cart
        cursor.execute("""
            SELECT SUM(p.precio * cp.cantidad) AS total
            FROM Carrito_Producto cp
            JOIN Producto p ON cp.id_producto = p.id_producto
            WHERE cp.id_carrito = %s
        """, (carrito['id_carrito'],))
        total_result = cursor.fetchone()
        total = total_result['total'] or 0

        # Insert Pedido
        cursor.execute("""
            INSERT INTO Pedido (id_carrito, id_metodo_pago, fecha_pedido, total)
            VALUES (%s, %s, NOW(), %s)
        """, (carrito['id_carrito'], metodo_id, total))
        pedido_id = cursor.lastrowid  # Capture the newly created Pedido ID

        # Gather payment detail info
        tipo_pago = ''
        referencia = ''
        notas = request.form.get('notas', '')

        if request.form.get('card_name'):
            tipo_pago = 'tarjeta'
            card_number = request.form.get('card_number', '')
            referencia = '**** **** **** ' + card_number[-4:] if card_number else '****'
        elif request.form.get('transfer_id'):
            tipo_pago = 'transferencia'
            referencia = request.form['transfer_id']
        elif request.form.get('paypal_email'):
            tipo_pago = 'paypal'
            referencia = request.form['paypal_email']

        # Insert into Pago_Detalle
        cursor.execute("""
            INSERT INTO Pago_Detalle (id_pedido, tipo, referencia, notas)
            VALUES (%s, %s, %s, %s)
        """, (pedido_id, tipo_pago, referencia, notas))

        # Mark carrito as cerrado
        cursor.execute("UPDATE Carrito SET estado = 'cerrado' WHERE id_carrito = %s", (carrito['id_carrito'],))

        conn.commit()
        cursor.close()
        conn.close()

        return render_template('checkout_success.html')

    cursor.close()
    conn.close()
    return render_template('checkout.html', metodos_pago=metodos_pago)


# CONFIRM CHECKOUT

@shop_bp.route('/confirm_checkout', methods=['POST'])
def confirm_checkout():
    if 'user_id' not in session or 'carrito_id' not in session or 'selected_metodo_id' not in session:
        return redirect(url_for('auth.login'))

    carrito_id = session.pop('carrito_id')
    metodo_id = session.pop('selected_metodo_id')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get total
    cursor.execute("""
        SELECT SUM(p.precio * cp.cantidad) AS total
        FROM Carrito_Producto cp
        JOIN Producto p ON cp.id_producto = p.id_producto
        WHERE cp.id_carrito = %s
    """, (carrito_id,))
    total_result = cursor.fetchone()
    total = total_result['total'] or 0

    # Insert pedido
    cursor.execute("""
        INSERT INTO Pedido (id_carrito, id_metodo_pago, fecha_pedido, total)
        VALUES (%s, %s, NOW(), %s)
    """, (carrito_id, metodo_id, total))

    # Close carrito
    cursor.execute("UPDATE Carrito SET estado = 'cerrado' WHERE id_carrito = %s", (carrito_id,))

    conn.commit()
    cursor.close()
    conn.close()

    return render_template('checkout_success.html')
