import os
import uuid
from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

# crear instancia
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'matrix-secret-key')

database_url = os.getenv('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///juegos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# Modelo de la base de datos
class Juego(db.Model):
    __tablename__ = 'juegos'
    no_serie = db.Column(db.String, primary_key=True)
    nombre = db.Column(db.String)
    genero = db.Column(db.String)
    pg = db.Column(db.String)
    anio_salida = db.Column(db.Integer)
    imagen = db.Column(db.String)

    def to_dict(self):
        return {
            'no_serie': self.no_serie,
            'nombre': self.nombre,
            'genero': self.genero,
            'pg': self.pg,
            'anio_salida': self.anio_salida,
            'imagen': self.imagen,
        }

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    edad = db.Column(db.Integer, nullable=False)
    correo = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

def guardar_imagen(archivo_imagen):
    if not archivo_imagen or not archivo_imagen.filename:
        return None

    nombre_seguro = secure_filename(archivo_imagen.filename)
    if not nombre_seguro:
        return None

    nombre_unico = f"{uuid.uuid4().hex}_{nombre_seguro}"
    ruta_destino = os.path.join(app.config['UPLOAD_FOLDER'], nombre_unico)
    archivo_imagen.save(ruta_destino)
    return nombre_unico

def eliminar_imagen(nombre_archivo):
    if not nombre_archivo:
        return

    ruta_archivo = os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo)
    if os.path.exists(ruta_archivo):
        os.remove(ruta_archivo)

def current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return Usuario.query.get(user_id)

with app.app_context():
    db.create_all()

# Ruta raiz
@app.route('/')
def home():
    ahora = datetime.now()
    return render_template('home.html', usuario=current_user(), ahora=ahora)

@app.route('/catalogo')
def catalogo():
    juegos = Juego.query.all()
    generos = sorted(set(j.genero for j in juegos if j.genero), key=str.lower)
    return render_template('index.html', juegos=juegos, todos_generos=generos, genero_filtro=None, usuario=current_user())

# Ruta /juegos crear un nuevo juego
@app.route('/juegos/new', methods=['GET','POST'])
def create_juego():
    if request.method == 'POST':
        no_serie = request.form['no_serie']
        nombre = request.form['nombre']
        genero = request.form['genero']
        pg = request.form['pg']
        anio_salida = int(request.form['anio_salida'])
        imagen = guardar_imagen(request.files.get('imagen'))

        nuevo_juego = Juego(no_serie=no_serie, nombre=nombre, genero=genero, pg=pg, anio_salida=anio_salida, imagen=imagen)

        db.session.add(nuevo_juego)
        db.session.commit()

        return redirect(url_for('catalogo'))
    
    return render_template('create_juegos.html', usuario=current_user())

# Eliminar juego
@app.route('/juegos/delete/<string:no_serie>')
def delete_juego(no_serie):
    juego = Juego.query.get(no_serie)
    if juego:
        eliminar_imagen(juego.imagen)
        db.session.delete(juego)
        db.session.commit()
    return redirect(url_for('catalogo'))

# Actualizar juego
@app.route('/juegos/update/<string:no_serie>', methods=['GET','POST'])
def update_juego(no_serie):
    juego = Juego.query.get(no_serie)
    if not juego:
        return redirect(url_for('catalogo'))

    if request.method == 'POST':
        juego.nombre = request.form['nombre']
        juego.genero = request.form['genero']
        juego.pg = request.form['pg']
        juego.anio_salida = int(request.form['anio_salida'])

        nueva_imagen = guardar_imagen(request.files.get('imagen'))
        if nueva_imagen:
            eliminar_imagen(juego.imagen)
            juego.imagen = nueva_imagen

        db.session.commit()
        return redirect(url_for('catalogo'))
    return render_template('update_juegos.html', juego=juego, usuario=current_user())

# Ruta /juegos
@app.route('/juegos')
def getJuegos():
    return 'Aqui van los juegos'

# Ruta para filtrar por género
@app.route('/genero/<string:genero>')
def por_genero(genero):
    juegos = Juego.query.filter_by(genero=genero).all()
    generos = sorted(set(j.genero for j in Juego.query.all() if j.genero), key=str.lower)
    return render_template('index.html', juegos=juegos, genero_filtro=genero, todos_generos=generos, usuario=current_user())

@app.route('/usuarios/registro', methods=['GET', 'POST'])
def registro_usuarios():
    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        edad = int(request.form['edad'])
        correo = request.form['correo'].strip().lower()
        contrasena = request.form['contrasena']

        usuario_existente = Usuario.query.filter_by(correo=correo).first()
        if usuario_existente:
            flash('Ese correo ya está registrado.', 'danger')
            return redirect(url_for('registro_usuarios'))

        nuevo_usuario = Usuario(nombre=nombre, edad=edad, correo=correo)
        nuevo_usuario.set_password(contrasena)
        db.session.add(nuevo_usuario)
        db.session.commit()
        flash('Usuario registrado correctamente. Ahora inicia sesión.', 'success')
        return redirect(url_for('inicio_sesion'))

    return render_template('registro_usuarios.html', usuario=current_user())

@app.route('/usuarios/login', methods=['GET', 'POST'])
def inicio_sesion():
    if request.method == 'POST':
        correo = request.form['correo'].strip().lower()
        contrasena = request.form['contrasena']

        usuario = Usuario.query.filter_by(correo=correo).first()
        if not usuario or not usuario.check_password(contrasena):
            flash('Correo o contraseña incorrectos.', 'danger')
            return redirect(url_for('inicio_sesion'))

        session['user_id'] = usuario.id
        session['user_name'] = usuario.nombre
        flash(f'Bienvenido, {usuario.nombre}.', 'success')
        return redirect(url_for('catalogo'))

    return render_template('login.html', usuario=current_user())

@app.route('/usuarios/logout')
def cerrar_sesion():
    session.pop('user_id', None)
    session.pop('user_name', None)
    flash('Sesión cerrada.', 'success')
    return redirect(url_for('catalogo'))

# MODIFICACIÓN FINAL PARA PRODUCCIÓN/DOCKER
if __name__ == '__main__':
    # Usamos host='0.0.0.0' para que sea accesible desde fuera del contenedor
    app.run(host='0.0.0.0', port=5000, debug=True)
