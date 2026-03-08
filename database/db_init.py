import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()

    # ── CHAT ──────────────────────────────────────────────
    conn.execute('''
        CREATE TABLE IF NOT EXISTS chat_mensajes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT NOT NULL,
            nombre     TEXT NOT NULL,
            mensaje    TEXT NOT NULL,
            fecha      TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        )
    ''')

    # ── USUARIOS ──────────────────────────────────────────
    conn.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    NOT NULL UNIQUE,
            nombre      TEXT    NOT NULL,
            password    TEXT    NOT NULL,
            rol         TEXT    NOT NULL DEFAULT 'supervisor',
            activo      INTEGER NOT NULL DEFAULT 1,
            creado_en   TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )
    ''')

    # ── LOG DE ACTIVIDAD ──────────────────────────────────
    conn.execute('''
        CREATE TABLE IF NOT EXISTS actividad (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id  INTEGER,
            username    TEXT    NOT NULL,
            accion      TEXT    NOT NULL,
            detalle     TEXT,
            ip          TEXT,
            fecha       TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )
    ''')

    # ── LIQUIDOS ──────────────────────────────────────────
    conn.execute('''
        CREATE TABLE IF NOT EXISTS liquidos (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            planta          TEXT    NOT NULL,
            fecha           TEXT    NOT NULL,
            proveedor       TEXT    NOT NULL,
            chofer          TEXT    NOT NULL,
            placa           TEXT    NOT NULL,
            cliente         TEXT    NOT NULL,
            nro_factura     TEXT    NOT NULL,
            nro_guia        TEXT    NOT NULL,
            flete_factura   REAL    NOT NULL DEFAULT 0,
            producto        TEXT    NOT NULL,
            cantidad        REAL    NOT NULL,
            monto_facturado REAL    NOT NULL,
            monto_unitario  REAL    NOT NULL,
            tipo_cambio     REAL    NOT NULL DEFAULT 0,
            monto_soles     REAL    NOT NULL,
            precio          REAL    NOT NULL,
            creado_por      TEXT    DEFAULT 'sistema'
        )
    ''')

    # ── GLP ───────────────────────────────────────────────
    conn.execute('''
        CREATE TABLE IF NOT EXISTS glp (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            planta          TEXT    NOT NULL,
            fecha           TEXT    NOT NULL,
            proveedor       TEXT    NOT NULL,
            chofer          TEXT    NOT NULL,
            placa           TEXT    NOT NULL,
            cliente         TEXT    NOT NULL,
            nro_factura     TEXT    NOT NULL,
            nro_guia        TEXT    NOT NULL,
            flete_factura   REAL    NOT NULL DEFAULT 0,
            producto        TEXT    NOT NULL,
            cantidad        REAL    NOT NULL,
            monto_facturado REAL    NOT NULL,
            monto_unitario  REAL    NOT NULL,
            tipo_cambio     REAL    NOT NULL,
            monto_soles     REAL    NOT NULL,
            precio          REAL    NOT NULL,
            creado_por      TEXT    DEFAULT 'sistema'
        )
    ''')

    conn.commit()

    # ── USUARIOS HARDCODEADOS (Technological Imperius) ────
    _seed_users(conn)
    conn.close()

def _seed_users(conn):
    """Crea los usuarios base si no existen."""
    users = [
        # (username, nombre, password, rol)
        ('admin_ti',   'Technological Imperius',  'TI@Admin2024!',   'admin'),
        ('MELINA-28',  'Melina',  '123456',  'supervisor'),
        ('Melanie-22', 'Annie',   '123456',  'supervisor'),
    ]
    for uname, nombre, pwd, rol in users:
        exists = conn.execute('SELECT id FROM usuarios WHERE username=?', (uname,)).fetchone()
        if not exists:
            conn.execute(
                'INSERT INTO usuarios (username, nombre, password, rol) VALUES (?,?,?,?)',
                (uname, nombre, generate_password_hash(pwd), rol)
            )
    conn.commit()

if __name__ == '__main__':
    init_db()
    print(f'Base de datos inicializada en: {DB_PATH}')


def migrate_db():
    """Add new tables if they don't exist yet."""
    conn = get_db_connection()

    # Solicitudes de acceso
    conn.execute('''
        CREATE TABLE IF NOT EXISTS solicitudes (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            nombres      TEXT    NOT NULL,
            dni          TEXT    NOT NULL,
            telefono     TEXT    NOT NULL,
            nacimiento   TEXT    NOT NULL,
            correo       TEXT    NOT NULL,
            estado       TEXT    NOT NULL DEFAULT 'pendiente',
            usuario_asig TEXT,
            notas        TEXT,
            fecha        TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )
    ''')

    # Configuracion por usuario
    conn.execute('''
        CREATE TABLE IF NOT EXISTS configuracion (
            usuario_id  INTEGER PRIMARY KEY,
            tema        TEXT    NOT NULL DEFAULT 'oscuro',
            idioma      TEXT    NOT NULL DEFAULT 'es',
            notif_email INTEGER NOT NULL DEFAULT 0,
            notif_web   INTEGER NOT NULL DEFAULT 1,
            updated_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )
    ''')

    # Solicitudes de eliminacion de cuenta
    conn.execute('''
        CREATE TABLE IF NOT EXISTS solicitudes_baja (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id  INTEGER NOT NULL,
            username    TEXT    NOT NULL,
            motivo      TEXT,
            estado      TEXT    NOT NULL DEFAULT 'pendiente',
            fecha       TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )
    ''')

    conn.commit()
    conn.close()
