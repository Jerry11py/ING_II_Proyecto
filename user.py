from flask import Blueprint, render_template, session, redirect, url_for
from weasyprint import HTML
from db_config import get_db_connection
from flask import Response


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

@user_bp.route('/usuario/pedido/<int:pedido_id>/descargar-pdf')
def descargar_pedido_pdf(pedido_id):
    # Retrieve the pedido details using the pedido_id
    pedido = obtener_pedido_por_id(pedido_id)
    
    # Use WeasyPrint to generate the PDF
    html_content = render_template('pdf/descargar_pedido_pdf.html', pedido=pedido)
    pdf = HTML(string=html_content).write_pdf()

    # Return the PDF as a response
    return Response(pdf, mimetype='application/pdf', headers={'Content-Disposition': f'attachment; filename="pedido_{pedido_id}.pdf"'})

def obtener_pedido_por_id(pedido_id):
    from db_config import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT p.id_pedido, p.fecha_pedido, p.total, mp.nombre AS metodo, c.id_carrito
        FROM Pedido p
        JOIN Metodo_Pago mp ON p.id_metodo_pago = mp.id_metodo_pago
        JOIN Carrito c ON p.id_carrito = c.id_carrito
        WHERE p.id_pedido = %s
    """, (pedido_id,))
    
    pedido = cursor.fetchone()

    if pedido:
        pedido['productos'] = []
        cursor.execute("""
            SELECT p.nombre, p.descripcion, p.precio, cp.cantidad, (p.precio * cp.cantidad) AS subtotal
            FROM Producto p
            JOIN Carrito_Producto cp ON p.id_producto = cp.id_producto
            WHERE cp.id_carrito = %s
        """, (pedido['id_carrito'],))
        
        pedido['productos'] = cursor.fetchall()

        cursor.execute("""
            SELECT tipo, referencia, notas
            FROM Pago_Detalle
            WHERE id_pedido = %s
        """, (pedido_id,))
        
        pedido['detalle'] = cursor.fetchone()

    cursor.close()
    conn.close()

    return pedido


