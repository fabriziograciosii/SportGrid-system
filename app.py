import os
import sqlite3
import io
import csv
import json
from datetime import datetime, timedelta
from flask import Flask, jsonify, render_template, request, session, redirect, url_for, Response

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'sportgrid_secret_key_2026')

@app.context_processor
def inject_current_user():
    user_id = session.get('user_id')
    return {
        'current_user': {
            'id': user_id,
            'nombre': session.get('user_nombre'),
            'email': session.get('user_email'),
            'telefono': session.get('user_telefono'),
            'logged_in': bool(user_id),
            'categoria_padel': session.get('user_cat_padel', '7ma Categoría'),
            'posicion_padel': session.get('user_pos_padel', 'Drive'),
            'partidos_jugados': session.get('user_partidos', 14),
            'reputacion': session.get('user_reputacion', 98)
        }
    }

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'sistema_reservas.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row 
    return conn

# ==========================================
# RUTAS DE PÁGINAS (VISTAS)
# ==========================================

# 1. Home / Marketplace Multideporte
@app.route('/')
def inicio():
    return render_template('index.html')

# 2. Detalle de Club y Canchas
@app.route('/club/<int:id_club>')
def ver_club(id_club):
    return render_template('club.html', id_club=id_club)

# 3. Landing Comercial de Software para Clubes (Planes, Precios y Demo)
@app.route('/software')
def software_clubes():
    return render_template('software.html')

# 3b. Términos, Condiciones y Políticas de Cancelación (Ley 24.240)
@app.route('/terminos')
def terminos_condiciones():
    return render_template('terminos.html')

# Endpoint Botón de Arrepentimiento (Resolución 424/2020 Secretaría de Comercio)
@app.route('/api/arrepentimiento', methods=['POST'])
def registrar_arrepentimiento():
    data = request.get_json() or {}
    codigo = data.get('codigo_reserva', '').strip()
    nombre = data.get('nombre', '').strip()
    telefono = data.get('telefono', '').strip()
    motivo = data.get('motivo', '').strip()

    if not codigo or not nombre or not telefono:
        return jsonify({'error': 'Código de reserva, nombre y teléfono son obligatorios'}), 400

    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS SolicitudesArrepentimiento (
            id_solicitud INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_reserva TEXT,
            nombre TEXT,
            telefono TEXT,
            motivo TEXT,
            fecha_solicitud TEXT,
            estado TEXT DEFAULT 'Pendiente'
        )
    ''')
    fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO SolicitudesArrepentimiento (codigo_reserva, nombre, telefono, motivo, fecha_solicitud)
        VALUES (?, ?, ?, ?, ?)
    ''', (codigo, nombre, telefono, motivo, fecha_actual))
    id_solicitud = cursor.lastrowid
    conn.commit()
    conn.close()

    numero_tramite = f"REV-{id_solicitud:05d}"
    return jsonify({
        'success': True,
        'numero_tramite': numero_tramite,
        'mensaje': 'Solicitud registrada correctamente conforme a la Ley 24.240.'
    }), 201

# Endpoint para captación de clubes ("Sumar mi club")
@app.route('/api/leads-clubes', methods=['POST'])
def registrar_lead_club():
    data = request.get_json() or {}
    nombre = data.get('nombre', '').strip()
    nombre_club = data.get('nombre_club', '').strip()
    ciudad = data.get('ciudad', '').strip()
    canchas = data.get('canchas', 2)
    telefono = data.get('telefono', '').strip()
    email = data.get('email', '').strip()
    mensaje = data.get('mensaje', '').strip()

    if not nombre or not nombre_club or not telefono:
        return jsonify({'error': 'Nombre, club y teléfono son requeridos'}), 400

    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS LeadsClubes (
            id_lead INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_contacto TEXT,
            nombre_club TEXT,
            ciudad TEXT,
            canchas_cant INTEGER,
            telefono TEXT,
            email TEXT,
            mensaje TEXT,
            fecha TEXT,
            estado TEXT DEFAULT 'Nuevo'
        )
    ''')
    fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO LeadsClubes (nombre_contacto, nombre_club, ciudad, canchas_cant, telefono, email, mensaje, fecha)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (nombre, nombre_club, ciudad, canchas, telefono, email, mensaje, fecha_actual))
    conn.commit()
    conn.close()

    return jsonify({
        'success': True,
        'mensaje': '¡Gracias por tu interés! Un asesor de SportGrid se comunicará a la brevedad.'
    }), 201

# Manejadores de error personalizados (404 y 500)
@app.errorhandler(404)
def pagina_no_encontrada(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def error_servidor(e):
    return render_template('500.html'), 500

# 4. Panel Operativo del Club (Admin protegido por sesión)
@app.route('/admin')
def panel_admin():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    id_club = session.get('admin_club_id', 1)
    admin_rol = session.get('admin_rol', 'dueno')
    conn = get_db_connection()
    club = conn.execute('SELECT * FROM Clubes WHERE id_club = ?', (id_club,)).fetchone()
    canchas = conn.execute(
        '''SELECT i.*, d.nombre_deporte 
           FROM Instalaciones i 
           JOIN Deportes d ON i.id_deporte = d.id_deporte 
           WHERE i.id_club = ?''', 
        (id_club,)
    ).fetchall()
    conn.close()

    return render_template('admin.html', club=dict(club) if club else {}, canchas=[dict(c) for c in canchas], admin_rol=admin_rol)

# 4b. Portal de Acceso para Dueños y Administradores de Complejos
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        club_id_quick = request.form.get('club_id_quick')
        rol_seleccionado = request.form.get('admin_rol', 'dueno')

        conn = get_db_connection()
        if club_id_quick:
            club = conn.execute('SELECT * FROM Clubes WHERE id_club = ?', (club_id_quick,)).fetchone()
            usuario = conn.execute('SELECT * FROM Usuarios WHERE id_usuario = ?', (club['id_admin'],)).fetchone() if club else None
        else:
            usuario = conn.execute('SELECT * FROM Usuarios WHERE LOWER(email) = ? AND rol = "Admin_Club"', (email,)).fetchone()
            club = conn.execute('SELECT * FROM Clubes WHERE id_admin = ?', (usuario['id_usuario'],)).fetchone() if usuario else None

        conn.close()

        if usuario and club:
            session['admin_logged_in'] = True
            session['admin_id'] = usuario['id_usuario']
            session['admin_nombre'] = usuario['nombre_completo']
            session['admin_email'] = usuario['email']
            session['admin_club_id'] = club['id_club']
            session['admin_club_nombre'] = club['nombre_club']
            session['admin_club_ciudad'] = club['ciudad']
            session['admin_rol'] = rol_seleccionado
            return redirect(url_for('panel_admin'))
        else:
            error = 'Credenciales no encontradas. Verificá tu correo de administrador o seleccioná un complejo demo.'

    if session.get('admin_logged_in'):
        return redirect(url_for('panel_admin'))

    conn = get_db_connection()
    clubes_demo = conn.execute(
        '''SELECT c.*, u.email as admin_email, u.nombre_completo as admin_nombre 
           FROM Clubes c 
           JOIN Usuarios u ON c.id_admin = u.id_usuario 
           LIMIT 3'''
    ).fetchall()
    conn.close()

    return render_template('admin_login.html', error=error, clubes_demo=[dict(c) for c in clubes_demo])

# 4c. Cierre de Sesión del Administrador
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_id', None)
    session.pop('admin_nombre', None)
    session.pop('admin_email', None)
    session.pop('admin_club_id', None)
    session.pop('admin_club_nombre', None)
    session.pop('admin_club_ciudad', None)
    session.pop('admin_rol', None)
    return redirect(url_for('admin_login'))

# 4d. Alta de Nuevo Complejo Deportivo Oficial
@app.route('/api/admin/clubes/alta', methods=['POST'])
def api_admin_alta_club():
    data = request.get_json() or request.form
    nombre_club = data.get('nombre_club', '').strip()
    ciudad = data.get('ciudad', '').strip()
    direccion = data.get('direccion', '').strip()
    telefono = data.get('telefono', '').strip()
    alias_mp = data.get('alias_mp', '').strip()
    cantidad_canchas = int(data.get('canchas_cant', 2))
    deporte_nombre = data.get('deporte', 'Pádel').strip()
    admin_email = data.get('admin_email', '').strip().lower()
    admin_pwd = data.get('admin_password', 'admin123').strip()

    if not nombre_club or not ciudad:
        return jsonify({'error': 'El nombre del club y la ciudad son obligatorios'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    clean_name = ''.join(filter(str.isalnum, nombre_club.lower()))
    if not admin_email:
        admin_email = f"admin@{clean_name}.com"
    
    admin_existente = conn.execute('SELECT id_usuario FROM Usuarios WHERE LOWER(email) = ?', (admin_email,)).fetchone()
    if admin_existente:
        id_admin = admin_existente['id_usuario']
    else:
        cursor.execute('''
            INSERT INTO Usuarios (nombre_completo, email, telefono, rol, password)
            VALUES (?, ?, ?, 'Admin_Club', ?)
        ''', (f"Admin {nombre_club}", admin_email, telefono, admin_pwd))
        id_admin = cursor.lastrowid

    cursor.execute('''
        INSERT INTO Clubes (id_admin, nombre_club, ciudad, direccion, hora_apertura, hora_cierre, telefono, alias_mp, servicios, precio_desde)
        VALUES (?, ?, ?, ?, '08:00', '00:00', ?, ?, 'Cantina, Vestuarios, Iluminación LED, Estacionamiento, WiFi', 16000)
    ''', (id_admin, nombre_club, ciudad, direccion, telefono, alias_mp or f"{clean_name.upper()}.MP"))
    id_club = cursor.lastrowid

    dep_row = conn.execute('SELECT id_deporte FROM Deportes WHERE LOWER(nombre_deporte) = LOWER(?)', (deporte_nombre,)).fetchone()
    id_dep = dep_row['id_deporte'] if dep_row else 1

    for i in range(1, cantidad_canchas + 1):
        cursor.execute('''
            INSERT INTO Instalaciones (id_club, id_deporte, nombre_interno, caracteristicas, precio)
            VALUES (?, ?, ?, 'Cristal panorámico y césped sintético | Techada', 16000)
        ''', (id_club, id_dep, f"Cancha {i} ({deporte_nombre})"))

    productos_base = [
        ('Agua Mineral 500ml', 'Bebidas', 1200, 30),
        ('Gatorade 500ml', 'Bebidas', 1800, 24),
        ('Cerveza Lata 473ml', 'Cervezas', 2200, 48),
        ('Tubo de Pelotas Pádel (x3)', 'Pelotas/Grips', 8500, 15),
        ('Alquiler de Paleta Pádel', 'Alquiler de Paletas', 3000, 6)
    ]
    for p_nom, p_cat, p_prec, p_stk in productos_base:
        cursor.execute('''
            INSERT INTO ProductosCantina (id_club, nombre, categoria, precio, stock)
            VALUES (?, ?, ?, ?, ?)
        ''', (id_club, p_nom, p_cat, p_prec, p_stk))

    conn.commit()
    conn.close()

    return jsonify({
        'success': True,
        'id_club': id_club,
        'nombre_club': nombre_club,
        'admin_email': admin_email,
        'mensaje': f'¡Club {nombre_club} dado de alta con éxito con {cantidad_canchas} canchas!'
    }), 201

# ==========================================
# ENDPOINTS API (DATOS)
# ==========================================

# Lista de deportes disponibles en el sistema
@app.route('/api/deportes', methods=['GET'])
def obtener_deportes():
    conn = get_db_connection()
    deportes = conn.execute('SELECT * FROM Deportes ORDER BY nombre_deporte ASC').fetchall()
    conn.close()
    return jsonify([dict(d) for d in deportes])

# Lista de ciudades principales y adheridas
@app.route('/api/ciudades', methods=['GET'])
def obtener_ciudades():
    ciudades = [
        "Resistencia, Chaco",
        "Corrientes, Corrientes",
        "Buenos Aires, CABA",
        "Córdoba, Córdoba",
        "Rosario, Santa Fe",
        "Mendoza, Mendoza",
        "Posadas, Misiones",
        "Formosa, Formosa",
        "Mar del Plata, Buenos Aires",
        "La Plata, Buenos Aires",
        "Salta, Salta",
        "San Miguel de Tucumán, Tucumán",
        "Santa Fe, Santa Fe",
        "Neuquén, Neuquén",
        "San Juan, San Juan",
        "San Carlos de Bariloche, Río Negro"
    ]
    return jsonify(ciudades)

# Obtener lista de clubes (con filtro opcional de ciudad o deporte)
@app.route('/api/clubes', methods=['GET'])
def obtener_clubes():
    ciudad = request.args.get('ciudad')
    conn = get_db_connection()
    
    if ciudad and ciudad.lower() not in ['todas', 'todos', '']:
        clubes_db = conn.execute(
            'SELECT * FROM Clubes WHERE LOWER(ciudad) LIKE LOWER(?)', 
            (f"%{ciudad.split(',')[0].strip()}%",)
        ).fetchall()
    else:
        clubes_db = conn.execute('SELECT * FROM Clubes').fetchall()
    
    resultado = []
    for c in clubes_db:
        c_dict = dict(c)
        canchas = conn.execute(
            '''SELECT i.*, d.nombre_deporte 
               FROM Instalaciones i 
               JOIN Deportes d ON i.id_deporte = d.id_deporte 
               WHERE i.id_club = ?''', 
            (c['id_club'],)
        ).fetchall()
        c_dict['total_canchas'] = len(canchas)
        c_dict['deportes'] = list(set([cancha['nombre_deporte'] for cancha in canchas]))
        resultado.append(c_dict)

    conn.close()
    return jsonify(resultado)

# Detalle de un club
@app.route('/api/club/<int:id_club>', methods=['GET'])
def obtener_detalle_club(id_club):
    conn = get_db_connection()
    club = conn.execute('SELECT * FROM Clubes WHERE id_club = ?', (id_club,)).fetchone()
    
    if not club:
        conn.close()
        return jsonify({'error': 'Club no encontrado'}), 404
        
    canchas = conn.execute(
        '''SELECT i.*, d.nombre_deporte, d.duracion_turno_minutos 
           FROM Instalaciones i
           JOIN Deportes d ON i.id_deporte = d.id_deporte
           WHERE i.id_club = ?''', 
        (id_club,)
    ).fetchall()
    conn.close()
    
    data = dict(club)
    data['canchas'] = [dict(c) for c in canchas]
    return jsonify(data)

# Horarios de 08:00 a 00:00 con selección de duración (60 min o 90 min)
@app.route('/api/horarios/<int:id_instalacion>', methods=['GET'])
def obtener_horarios(id_instalacion):
    # Parámetro opcional de duración solicitada por el usuario (60 o 90)
    duracion_param = request.args.get('duracion')
    
    conn = get_db_connection()
    cancha = conn.execute(
        '''SELECT i.*, d.duracion_turno_minutos 
           FROM Instalaciones i 
           JOIN Deportes d ON i.id_deporte = d.id_deporte 
           WHERE i.id_instalacion = ?''', 
        (id_instalacion,)
    ).fetchone()
    conn.close()

    if not cancha:
        return jsonify({'error': 'Cancha no encontrada'}), 404

    if duracion_param in ['60', '90']:
        minutos_turno = int(duracion_param)
    else:
        minutos_turno = cancha['duracion_turno_minutos'] or 90

    # Rango solicitado: 08:00 a 00:00 hs (medianoche)
    hora_inicio = datetime.strptime('08:00', '%H:%M')
    hora_cierre = datetime.strptime('00:00', '%H:%M') + timedelta(days=1)
    duracion_turno = timedelta(minutes=minutos_turno)
    
    turnos = []
    hora_actual = hora_inicio
    
    while hora_actual + duracion_turno <= hora_cierre:
        turnos.append({
            'inicio': hora_actual.strftime('%H:%M'),
            'fin': (hora_actual + duracion_turno).strftime('%H:%M'),
            'duracion': minutos_turno
        })
        hora_actual += duracion_turno
        
    return jsonify(turnos)

# ==========================================
# RUTAS DE JUGADOR & MIS RESERVAS
# ==========================================

# 5. Vista "Mis Reservas" (Portal Jugador - Protegido por sesión)
@app.route('/mis-reservas')
def mis_reservas():
    if not session.get('user_id'):
        return redirect('/?auth=login')
    return render_template('mis_reservas.html')

# 5b. Cerrar sesión de jugador
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_nombre', None)
    session.pop('user_email', None)
    session.pop('user_telefono', None)
    return redirect('/')

# ==========================================
# ENDPOINTS DE AUTENTICACIÓN DE JUGADORES
# ==========================================

@app.route('/api/auth/login', methods=['POST'])
def api_auth_login():
    data = request.get_json() or request.form
    login_val = data.get('login', '').strip().lower()
    password = data.get('password', '').strip()

    if not login_val or not password:
        return jsonify({'error': 'Ingresá tu usuario/email y contraseña'}), 400

    clean_tel = ''.join(filter(str.isdigit, login_val))
    conn = get_db_connection()
    if clean_tel and len(clean_tel) >= 6:
        usuario = conn.execute(
            'SELECT * FROM Usuarios WHERE LOWER(email) = ? OR REPLACE(REPLACE(REPLACE(telefono, "-", ""), " ", ""), "+", "") LIKE ?',
            (login_val, f'%{clean_tel[-8:]}%')
        ).fetchone()
    else:
        usuario = conn.execute('SELECT * FROM Usuarios WHERE LOWER(email) = ?', (login_val,)).fetchone()

    conn.close()

    if not usuario:
        return jsonify({'error': 'Usuario no encontrado. Verificá tu correo o registrate.'}), 401

    user_dict = dict(usuario)
    stored_pwd = user_dict.get('password') or '123456'
    if stored_pwd != password:
        return jsonify({'error': 'Contraseña incorrecta'}), 401

    session['user_id'] = user_dict['id_usuario']
    session['user_nombre'] = user_dict['nombre_completo']
    session['user_email'] = user_dict['email']
    session['user_telefono'] = user_dict.get('telefono', '')
    session['user_cat_padel'] = user_dict.get('categoria_padel') or '7ma Categoría'
    session['user_pos_padel'] = user_dict.get('posicion_padel') or 'Drive'
    session['user_partidos'] = user_dict.get('partidos_jugados') or 14
    session['user_reputacion'] = user_dict.get('reputacion_asistencia') or 98

    return jsonify({
        'success': True,
        'user': {
            'id': user_dict['id_usuario'],
            'nombre': user_dict['nombre_completo'],
            'email': user_dict['email'],
            'telefono': user_dict.get('telefono', ''),
            'categoria_padel': session['user_cat_padel'],
            'posicion_padel': session['user_pos_padel'],
            'partidos_jugados': session['user_partidos'],
            'reputacion': session['user_reputacion']
        }
    })

@app.route('/api/auth/register', methods=['POST'])
def api_auth_register():
    data = request.get_json() or request.form
    nombre = data.get('nombre_completo', '').strip()
    email = data.get('email', '').strip().lower()
    telefono = data.get('telefono', '').strip()
    password = data.get('password', '').strip()

    if not nombre or not email or not password:
        return jsonify({'error': 'Completá todos los campos requeridos'}), 400

    conn = get_db_connection()
    existente = conn.execute('SELECT * FROM Usuarios WHERE LOWER(email) = ?', (email,)).fetchone()
    if existente:
        conn.close()
        return jsonify({'error': 'Ya existe una cuenta con este email'}), 409

    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO Usuarios (nombre_completo, email, telefono, rol, password)
        VALUES (?, ?, ?, 'Jugador', ?)
    ''', (nombre, email, telefono, password))
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    session['user_id'] = user_id
    session['user_nombre'] = nombre
    session['user_email'] = email
    session['user_telefono'] = telefono

    return jsonify({
        'success': True,
        'user': {
            'id': user_id,
            'nombre': nombre,
            'email': email,
            'telefono': telefono
        }
    }), 201

@app.route('/api/auth/me', methods=['GET'])
def api_auth_me():
    if session.get('user_id'):
        return jsonify({
            'logged_in': True,
            'user': {
                'id': session['user_id'],
                'nombre': session.get('user_nombre'),
                'email': session.get('user_email'),
                'telefono': session.get('user_telefono')
            }
        })
    return jsonify({'logged_in': False})

@app.route('/api/auth/logout', methods=['POST'])
def api_auth_logout():
    session.pop('user_id', None)
    session.pop('user_nombre', None)
    session.pop('user_email', None)
    session.pop('user_telefono', None)
    session.pop('user_cat_padel', None)
    session.pop('user_pos_padel', None)
    session.pop('user_partidos', None)
    session.pop('user_reputacion', None)
    return jsonify({'success': True})

# 2 B. Perfil deportivo del jugador y gamificación
@app.route('/api/usuario/perfil', methods=['GET', 'POST'])
def api_usuario_perfil():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'No autenticado'}), 401
    
    conn = get_db_connection()
    if request.method == 'POST':
        data = request.get_json() or {}
        cat_padel = data.get('categoria_padel', '7ma Categoría')
        pos_padel = data.get('posicion_padel', 'Drive')
        mano_habil = data.get('mano_habil', 'Derecha')
        cat_futbol = data.get('categoria_futbol', 'Intermedio')

        conn.execute('''
            UPDATE Usuarios
            SET categoria_padel = ?, posicion_padel = ?, mano_habil = ?, categoria_futbol = ?
            WHERE id_usuario = ?
        ''', (cat_padel, pos_padel, mano_habil, cat_futbol, user_id))
        conn.commit()

        session['user_cat_padel'] = cat_padel
        session['user_pos_padel'] = pos_padel
        conn.close()
        return jsonify({'success': True, 'mensaje': 'Perfil deportivo actualizado con éxito'})

    row = conn.execute('SELECT * FROM Usuarios WHERE id_usuario = ?', (user_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    u = dict(row)
    return jsonify({
        'id_usuario': u['id_usuario'],
        'nombre_completo': u['nombre_completo'],
        'email': u['email'],
        'telefono': u['telefono'],
        'categoria_padel': u.get('categoria_padel') or '7ma Categoría',
        'posicion_padel': u.get('posicion_padel') or 'Drive',
        'mano_habil': u.get('mano_habil') or 'Derecha',
        'categoria_futbol': u.get('categoria_futbol') or 'Intermedio',
        'partidos_jugados': u.get('partidos_jugados') or 14,
        'reputacion_asistencia': u.get('reputacion_asistencia') or 98
    })

# 3 B. Endpoints para Turnos Liberados de Último Minuto con Descuento
@app.route('/api/turnos-ofertas', methods=['GET'])
def api_obtener_turnos_ofertas():
    id_club = request.args.get('club_id')
    conn = get_db_connection()
    if id_club:
        rows = conn.execute('''
            SELECT o.*, c.nombre_club, c.ciudad, i.nombre_interno as nombre_cancha, d.nombre_deporte
            FROM OfertasUltimoMinuto o
            JOIN Clubes c ON o.id_club = c.id_club
            JOIN Instalaciones i ON o.id_instalacion = i.id_instalacion
            JOIN Deportes d ON i.id_deporte = d.id_deporte
            WHERE o.estado = 'Activa' AND o.id_club = ?
            ORDER BY o.fecha ASC, o.hora_inicio ASC
        ''', (id_club,)).fetchall()
    else:
        rows = conn.execute('''
            SELECT o.*, c.nombre_club, c.ciudad, i.nombre_interno as nombre_cancha, d.nombre_deporte
            FROM OfertasUltimoMinuto o
            JOIN Clubes c ON o.id_club = c.id_club
            JOIN Instalaciones i ON o.id_instalacion = i.id_instalacion
            JOIN Deportes d ON i.id_deporte = d.id_deporte
            WHERE o.estado = 'Activa'
            ORDER BY o.fecha ASC, o.hora_inicio ASC
        ''').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/admin/turnos-ofertas', methods=['POST'])
def api_admin_crear_turno_oferta():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'No autorizado'}), 401
    
    id_club = session.get('admin_club_id', 1)
    data = request.get_json() or {}
    id_instalacion = data.get('id_instalacion')
    fecha = data.get('fecha')
    hora_inicio = data.get('hora_inicio')
    precio_original = float(data.get('precio_original', 16000))
    precio_oferta = float(data.get('precio_oferta', 12000))
    descuento_porc = int(round((1 - precio_oferta / precio_original) * 100)) if precio_original > 0 else 20
    descripcion = data.get('descripcion', 'Turno liberado con descuento especial')

    if not id_instalacion or not fecha or not hora_inicio:
        return jsonify({'error': 'Faltan campos obligatorios'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO OfertasUltimoMinuto (id_club, id_instalacion, fecha, hora_inicio, precio_original, precio_oferta, descuento_porc, descripcion)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (id_club, id_instalacion, fecha, hora_inicio, precio_original, precio_oferta, descuento_porc, descripcion))
    id_oferta = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'id_oferta': id_oferta, 'mensaje': '¡Oferta de último minuto publicada!'}), 201

@app.route('/api/admin/turnos-ofertas/<int:id_oferta>/eliminar', methods=['POST'])
def api_admin_eliminar_turno_oferta(id_oferta):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'No autorizado'}), 401
    id_club = session.get('admin_club_id', 1)
    conn = get_db_connection()
    conn.execute('DELETE FROM OfertasUltimoMinuto WHERE id_oferta = ? AND id_club = ?', (id_oferta, id_club))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ==========================================
# ENDPOINTS REST DE RESERVAS Y TRANSACCIONES
# ==========================================

# Listar reservas (con filtros por club, fecha, instalación o teléfono)
@app.route('/api/reservas', methods=['GET'])
def listar_reservas():
    club_id = request.args.get('club_id')
    fecha = request.args.get('fecha')
    instalacion_id = request.args.get('instalacion_id')
    usuario_telefono = request.args.get('telefono')

    query = '''
        SELECT r.*, i.nombre_interno as cancha_nombre, i.id_club, 
               c.nombre_club, c.ciudad, c.direccion as club_direccion, c.telefono as club_telefono,
               d.nombre_deporte
        FROM Reservas r
        JOIN Instalaciones i ON r.id_instalacion = i.id_instalacion
        JOIN Clubes c ON i.id_club = c.id_club
        JOIN Deportes d ON i.id_deporte = d.id_deporte
        WHERE r.estado != 'Cancelada'
    '''
    params = []

    if club_id:
        query += ' AND i.id_club = ?'
        params.append(club_id)
    if fecha:
        query += ' AND r.fecha = ?'
        params.append(fecha)
    if instalacion_id:
        query += ' AND r.id_instalacion = ?'
        params.append(instalacion_id)
    if usuario_telefono:
        clean_tel = ''.join(filter(str.isdigit, usuario_telefono))
        query += ' AND REPLACE(REPLACE(r.titular_telefono, "-", ""), " ", "") LIKE ?'
        params.append(f'%{clean_tel[-8:]}%')

    # Si es una consulta desde el portal del jugador ("Mis Reservas" sin club_id ni instalacion_id)
    if not club_id and not instalacion_id:
        user_id = session.get('user_id')
        if not user_id:
            # Si el usuario NO está logueado, no existen reservas sin datos
            return jsonify([])
        
        user_tel = session.get('user_telefono')
        if user_tel:
            clean_tel = ''.join(filter(str.isdigit, user_tel))
            if len(clean_tel) >= 6:
                query += ' AND (r.id_usuario = ? OR REPLACE(REPLACE(r.titular_telefono, "-", ""), " ", "") LIKE ?)'
                params.extend([user_id, f'%{clean_tel[-8:]}%'])
            else:
                query += ' AND r.id_usuario = ?'
                params.append(user_id)
        else:
            query += ' AND r.id_usuario = ?'
            params.append(user_id)

    query += ' ORDER BY r.fecha ASC, r.hora_inicio ASC'

    conn = get_db_connection()
    reservas = conn.execute(query, params).fetchall()
    conn.close()

    return jsonify([dict(r) for r in reservas])

# Crear una nueva reserva (persistencia real con validación de solapamiento)
@app.route('/api/reservas', methods=['POST'])
def crear_reserva():
    data = request.get_json() or request.form
    id_instalacion = data.get('id_instalacion')
    fecha = data.get('fecha') # YYYY-MM-DD
    hora_inicio = data.get('hora_inicio') # HH:MM
    duracion = int(data.get('duracion', 90))
    titular_nombre = data.get('titular_nombre')
    titular_telefono = data.get('titular_telefono')
    titular_email = data.get('titular_email', '')
    metodo_pago = data.get('metodo_pago', 'Mercado Pago')
    monto_total = float(data.get('monto_total', 16000))
    monto_sena = float(data.get('monto_sena', 8000 if metodo_pago == 'Mercado Pago' else 0))
    codigo_mp = data.get('codigo_mp', '')

    if not (id_instalacion and fecha and hora_inicio and titular_nombre and titular_telefono):
        return jsonify({'error': 'Faltan campos obligatorios para confirmar la reserva'}), 400

    # Calcular hora fin
    inicio_dt = datetime.strptime(hora_inicio, '%H:%M')
    fin_dt = inicio_dt + timedelta(minutes=duracion)
    hora_fin = fin_dt.strftime('%H:%M')

    conn = get_db_connection()

    # Validar que no haya solapamiento en la misma fecha e instalación
    solapada = conn.execute('''
        SELECT * FROM Reservas 
        WHERE id_instalacion = ? AND fecha = ? AND estado != 'Cancelada'
        AND (
            (hora_inicio <= ? AND hora_fin > ?) OR
            (hora_inicio < ? AND hora_fin >= ?) OR
            (hora_inicio >= ? AND hora_fin <= ?)
        )
    ''', (id_instalacion, fecha, hora_inicio, hora_inicio, hora_fin, hora_fin, hora_inicio, hora_fin)).fetchone()

    if solapada:
        conn.close()
        return jsonify({'error': f'La cancha ya se encuentra reservada en el horario {solapada["hora_inicio"]} - {solapada["hora_fin"]} hs'}), 409

    import random
    codigo_reserva = f'#SG-{random.randint(1000, 9999)}'
    if not codigo_mp and metodo_pago == 'Mercado Pago':
        codigo_mp = f'#MP-{random.randint(10000000, 99999999)}'

    user_id = session.get('user_id', 1)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO Reservas (id_usuario, id_instalacion, fecha, hora_inicio, hora_fin, estado,
                              titular_nombre, titular_telefono, titular_email, metodo_pago,
                              monto_total, monto_sena, codigo_reserva, codigo_mp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, id_instalacion, fecha, hora_inicio, hora_fin, 'Confirmada',
          titular_nombre, titular_telefono, titular_email, metodo_pago,
          monto_total, monto_sena, codigo_reserva, codigo_mp))

    id_reserva = cursor.lastrowid
    conn.commit()

    # Obtener detalles completos para responder
    reserva_creada = conn.execute('''
        SELECT r.*, i.nombre_interno as cancha_nombre, c.nombre_club, c.direccion as club_direccion
        FROM Reservas r
        JOIN Instalaciones i ON r.id_instalacion = i.id_instalacion
        JOIN Clubes c ON i.id_club = c.id_club
        WHERE r.id_reserva = ?
    ''', (id_reserva,)).fetchone()
    conn.close()

    return jsonify(dict(reserva_creada)), 201

# Cancelar una reserva
@app.route('/api/reservas/<int:id_reserva>/cancelar', methods=['POST'])
def cancelar_reserva(id_reserva):
    conn = get_db_connection()
    reserva = conn.execute('SELECT * FROM Reservas WHERE id_reserva = ?', (id_reserva,)).fetchone()
    if not reserva:
        conn.close()
        return jsonify({'error': 'Reserva no encontrada'}), 404

    conn.execute('UPDATE Reservas SET estado = "Cancelada" WHERE id_reserva = ?', (id_reserva,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'mensaje': 'Reserva cancelada con éxito'})

# ==========================================
# ENDPOINTS DE CONFIGURACIÓN DEL CLUB (ADMIN)
# ==========================================

@app.route('/api/admin/club/configuracion', methods=['GET', 'POST'])
def admin_configuracion_club():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'No autorizado'}), 401
    
    id_club = session.get('admin_club_id', 1)
    conn = get_db_connection()

    if request.method == 'POST':
        if session.get('admin_rol') == 'recepcion':
            conn.close()
            return jsonify({'error': 'Acceso restringido a dueños y administradores generales'}), 403

        data = request.get_json() or request.form
        nombre_club = data.get('nombre_club')
        direccion = data.get('direccion')
        telefono = data.get('telefono')
        alias_mp = data.get('alias_mp')
        hora_apertura = data.get('hora_apertura')
        hora_cierre = data.get('hora_cierre')
        servicios = data.get('servicios')
        precio_desde = data.get('precio_desde')
        link_grupo_wa = data.get('link_grupo_wa')

        conn.execute('''
            UPDATE Clubes 
            SET nombre_club = COALESCE(?, nombre_club),
                direccion = COALESCE(?, direccion),
                telefono = COALESCE(?, telefono),
                alias_mp = COALESCE(?, alias_mp),
                hora_apertura = COALESCE(?, hora_apertura),
                hora_cierre = COALESCE(?, hora_cierre),
                servicios = COALESCE(?, servicios),
                precio_desde = COALESCE(?, precio_desde),
                link_grupo_wa = COALESCE(?, link_grupo_wa)
            WHERE id_club = ?
        ''', (nombre_club, direccion, telefono, alias_mp, hora_apertura, hora_cierre, servicios, precio_desde, link_grupo_wa, id_club))
        conn.commit()
        if nombre_club:
            session['admin_club_nombre'] = nombre_club

    club = conn.execute('SELECT * FROM Clubes WHERE id_club = ?', (id_club,)).fetchone()
    canchas = conn.execute(
        '''SELECT i.*, d.nombre_deporte 
           FROM Instalaciones i 
           JOIN Deportes d ON i.id_deporte = d.id_deporte 
           WHERE i.id_club = ?''', 
        (id_club,)
    ).fetchall()
    conn.close()

    data = dict(club)
    data['canchas'] = [dict(c) for c in canchas]
    return jsonify(data)

# ==========================================
# 1. MÓDULO CANTINA & KIOSCO (POS Y CIERRE DE CAJA)
# ==========================================

@app.route('/api/cantina/productos', methods=['GET', 'POST'])
def cantina_productos():
    conn = get_db_connection()
    if request.method == 'POST':
        if not session.get('admin_logged_in'):
            conn.close()
            return jsonify({'error': 'No autorizado'}), 401
        data = request.get_json() or request.form
        id_club = session.get('admin_club_id', 1)
        nombre = data.get('nombre')
        categoria = data.get('categoria', 'Bebidas')
        precio = float(data.get('precio', 0))
        stock = int(data.get('stock', 0))

        if not nombre or precio <= 0:
            conn.close()
            return jsonify({'error': 'Nombre y precio válido son requeridos'}), 400

        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO ProductosCantina (id_club, nombre, categoria, precio, stock)
            VALUES (?, ?, ?, ?, ?)
        ''', (id_club, nombre, categoria, precio, stock))
        id_prod = cursor.lastrowid
        conn.commit()
        conn.close()
        return jsonify({'id_producto': id_prod, 'nombre': nombre, 'precio': precio, 'stock': stock}), 201

    club_id = request.args.get('club_id') or session.get('admin_club_id', 1)
    prods = conn.execute('SELECT * FROM ProductosCantina WHERE id_club = ? ORDER BY categoria, nombre', (club_id,)).fetchall()
    conn.close()
    return jsonify([dict(p) for p in prods])

@app.route('/api/cantina/ventas', methods=['GET', 'POST'])
def cantina_ventas():
    conn = get_db_connection()
    if request.method == 'POST':
        if not session.get('admin_logged_in'):
            conn.close()
            return jsonify({'error': 'No autorizado'}), 401
        data = request.get_json() or {}
        id_club = session.get('admin_club_id', 1)
        id_reserva = data.get('id_reserva')
        metodo_pago = data.get('metodo_pago', 'Efectivo')
        items = data.get('items', [])
        total = float(data.get('total', 0))
        fecha_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if not items or total <= 0:
            conn.close()
            return jsonify({'error': 'No hay artículos en la comanda'}), 400

        cursor = conn.cursor()
        for it in items:
            cursor.execute('UPDATE ProductosCantina SET stock = MAX(0, stock - ?) WHERE id_producto = ?',
                           (it.get('cantidad', 1), it.get('id_producto')))

        cursor.execute('''
            INSERT INTO VentasCantina (id_club, id_reserva, fecha_hora, total, metodo_pago, detalle_json)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (id_club, id_reserva, fecha_hora, total, metodo_pago, json.dumps(items)))
        id_venta = cursor.lastrowid
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'id_venta': id_venta, 'total': total}), 201

    club_id = request.args.get('club_id') or session.get('admin_club_id', 1)
    fecha = request.args.get('fecha') or datetime.now().strftime('%Y-%m-%d')
    ventas = conn.execute('''
        SELECT * FROM VentasCantina 
        WHERE id_club = ? AND fecha_hora LIKE ?
        ORDER BY fecha_hora DESC
    ''', (club_id, f'{fecha}%')).fetchall()
    conn.close()
    return jsonify([dict(v) for v in ventas])

@app.route('/api/admin/caja', methods=['GET'])
def admin_resumen_caja():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'No autorizado'}), 401
    
    id_club = session.get('admin_club_id', 1)
    fecha = request.args.get('fecha') or datetime.now().strftime('%Y-%m-%d')

    conn = get_db_connection()
    reservas = conn.execute('''
        SELECT r.*, i.nombre_interno 
        FROM Reservas r 
        JOIN Instalaciones i ON r.id_instalacion = i.id_instalacion
        WHERE i.id_club = ? AND r.fecha = ? AND r.estado != 'Cancelada'
    ''', (id_club, fecha)).fetchall()

    total_senas_mp = sum(r['monto_sena'] for r in reservas if r['metodo_pago'] == 'Mercado Pago')
    total_pendientes_club = sum(r['monto_total'] for r in reservas if r['metodo_pago'] == 'Club')
    total_canchas = sum(r['monto_total'] for r in reservas)

    ventas_cantina = conn.execute('''
        SELECT * FROM VentasCantina 
        WHERE id_club = ? AND fecha_hora LIKE ?
    ''', (id_club, f'{fecha}%')).fetchall()

    total_cantina = sum(v['total'] for v in ventas_cantina)
    cantina_efectivo = sum(v['total'] for v in ventas_cantina if v['metodo_pago'] == 'Efectivo')
    cantina_mp = sum(v['total'] for v in ventas_cantina if v['metodo_pago'] in ['Mercado Pago', 'QR'])

    conn.close()

    return jsonify({
        'fecha': fecha,
        'turnos_total': len(reservas),
        'total_canchas': total_canchas,
        'senas_cobradas_mp': total_senas_mp,
        'canchas_saldo_en_complejo': total_pendientes_club,
        'total_cantina': total_cantina,
        'cantina_efectivo': cantina_efectivo,
        'cantina_mp': cantina_mp,
        'caja_total_general': total_senas_mp + total_cantina,
        'estimado_total_dia': total_canchas + total_cantina
    })

# ==========================================
# 2. MÓDULO PARTIDOS ABIERTOS ("¿FALTA UNO?")
# ==========================================

@app.route('/api/partidos-abiertos', methods=['GET', 'POST'])
def partidos_abiertos():
    conn = get_db_connection()
    if request.method == 'POST':
        if not session.get('user_id') and not session.get('admin_logged_in'):
            conn.close()
            return jsonify({'error': 'Iniciá sesión para publicar un partido abierto'}), 401

        data = request.get_json() or request.form
        id_creador = session.get('user_id', 1)
        id_club = data.get('id_club')
        id_instalacion = data.get('id_instalacion')
        fecha = data.get('fecha')
        hora_inicio = data.get('hora_inicio')
        deporte = data.get('deporte', 'Pádel')
        nivel = data.get('nivel', 'Cualquiera')
        jugadores_faltantes = int(data.get('jugadores_faltantes', 1))
        descripcion = data.get('descripcion', '')
        id_reserva = data.get('id_reserva')

        if not (id_club and id_instalacion and fecha and hora_inicio):
            conn.close()
            return jsonify({'error': 'Faltan datos requeridos del partido'}), 400

        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO PartidosAbiertos (id_reserva, id_creador, id_club, id_instalacion, fecha, hora_inicio, deporte, nivel, jugadores_faltantes, descripcion, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Abierto')
        ''', (id_reserva, id_creador, id_club, id_instalacion, fecha, hora_inicio, deporte, nivel, jugadores_faltantes, descripcion))
        id_partido = cursor.lastrowid
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'id_partido': id_partido}), 201

    ciudad = request.args.get('ciudad')
    deporte = request.args.get('deporte')

    query = '''
        SELECT p.*, c.nombre_club, c.ciudad, c.direccion as club_direccion, c.telefono as club_telefono,
               i.nombre_interno as cancha_nombre, u.nombre_completo as creador_nombre
        FROM PartidosAbiertos p
        JOIN Clubes c ON p.id_club = c.id_club
        JOIN Instalaciones i ON p.id_instalacion = i.id_instalacion
        JOIN Usuarios u ON p.id_creador = u.id_usuario
        WHERE p.estado = 'Abierto'
    '''
    params = []
    if ciudad and ciudad.lower() not in ['todas', 'todos', '']:
        query += ' AND LOWER(c.ciudad) LIKE LOWER(?)'
        params.append(f'%{ciudad.split(",")[0].strip()}%')
    if deporte and deporte.lower() not in ['todos', 'todas', '']:
        query += ' AND LOWER(p.deporte) = LOWER(?)'
        params.append(deporte)

    query += ' ORDER BY p.fecha ASC, p.hora_inicio ASC'
    partidos = conn.execute(query, params).fetchall()

    res = []
    for p in partidos:
        p_dict = dict(p)
        inscritos = conn.execute('SELECT * FROM JugadoresPartido WHERE id_partido = ?', (p['id_partido'],)).fetchall()
        p_dict['inscriptos_detalle'] = [dict(i) for i in inscritos]
        p_dict['total_inscriptos'] = len(inscritos)
        res.append(p_dict)

    conn.close()
    return jsonify(res)

@app.route('/api/partidos-abiertos/<int:id_partido>/unirse', methods=['POST'])
def unirse_partido_abierto(id_partido):
    if not session.get('user_id'):
        return jsonify({'error': 'Tenés que iniciar sesión para unirte a un partido'}), 401

    conn = get_db_connection()
    partido = conn.execute('SELECT * FROM PartidosAbiertos WHERE id_partido = ?', (id_partido,)).fetchone()
    if not partido or partido['estado'] != 'Abierto':
        conn.close()
        return jsonify({'error': 'El partido ya no está disponible o está completo'}), 404

    user_id = session.get('user_id')
    nombre = session.get('user_nombre', 'Jugador')
    tel = session.get('user_telefono', '')

    ya_inscrito = conn.execute('SELECT id_inscripcion FROM JugadoresPartido WHERE id_partido = ? AND id_usuario = ?', (id_partido, user_id)).fetchone()
    if ya_inscrito:
        conn.close()
        return jsonify({'error': 'Ya te encontrás anotado en este partido'}), 409

    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO JugadoresPartido (id_partido, id_usuario, nombre_jugador, telefono, fecha_inscripcion)
        VALUES (?, ?, ?, ?, ?)
    ''', (id_partido, user_id, nombre, tel, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

    nuevos_faltantes = partido['jugadores_faltantes'] - 1
    nuevo_estado = 'Completo' if nuevos_faltantes <= 0 else 'Abierto'

    cursor.execute('UPDATE PartidosAbiertos SET jugadores_faltantes = ?, estado = ? WHERE id_partido = ?',
                   (max(0, nuevos_faltantes), nuevo_estado, id_partido))
    conn.commit()
    conn.close()

    return jsonify({
        'success': True,
        'mensaje': f'¡Te sumaste con éxito al partido de {partido["deporte"]}!',
        'nuevo_estado': nuevo_estado,
        'jugadores_faltantes': max(0, nuevos_faltantes)
    })

# ==========================================
# 3. MÓDULO ABONOS FIJOS / TURNOS RECURRENTES
# ==========================================

@app.route('/api/admin/abonos', methods=['GET', 'POST'])
def admin_abonos_fijos():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'No autorizado'}), 401

    id_club = session.get('admin_club_id', 1)
    conn = get_db_connection()

    if request.method == 'POST':
        data = request.get_json() or request.form
        id_instalacion = data.get('id_instalacion')
        dia_semana = data.get('dia_semana')
        hora_inicio = data.get('hora_inicio')
        duracion = int(data.get('duracion', 90))
        titular_nombre = data.get('titular_nombre')
        titular_telefono = data.get('titular_telefono')
        monto_mensual = float(data.get('monto_mensual', 55000))
        estado_pago = data.get('estado_pago', 'Al día')
        notas = data.get('notas', '')

        if not (id_instalacion and dia_semana and hora_inicio and titular_nombre):
            conn.close()
            return jsonify({'error': 'Faltan campos requeridos'}), 400

        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO AbonosFijos (id_club, id_instalacion, dia_semana, hora_inicio, duracion, titular_nombre, titular_telefono, monto_mensual, estado_pago, fecha_inicio, notas)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (id_club, id_instalacion, dia_semana, hora_inicio, duracion, titular_nombre, titular_telefono, monto_mensual, estado_pago, datetime.now().strftime('%Y-%m-%d'), notas))
        id_abono = cursor.lastrowid
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'id_abono': id_abono}), 201

    abonos = conn.execute('''
        SELECT a.*, i.nombre_interno as cancha_nombre, d.nombre_deporte
        FROM AbonosFijos a
        JOIN Instalaciones i ON a.id_instalacion = i.id_instalacion
        JOIN Deportes d ON i.id_deporte = d.id_deporte
        WHERE a.id_club = ?
        ORDER BY 
            CASE a.dia_semana 
                WHEN 'Lunes' THEN 1 
                WHEN 'Martes' THEN 2 
                WHEN 'Miércoles' THEN 3 
                WHEN 'Jueves' THEN 4 
                WHEN 'Viernes' THEN 5 
                WHEN 'Sábado' THEN 6 
                WHEN 'Domingo' THEN 7 
            END, a.hora_inicio ASC
    ''', (id_club,)).fetchall()
    conn.close()
    return jsonify([dict(a) for a in abonos])

@app.route('/api/admin/abonos/<int:id_abono>/estado-pago', methods=['POST'])
def cambiar_estado_pago_abono(id_abono):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'No autorizado'}), 401
    
    conn = get_db_connection()
    abono = conn.execute('SELECT * FROM AbonosFijos WHERE id_abono = ?', (id_abono,)).fetchone()
    if not abono:
        conn.close()
        return jsonify({'error': 'Abono no encontrado'}), 404

    nuevo_estado = 'Pendiente' if abono['estado_pago'] == 'Al día' else 'Al día'
    conn.execute('UPDATE AbonosFijos SET estado_pago = ? WHERE id_abono = ?', (nuevo_estado, id_abono))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'nuevo_estado': nuevo_estado})

@app.route('/api/admin/abonos/<int:id_abono>/eliminar', methods=['POST'])
def eliminar_abono_fijo(id_abono):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'No autorizado'}), 401
    
    conn = get_db_connection()
    conn.execute('DELETE FROM AbonosFijos WHERE id_abono = ?', (id_abono,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ==========================================
# 4. EXPORTACIÓN DE REPORTES (CSV / EXCEL)
# ==========================================

@app.route('/api/admin/reporte/reservas.csv')
def exportar_reporte_reservas():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    id_club = session.get('admin_club_id', 1)
    fecha_filtro = request.args.get('fecha')
    conn = get_db_connection()

    query = '''
        SELECT r.codigo_reserva, r.fecha, r.hora_inicio, r.hora_fin, 
               i.nombre_interno as cancha, d.nombre_deporte,
               r.titular_nombre, r.titular_telefono, r.titular_email,
               r.metodo_pago, r.monto_total, r.monto_sena, r.codigo_mp, r.estado
        FROM Reservas r
        JOIN Instalaciones i ON r.id_instalacion = i.id_instalacion
        JOIN Deportes d ON i.id_deporte = d.id_deporte
        WHERE i.id_club = ?
    '''
    params = [id_club]
    if fecha_filtro:
        query += ' AND r.fecha = ?'
        params.append(fecha_filtro)
    
    query += ' ORDER BY r.fecha DESC, r.hora_inicio ASC'
    rows = conn.execute(query, params).fetchall()
    club = conn.execute('SELECT nombre_club FROM Clubes WHERE id_club = ?', (id_club,)).fetchone()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow([
        'Codigo Reserva', 'Fecha', 'Inicio', 'Fin', 'Cancha', 'Deporte',
        'Titular', 'Telefono', 'Email', 'Metodo Pago', 'Monto Total ($)',
        'Monto Sena ($)', 'Codigo MercadoPago', 'Estado'
    ])

    for row in rows:
        writer.writerow([
            row['codigo_reserva'], row['fecha'], row['hora_inicio'], row['hora_fin'],
            row['cancha'], row['nombre_deporte'], row['titular_nombre'], row['titular_telefono'],
            row['titular_email'], row['metodo_pago'], row['monto_total'], row['monto_sena'],
            row['codigo_mp'], row['estado']
        ])

    nombre_club_clean = (club['nombre_club'] if club else 'Club').replace(' ', '_')
    filename = f'SportGrid_{nombre_club_clean}_Reservas_{fecha_filtro or "Historico"}.csv'

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )

# ==========================================
# 5. INTEGRACIÓN MERCADO PAGO CHECKOUT PRO & WEBHOOK
# ==========================================

@app.route('/api/mercadopago/crear-preferencia', methods=['POST'])
def crear_preferencia_mercadopago():
    data = request.get_json() or {}
    cancha_nombre = data.get('cancha_nombre', 'Turno Cancha')
    monto_sena = float(data.get('monto_sena', 8000))
    email_jugador = data.get('email', 'jugador@sportgrid.com.ar')

    import random
    pref_id = f'pref_sg_{random.randint(10000000, 99999999)}'
    init_point = f'https://www.mercadopago.com.ar/checkout/v1/redirect?pref_id={pref_id}'

    return jsonify({
        'id': pref_id,
        'init_point': init_point,
        'sandbox_init_point': init_point,
        'monto': monto_sena
    })

@app.route('/api/mercadopago/webhook', methods=['POST'])
def webhook_mercadopago():
    return jsonify({'status': 'ok', 'processed': True})

# ==========================================
# 6. MÓDULO RESEÑAS Y CALIFICACIONES
# ==========================================

@app.route('/api/club/<int:id_club>/resenas', methods=['GET', 'POST'])
def club_resenas(id_club):
    conn = get_db_connection()
    if request.method == 'POST':
        if not session.get('user_id'):
            conn.close()
            return jsonify({'error': 'Tenés que iniciar sesión para calificar este complejo'}), 401

        data = request.get_json() or request.form
        user_id = session.get('user_id')
        calificacion = int(data.get('calificacion', 5))
        comentario = data.get('comentario', '').strip()
        fecha_actual = datetime.now().strftime('%Y-%m-%d')

        if calificacion < 1 or calificacion > 5:
            conn.close()
            return jsonify({'error': 'La calificación debe ser de 1 a 5 estrellas'}), 400

        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Resenas (id_club, id_usuario, calificacion, comentario, fecha)
            VALUES (?, ?, ?, ?, ?)
        ''', (id_club, user_id, calificacion, comentario, fecha_actual))
        conn.commit()
        conn.close()
        return jsonify({'success': True}), 201

    rows = conn.execute('''
        SELECT r.*, u.nombre_completo as autor
        FROM Resenas r
        JOIN Usuarios u ON r.id_usuario = u.id_usuario
        WHERE r.id_club = ?
        ORDER BY r.fecha DESC
    ''', (id_club,)).fetchall()
    conn.close()

    resenas_list = [dict(r) for r in rows]
    promedio = round(sum(r['calificacion'] for r in resenas_list) / len(resenas_list), 1) if resenas_list else 5.0

    return jsonify({
        'promedio': promedio,
        'total': len(resenas_list),
        'resenas': resenas_list
    })

if __name__ == '__main__':
    print("Iniciando SPORTGRID en http://localhost:5001/...")
    print("-> Portal Público:      http://localhost:5001/")
    print("-> Software para Clubes: http://localhost:5001/software")
    print("-> Panel Administrativo: http://localhost:5001/admin")
    print("-> Mis Reservas:        http://localhost:5001/mis-reservas")
    app.run(debug=True, port=5001)
