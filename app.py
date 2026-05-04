import os
import uuid
from flask import Flask, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from werkzeug.utils import secure_filename


load_dotenv()


#crear instancia
app =  Flask(__name__)


database_url = os.getenv('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///juegos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

#Modelo de la base de datos
class Juego(db.Model):
    __tablename__ = 'juegos'
    no_serie = db.Column(db.String, primary_key=True)
    nombre = db.Column(db.String)
    genero = db.Column(db.String)
    pg = db.Column(db.String)
    anio_salida = db.Column(db.Integer)
    imagen = db.Column(db.String)

    def to_dict(self):
        return{
            'no_serie': self.no_serie,
            'nombre': self.nombre,
            'genero': self.genero,
            'pg': self.pg,
            'anio_salida': self.anio_salida,
            'imagen': self.imagen,
        }


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


with app.app_context():
    db.create_all()


#Ruta raiz
@app.route('/')
def index():
    juegos = Juego.query.all()
    generos = sorted(set(j.genero for j in juegos if j.genero), key=str.lower)
    return render_template('index.html', juegos=juegos, todos_generos=generos, genero_filtro=None)

#Ruta /juegos crear un nuevo juego
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

        return redirect(url_for('index'))
    
    #Aqui sigue si es GET
    return render_template('create_juegos.html')


#Eliminar juego
@app.route('/juegos/delete/<string:no_serie>')
def delete_juego(no_serie):
    juego = Juego.query.get(no_serie)
    if juego:
        eliminar_imagen(juego.imagen)
        db.session.delete(juego)
        db.session.commit()
    return redirect(url_for('index'))

#Actualizar juego
@app.route('/juegos/update/<string:no_serie>', methods=['GET','POST'])
def update_juego(no_serie):
    juego = Juego.query.get(no_serie)
    if not juego:
        return redirect(url_for('index'))

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
        return redirect(url_for('index'))
    return render_template('update_juegos.html', juego=juego)

#Ruta /juegos
@app.route('/juegos')
def getJuegos():
    return 'Aqui van los juegos'

#Ruta para filtrar por género
@app.route('/genero/<string:genero>')
def por_genero(genero):
    juegos = Juego.query.filter_by(genero=genero).all()
    generos = sorted(set(j.genero for j in Juego.query.all() if j.genero), key=str.lower)
    return render_template('index.html', juegos=juegos, genero_filtro=genero, todos_generos=generos)


if __name__ == '__main__':
    app.run(debug=True)