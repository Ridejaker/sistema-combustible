import os, json, urllib.request
from datetime import date, datetime
from functools import wraps
from flask import (Flask, request, jsonify, render_template,
                   session, redirect, url_for, flash)
from werkzeug.security import check_password_hash, generate_password_hash
from database.db_init import init_db, migrate_db, get_db_connection

app = Flask(__name__)
app.secret_key = 'TI_FuelMaster_SecretKey_2024_xK9p'

with app.app_context():
    init_db()
    migrate_db()

# ── Auth helpers ──────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('rol') != 'admin':
            return jsonify({'error': 'Acceso denegado'}), 403
        return f(*args, **kwargs)
    return decorated

def log_activity(accion, detalle=None):
    try:
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO actividad (usuario_id, username, accion, detalle, ip) VALUES (?,?,?,?,?)',
            (session.get('user_id'), session.get('username','sistema'),
             accion, detalle, request.remote_addr)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

# ── Tipo de cambio ────────────────────────────────────────
def get_tipo_cambio():
    try:
        url = 'https://open.er-api.com/v6/latest/USD'
        with urllib.request.urlopen(url, timeout=4) as r:
            return round(json.loads(r.read())['rates']['PEN'], 4)
    except Exception:
        pass
    try:
        url = 'https://api.exchangerate-api.com/v4/latest/USD'
        with urllib.request.urlopen(url, timeout=4) as r:
            return round(json.loads(r.read())['rates']['PEN'], 4)
    except Exception:
        return None

# ════════════════════════════════════════════════════════
# AUTH ROUTES
# ════════════════════════════════════════════════════════

@app.route('/login', methods=['GET','POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('bienvenida'))
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','')
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM usuarios WHERE username=? AND activo=1', (username,)
        ).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id']  = user['id']
            session['username'] = user['username']
            session['nombre']   = user['nombre']
            session['rol']      = user['rol']
            log_activity('LOGIN', f'Inicio de sesion exitoso')
            return redirect(url_for('bienvenida'))
        flash('Usuario o contrasena incorrectos', 'error')
    return render_template('login.html')

@app.route('/bienvenida')
@login_required
def bienvenida():
    return render_template('bienvenida.html',
                           nombre=session.get('nombre',''),
                           username=session.get('username',''),
                           rol=session.get('rol',''))

@app.route('/logout')
@login_required
def logout():
    log_activity('LOGOUT', 'Cierre de sesion')
    session.clear()
    return redirect(url_for('login'))

# ════════════════════════════════════════════════════════
# HTML ROUTES (protected)
# ════════════════════════════════════════════════════════

@app.route('/')
@login_required
def index():
    return render_template('index.html',
                           nombre=session.get('nombre',''),
                           username=session.get('username',''),
                           rol=session.get('rol',''))

@app.route('/liquidos')
@login_required
def liquidos_page():
    return render_template('liquidos.html',
                           nombre=session.get('nombre',''),
                           username=session.get('username',''),
                           rol=session.get('rol',''))

@app.route('/glp')
@login_required
def glp_page():
    return render_template('glp.html',
                           nombre=session.get('nombre',''),
                           username=session.get('username',''),
                           rol=session.get('rol',''))

@app.route('/usuarios')
@login_required
def usuarios_page():
    if session.get('rol') != 'admin':
        return redirect(url_for('index'))
    return render_template('usuarios.html',
                           nombre=session.get('nombre',''),
                           username=session.get('username',''),
                           rol=session.get('rol',''))

@app.route('/actividad')
@login_required
def actividad_page():
    return render_template('actividad.html',
                           nombre=session.get('nombre',''),
                           username=session.get('username',''),
                           rol=session.get('rol',''))

# ════════════════════════════════════════════════════════
# API – TIPO CAMBIO
# ════════════════════════════════════════════════════════

@app.route('/api/tipo_cambio')
@login_required
def tipo_cambio():
    tc = get_tipo_cambio()
    if tc:
        return jsonify({'tipo_cambio': tc})
    return jsonify({'tipo_cambio': None}), 503

# ════════════════════════════════════════════════════════
# API – USUARIOS (solo admin)
# ════════════════════════════════════════════════════════

@app.route('/api/usuarios', methods=['GET'])
@admin_required
def get_usuarios():
    conn = get_db_connection()
    rows = conn.execute('SELECT id,username,nombre,rol,activo,creado_en FROM usuarios ORDER BY id').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/usuarios', methods=['POST'])
@admin_required
def create_usuario():
    data = request.get_json()
    username = data.get('username','').strip()
    nombre   = data.get('nombre','').strip()
    password = data.get('password','')
    rol      = data.get('rol','supervisor')
    if not username or not nombre or not password:
        return jsonify({'error': 'Campos requeridos'}), 400
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO usuarios (username,nombre,password,rol) VALUES (?,?,?,?)',
            (username, nombre, generate_password_hash(password), rol)
        )
        conn.commit()
        log_activity('CREAR_USUARIO', f'Usuario creado: {username}')
        return jsonify({'ok': True}), 201
    except Exception as e:
        return jsonify({'error': 'El username ya existe'}), 409
    finally:
        conn.close()

@app.route('/api/usuarios/<int:uid>', methods=['PUT'])
@admin_required
def update_usuario(uid):
    data = request.get_json()
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM usuarios WHERE id=?', (uid,)).fetchone()
    if not user:
        conn.close()
        return jsonify({'error': 'No encontrado'}), 404
    nombre  = data.get('nombre', user['nombre'])
    rol     = data.get('rol',    user['rol'])
    activo  = data.get('activo', user['activo'])
    pwd_raw = data.get('password','')
    if pwd_raw:
        new_pwd = generate_password_hash(pwd_raw)
        conn.execute('UPDATE usuarios SET nombre=?,rol=?,activo=?,password=? WHERE id=?',
                     (nombre,rol,activo,new_pwd,uid))
    else:
        conn.execute('UPDATE usuarios SET nombre=?,rol=?,activo=? WHERE id=?',
                     (nombre,rol,activo,uid))
    conn.commit()
    conn.close()
    log_activity('EDITAR_USUARIO', f'Usuario editado: {user["username"]}')
    return jsonify({'ok': True})

@app.route('/api/usuarios/<int:uid>/toggle', methods=['POST'])
@admin_required
def toggle_usuario(uid):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM usuarios WHERE id=?', (uid,)).fetchone()
    if not user:
        conn.close()
        return jsonify({'error':'No encontrado'}), 404
    nuevo = 0 if user['activo'] else 1
    conn.execute('UPDATE usuarios SET activo=? WHERE id=?', (nuevo, uid))
    conn.commit()
    conn.close()
    estado = 'activado' if nuevo else 'desactivado'
    log_activity('TOGGLE_USUARIO', f'Usuario {user["username"]} {estado}')
    return jsonify({'ok': True, 'activo': nuevo})

# ════════════════════════════════════════════════════════
# API – ACTIVIDAD
# ════════════════════════════════════════════════════════

@app.route('/api/actividad')
@login_required
def get_actividad():
    conn = get_db_connection()
    rows = conn.execute(
        'SELECT * FROM actividad ORDER BY fecha DESC LIMIT 200'
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

# ════════════════════════════════════════════════════════
# API – LIQUIDOS
# ════════════════════════════════════════════════════════

FIELDS = ['planta','fecha','proveedor','chofer','placa','cliente',
          'nro_factura','nro_guia','flete_factura','producto',
          'cantidad','monto_facturado','monto_unitario',
          'tipo_cambio','monto_soles','precio']

def safe_float(v, default=0):
    try: return float(v)
    except: return default

@app.route('/api/liquidos', methods=['GET'])
@login_required
def get_liquidos():
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM liquidos ORDER BY fecha DESC, id DESC').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/liquidos', methods=['POST'])
@login_required
def create_liquido():
    d = request.get_json()
    creado_por = session.get('username','sistema')
    conn = get_db_connection()
    cur = conn.execute(
        '''INSERT INTO liquidos (planta,fecha,proveedor,chofer,placa,cliente,
           nro_factura,nro_guia,flete_factura,producto,cantidad,monto_facturado,
           monto_unitario,tipo_cambio,monto_soles,precio,creado_por)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (d['planta'],d['fecha'],d['proveedor'],d['chofer'],d['placa'],d['cliente'],
         d['nro_factura'],d['nro_guia'],safe_float(d.get('flete_factura')),
         d['producto'],safe_float(d['cantidad']),safe_float(d['monto_facturado']),
         safe_float(d['monto_unitario']),safe_float(d.get('tipo_cambio')),
         safe_float(d['monto_soles']),safe_float(d['precio']),creado_por)
    )
    conn.commit()
    row = conn.execute('SELECT * FROM liquidos WHERE id=?',(cur.lastrowid,)).fetchone()
    conn.close()
    log_activity('CREAR_LIQUIDO', f"Factura {d['nro_factura']} - {d['producto']} - {d['cantidad']} gal")
    return jsonify(dict(row)), 201

@app.route('/api/liquidos/<int:rid>', methods=['PUT'])
@login_required
def update_liquido(rid):
    d = request.get_json()
    conn = get_db_connection()
    conn.execute(
        '''UPDATE liquidos SET planta=?,fecha=?,proveedor=?,chofer=?,placa=?,cliente=?,
           nro_factura=?,nro_guia=?,flete_factura=?,producto=?,cantidad=?,monto_facturado=?,
           monto_unitario=?,tipo_cambio=?,monto_soles=?,precio=? WHERE id=?''',
        (d['planta'],d['fecha'],d['proveedor'],d['chofer'],d['placa'],d['cliente'],
         d['nro_factura'],d['nro_guia'],safe_float(d.get('flete_factura')),
         d['producto'],safe_float(d['cantidad']),safe_float(d['monto_facturado']),
         safe_float(d['monto_unitario']),safe_float(d.get('tipo_cambio')),
         safe_float(d['monto_soles']),safe_float(d['precio']),rid)
    )
    conn.commit()
    row = conn.execute('SELECT * FROM liquidos WHERE id=?',(rid,)).fetchone()
    conn.close()
    log_activity('EDITAR_LIQUIDO', f'Registro ID {rid} editado')
    return jsonify(dict(row))

@app.route('/api/liquidos/<int:rid>', methods=['DELETE'])
@login_required
def delete_liquido(rid):
    conn = get_db_connection()
    row = conn.execute('SELECT * FROM liquidos WHERE id=?',(rid,)).fetchone()
    conn.execute('DELETE FROM liquidos WHERE id=?',(rid,))
    conn.commit()
    conn.close()
    if row:
        log_activity('ELIMINAR_LIQUIDO', f"Factura {row['nro_factura']} eliminada")
    return jsonify({'ok': True})

# ════════════════════════════════════════════════════════
# API – GLP
# ════════════════════════════════════════════════════════

@app.route('/api/glp', methods=['GET'])
@login_required
def get_glp():
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM glp ORDER BY fecha DESC, id DESC').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/glp', methods=['POST'])
@login_required
def create_glp():
    d = request.get_json()
    creado_por = session.get('username','sistema')
    conn = get_db_connection()
    cur = conn.execute(
        '''INSERT INTO glp (planta,fecha,proveedor,chofer,placa,cliente,
           nro_factura,nro_guia,flete_factura,producto,cantidad,monto_facturado,
           monto_unitario,tipo_cambio,monto_soles,precio,creado_por)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (d['planta'],d['fecha'],d['proveedor'],d['chofer'],d['placa'],d['cliente'],
         d['nro_factura'],d['nro_guia'],safe_float(d.get('flete_factura')),
         d['producto'],safe_float(d['cantidad']),safe_float(d['monto_facturado']),
         safe_float(d['monto_unitario']),safe_float(d.get('tipo_cambio')),
         safe_float(d['monto_soles']),safe_float(d['precio']),creado_por)
    )
    conn.commit()
    row = conn.execute('SELECT * FROM glp WHERE id=?',(cur.lastrowid,)).fetchone()
    conn.close()
    log_activity('CREAR_GLP', f"Factura {d['nro_factura']} - {d['producto']} - {d['cantidad']} kg")
    return jsonify(dict(row)), 201

@app.route('/api/glp/<int:rid>', methods=['PUT'])
@login_required
def update_glp(rid):
    d = request.get_json()
    conn = get_db_connection()
    conn.execute(
        '''UPDATE glp SET planta=?,fecha=?,proveedor=?,chofer=?,placa=?,cliente=?,
           nro_factura=?,nro_guia=?,flete_factura=?,producto=?,cantidad=?,monto_facturado=?,
           monto_unitario=?,tipo_cambio=?,monto_soles=?,precio=? WHERE id=?''',
        (d['planta'],d['fecha'],d['proveedor'],d['chofer'],d['placa'],d['cliente'],
         d['nro_factura'],d['nro_guia'],safe_float(d.get('flete_factura')),
         d['producto'],safe_float(d['cantidad']),safe_float(d['monto_facturado']),
         safe_float(d['monto_unitario']),safe_float(d.get('tipo_cambio')),
         safe_float(d['monto_soles']),safe_float(d['precio']),rid)
    )
    conn.commit()
    row = conn.execute('SELECT * FROM glp WHERE id=?',(rid,)).fetchone()
    conn.close()
    log_activity('EDITAR_GLP', f'Registro GLP ID {rid} editado')
    return jsonify(dict(row))

@app.route('/api/glp/<int:rid>', methods=['DELETE'])
@login_required
def delete_glp(rid):
    conn = get_db_connection()
    row = conn.execute('SELECT * FROM glp WHERE id=?',(rid,)).fetchone()
    conn.execute('DELETE FROM glp WHERE id=?',(rid,))
    conn.commit()
    conn.close()
    if row:
        log_activity('ELIMINAR_GLP', f"Factura {row['nro_factura']} eliminada")
    return jsonify({'ok': True})

# ════════════════════════════════════════════════════════
# API – DASHBOARD
# ════════════════════════════════════════════════════════

@app.route('/api/dashboard')
@login_required
def dashboard():
    today = date.today().isoformat()
    conn  = get_db_connection()
    def day(table, col='monto_facturado'):
        return conn.execute(
            f'SELECT COUNT(*) cnt, COALESCE(SUM({col}),0) monto, COALESCE(SUM(cantidad),0) cantidad '
            f'FROM {table} WHERE fecha=?', (today,)).fetchone()
    liq  = day('liquidos')
    glp  = day('glp')
    week = conn.execute(
        '''SELECT fecha, COALESCE(SUM(monto_facturado),0) total FROM liquidos
           WHERE fecha >= date('now','-6 days') GROUP BY fecha ORDER BY fecha'''
    ).fetchall()
    recent = conn.execute(
        '''SELECT 'Liquidos' tipo, fecha, producto, monto_facturado total, creado_por FROM liquidos
           UNION ALL
           SELECT 'GLP', fecha, producto, monto_facturado, creado_por FROM glp
           ORDER BY fecha DESC LIMIT 8'''
    ).fetchall()
    conn.close()
    return jsonify({
        'liquidos_hoy': {'registros':liq['cnt'],'monto':round(liq['monto'],2),'cantidad':round(liq['cantidad'],2)},
        'glp_hoy':      {'registros':glp['cnt'],'monto':round(glp['monto'],2),'cantidad':round(glp['cantidad'],2)},
        'semana':       [dict(r) for r in week],
        'actividad':    [dict(r) for r in recent],
    })


# ══════════════════════════════════════════════════════════════
#  CHAT EN TIEMPO REAL
# ══════════════════════════════════════════════════════════════

@app.route('/api/chat/mensajes')
@login_required
def chat_get():
    """Devuelve mensajes desde un ID dado (polling)."""
    desde = request.args.get('desde', 0, type=int)
    conn  = get_db_connection()
    rows  = conn.execute(
        'SELECT id, username, nombre, mensaje, fecha FROM chat_mensajes WHERE id > ? ORDER BY id ASC LIMIT 50',
        (desde,)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/chat/enviar', methods=['POST'])
@login_required
def chat_enviar():
    """Guarda un nuevo mensaje."""
    data    = request.get_json(silent=True) or {}
    mensaje = (data.get('mensaje') or '').strip()
    if not mensaje or len(mensaje) > 500:
        return jsonify({'ok': False, 'error': 'Mensaje invalido'}), 400
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO chat_mensajes (username, nombre, mensaje) VALUES (?,?,?)',
        (session['username'], session['nombre'], mensaje)
    )
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/chat/ultimo_id')
@login_required
def chat_ultimo_id():
    conn = get_db_connection()
    row  = conn.execute('SELECT MAX(id) as mid FROM chat_mensajes').fetchone()
    conn.close()
    return jsonify({'id': row['mid'] or 0})


import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ════════════════════════════════════════════════════════
# SOLICITUDES DE ACCESO (público)
# ════════════════════════════════════════════════════════

@app.route('/solicitar-acceso', methods=['GET'])
def solicitar_acceso_page():
    return render_template('solicitar_acceso.html')

@app.route('/api/solicitudes', methods=['POST'])
def crear_solicitud():
    data = request.get_json()
    required = ['nombres','dni','telefono','nacimiento','correo']
    for f in required:
        if not data.get(f,'').strip():
            return jsonify({'error': f'Campo requerido: {f}'}), 400
    conn = get_db_connection()
    # Evitar DNI duplicado pendiente
    existing = conn.execute(
        "SELECT id FROM solicitudes WHERE dni=? AND estado='pendiente'", (data['dni'],)
    ).fetchone()
    if existing:
        conn.close()
        return jsonify({'error': 'Ya existe una solicitud pendiente con ese DNI'}), 409
    conn.execute(
        '''INSERT INTO solicitudes (nombres,dni,telefono,nacimiento,correo)
           VALUES (?,?,?,?,?)''',
        (data['nombres'].strip(), data['dni'].strip(), data['telefono'].strip(),
         data['nacimiento'].strip(), data['correo'].strip())
    )
    conn.commit()
    conn.close()
    return jsonify({'ok': True, 'message': 'Solicitud enviada. Technological Imperius la revisara pronto.'}), 201

@app.route('/api/solicitudes', methods=['GET'])
@admin_required
def get_solicitudes():
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM solicitudes ORDER BY fecha DESC').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/solicitudes/<int:sid>/aprobar', methods=['POST'])
@admin_required
def aprobar_solicitud(sid):
    data = request.get_json()
    username = data.get('username','').strip()
    password = data.get('password','').strip()
    if not username or not password:
        return jsonify({'error': 'Username y password requeridos'}), 400
    conn = get_db_connection()
    sol = conn.execute('SELECT * FROM solicitudes WHERE id=?', (sid,)).fetchone()
    if not sol:
        conn.close()
        return jsonify({'error': 'Solicitud no encontrada'}), 404
    # Crear usuario
    try:
        conn.execute(
            'INSERT INTO usuarios (username,nombre,password,rol) VALUES (?,?,?,?)',
            (username, sol['nombres'], generate_password_hash(password), 'supervisor')
        )
    except Exception:
        conn.close()
        return jsonify({'error': 'El username ya existe, elige otro'}), 409
    # Marcar solicitud como aprobada
    conn.execute(
        "UPDATE solicitudes SET estado='aprobado', usuario_asig=?, notas=? WHERE id=?",
        (username, data.get('notas',''), sid)
    )
    conn.commit()
    conn.close()
    log_activity('APROBAR_SOLICITUD', f"Solicitud de {sol['nombres']} aprobada -> usuario: {username}")
    return jsonify({'ok': True})

@app.route('/api/solicitudes/<int:sid>/rechazar', methods=['POST'])
@admin_required
def rechazar_solicitud(sid):
    data = request.get_json()
    conn = get_db_connection()
    conn.execute(
        "UPDATE solicitudes SET estado='rechazado', notas=? WHERE id=?",
        (data.get('notas',''), sid)
    )
    conn.commit()
    sol = conn.execute('SELECT * FROM solicitudes WHERE id=?', (sid,)).fetchone()
    conn.close()
    log_activity('RECHAZAR_SOLICITUD', f"Solicitud ID {sid} rechazada")
    return jsonify({'ok': True})


@app.route('/api/solicitudes-baja/<int:bid>/resolver', methods=['POST'])
@admin_required
def resolver_baja(bid):
    data   = request.get_json()
    accion = data.get('accion','rechazar')  # 'aprobar' or 'rechazar'
    conn   = get_db_connection()
    sol    = conn.execute('SELECT * FROM solicitudes_baja WHERE id=?', (bid,)).fetchone()
    if not sol:
        conn.close()
        return jsonify({'error':'No encontrado'}), 404
    if accion == 'aprobar':
        conn.execute('UPDATE usuarios SET activo=0 WHERE id=?', (sol['usuario_id'],))
        conn.execute("UPDATE solicitudes_baja SET estado='aprobado' WHERE id=?", (bid,))
        log_activity('BAJA_APROBADA', f"Cuenta {sol['username']} desactivada")
    else:
        conn.execute("UPDATE solicitudes_baja SET estado='rechazado' WHERE id=?", (bid,))
        log_activity('BAJA_RECHAZADA', f"Solicitud baja de {sol['username']} rechazada")
    conn.commit()
    conn.close()
    return jsonify({'ok': True})
