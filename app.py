import sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'nasa_space_apps_2026_secret_key'
DB_NAME = 'nasa_trainer.db'

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol TEXT NOT NULL DEFAULT 'astronauta'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS escenarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            fuente_nasa TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            opcion_a TEXT NOT NULL,
            energia_a INTEGER NOT NULL,
            oxigeno_a INTEGER NOT NULL,
            escudo_a INTEGER NOT NULL,
            opcion_b TEXT NOT NULL,
            energia_b INTEGER NOT NULL,
            oxigeno_b INTEGER NOT NULL,
            escudo_b INTEGER NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS misiones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            nombre_cadete TEXT NOT NULL,
            energia_final INTEGER NOT NULL,
            oxigeno_final INTEGER NOT NULL,
            escudo_final INTEGER NOT NULL,
            estado TEXT NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')
    
    cursor.execute('SELECT id FROM usuarios WHERE username = ?', ('admin',))
    if not cursor.fetchone():
        cursor.execute('INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?)',
                       ('admin', generate_password_hash('123'), 'admin'))
                       
    cursor.execute('SELECT COUNT(*) FROM escenarios')
    cantidad = cursor.fetchone()[0]
    if cantidad == 0:
        datos_iniciales = [
            (
                'Tormenta Solar Clase X',
                'NASA DONKI (Space Weather Database)',
                'Una eyección de masa coronal impacta la órbita lunar. Debes equilibrar los escudos y la energía.',
                'Activar Escudo Magnético Máximo (-25% Energía, +25% Escudo)', -25, -5, 25,
                'Apagar generadores de O2 para ahorrar batería (+15% Energía, -20% Oxígeno)', 15, -20, 0
            ),
            (
                'Fallo en Invernadero Hidropónico',
                'NASA OSDR (Open Science Data Repository)',
                'Las plantas productoras de oxígeno requieren luz UV intensa, pero las baterías están bajas.',
                'Encender lámparas UV al máximo (-20% Energía, +25% Oxígeno)', -20, 25, 0,
                'Priorizar recarga solar y racionar aire (+20% Energía, -15% Oxígeno)', 20, -15, 0
            ),
            (
                'Acumulación de Regolito Lunar',
                'NASA Artemis Surface Telemetry',
                'El polvo lunar cubre los paneles solares reduciendo la generación eléctrica.',
                'Caminata espacial EVA para limpieza (+30% Energía, -15% Oxígeno, -10% Escudo)', 30, -15, -10,
                'Vibración automática de bajo consumo (+10% Energía, -5% Oxígeno)', 10, -5, 0
            )
        ]
        cursor.executemany('''
            INSERT INTO escenarios (titulo, fuente_nasa, descripcion, opcion_a, energia_a, oxigeno_a, escudo_a,
                                    opcion_b, energia_b, oxigeno_b, escudo_b)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', datos_iniciales)
        
    conn.commit()
    conn.close()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión para acceder.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('rol') != 'admin':
            flash('Acceso denegado: Se requiere rol de Administrador.', 'danger')
            return redirect(url_for('simulator'))
        return f(*args, **kwargs)
    return decorated

init_db()

@app.route('/', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('simulator'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        user = conn.execute('SELECT * FROM usuarios WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['rol'] = user['rol']
            return redirect(url_for('simulator'))
        flash('Usuario o contraseña incorrectos.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        rol = request.form.get('rol', 'astronauta')
        conn = get_db()
        try:
            conn.execute('INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?)',
                         (username, generate_password_hash(password), rol))
            conn.commit()
            flash('Registro exitoso. Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('El nombre de usuario ya existe.', 'danger')
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/simulator')
@login_required
def simulator():
    conn = get_db()
    escenarios = conn.execute('SELECT * FROM escenarios').fetchall()
    conn.close()
    lista_escenarios = [dict(row) for row in escenarios]
    return render_template('simulator.html', escenarios=lista_escenarios)

@app.route('/guardar_mision', methods=['POST'])
@login_required
def guardar_mision():
    nombre_cadete = request.form['nombre_cadete']
    energia = int(request.form['energia'])
    oxigeno = int(request.form['oxigeno'])
    escudo = int(request.form['escudo'])
    estado = request.form['estado']
    
    conn = get_db()
    conn.execute('''
        INSERT INTO misiones (usuario_id, nombre_cadete, energia_final, oxigeno_final, escudo_final, estado)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (session['user_id'], nombre_cadete, energia, oxigeno, escudo, estado))
    conn.commit()
    conn.close()
    flash('Resultado de la misión guardado en la bitácora.', 'success')
    return redirect(url_for('missions'))

@app.route('/missions')
@login_required
def missions():
    conn = get_db()
    if session['rol'] == 'admin':
        misiones = conn.execute('SELECT * FROM misiones ORDER BY fecha DESC').fetchall()
    else:
        misiones = conn.execute('SELECT * FROM misiones WHERE usuario_id = ? ORDER BY fecha DESC',
                                (session['user_id'],)).fetchall()
    conn.close()
    return render_template('missions.html', misiones=misiones)

@app.route('/missions/update/<int:id>', methods=['POST'])
@login_required
def update_mission(id):
    nuevo_nombre = request.form['nombre_cadete']
    conn = get_db()
    conn.execute('UPDATE misiones SET nombre_cadete = ? WHERE id = ?', (nuevo_nombre, id))
    conn.commit()
    conn.close()
    flash('Nombre del cadete actualizado.', 'success')
    return redirect(url_for('missions'))

@app.route('/missions/delete/<int:id>')
@login_required
def delete_mission(id):
    conn = get_db()
    conn.execute('DELETE FROM misiones WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Registro de misión eliminado.', 'success')
    return redirect(url_for('missions'))

@app.route('/admin/escenarios', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_events():
    conn = get_db()
    if request.method == 'POST':
        conn.execute('''
            INSERT INTO escenarios (titulo, fuente_nasa, descripcion, opcion_a, energia_a, oxigeno_a, escudo_a,
                                    opcion_b, energia_b, oxigeno_b, escudo_b)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request.form['titulo'], request.form['fuente_nasa'], request.form['descripcion'],
            request.form['opcion_a'], int(request.form['energia_a']), int(request.form['oxigeno_a']), int(request.form['escudo_a']),
            request.form['opcion_b'], int(request.form['energia_b']), int(request.form['oxigeno_b']), int(request.form['escudo_b'])
        ))
        conn.commit()
        flash('Nuevo escenario NASA agregado correctamente.', 'success')
        return redirect(url_for('admin_events'))
        
    escenarios = conn.execute('SELECT * FROM escenarios').fetchall()
    conn.close()
    return render_template('admin_events.html', escenarios=escenarios)

@app.route('/admin/escenarios/delete/<int:id>')
@login_required
@admin_required
def delete_event(id):
    conn = get_db()
    conn.execute('DELETE FROM escenarios WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Escenario eliminado.', 'success')
    return redirect(url_for('admin_events'))

if __name__ == '__main__':
    app.run(debug=True)