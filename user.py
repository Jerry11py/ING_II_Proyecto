from flask import Blueprint, render_template, session, redirect, url_for

user_bp = Blueprint('user', __name__)

@user_bp.route('/usuario')
def user_menu():
    if session.get('role') != 'user':
        return redirect(url_for('auth.login'))
    return render_template('user_menu.html')

# ruta para ver pedidos en menu de usuarios
@user_bp.route('/usuario/pedidos')
def user_pedidos():
    if session.get('role') != 'user':
        return redirect(url_for('auth.login'))

    from db_config import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch all pedidos for this user
    cursor.execute("""
        SELECT p.id_pedido, p.fecha_pedido, p.total, mp.nombre AS metodo, c.id_carrito
        FROM Pedido p
        JOIN Metodo_Pago mp ON p.id_metodo_pago = mp.id_metodo_pago
        JOIN Carrito c ON p.id_carrito = c.id_carrito
        WHERE c.id_cliente = %s
        ORDER BY p.fecha_pedido DESC
    """, (session['user_id'],))
    pedidos_raw = cursor.fetchall()

    pedidos = {}
    for pedido in pedidos_raw:
        pedidos[pedido['id_pedido']] = {
            'fecha': pedido['fecha_pedido'],
            'metodo': pedido['metodo'],
            'total': pedido['total'],
            'productos': [],
            'detalle': None  # Will hold Pago_Detalle
        }

    # Get product info per pedido
    pedido_ids = tuple(pedidos.keys())
    if pedido_ids:
        format_ids = ','.join(['%s'] * len(pedido_ids))

        # Get products
        cursor.execute(f"""
            SELECT p.nombre, p.descripcion, p.precio, cp.cantidad, (p.precio * cp.cantidad) AS subtotal, ped.id_pedido
            FROM Pedido ped
            JOIN Carrito c ON ped.id_carrito = c.id_carrito
            JOIN Carrito_Producto cp ON cp.id_carrito = c.id_carrito
            JOIN Producto p ON p.id_producto = cp.id_producto
            WHERE ped.id_pedido IN ({format_ids})
        """, pedido_ids)
        productos = cursor.fetchall()
        for prod in productos:
            pedidos[prod['id_pedido']]['productos'].append(prod)

        # Get Pago_Detalle
        cursor.execute(f"""
            SELECT id_pedido, tipo, referencia, notas
            FROM Pago_Detalle
            WHERE id_pedido IN ({format_ids})
        """, pedido_ids)
        detalles = cursor.fetchall()
        for detalle in detalles:
            pedidos[detalle['id_pedido']]['detalle'] = detalle

    cursor.close()
    conn.close()

    return render_template('pedidos.html', pedidos=pedidos)
