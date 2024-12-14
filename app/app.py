import json
import os
from flask import Flask, render_template, request, redirect, url_for, flash, Response
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


Base = declarative_base()
DATABASE_URL = "sqlite:///task.db"

class Task(Base):
    __tablename__ = 'task'
    id = Column(Integer, primary_key=True, autoincrement=True)
    titulo = Column(String, nullable=False)
    descripcion = Column(String, nullable=False)
    completada = Column(Boolean, default=False)

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

app = Flask(__name__)
app.secret_key = 'task_manager_12345'

@app.route('/')
def index():
    tasks = session.query(Task).all()
    data = {
        'tittle': 'Task Manager',
        'tasks': tasks
    }
    return render_template('index.html', data=data)


@app.route('/add', methods=['POST'])
def add():
    titulo = request.form['taskTitle']
    descripcion = request.form['taskDescription']
    new_task = Task(titulo=titulo, descripcion=descripcion)
    session.add(new_task)
    session.commit()
    return redirect(url_for('index'))

@app.route('/complete/<int:id>', methods=['POST']) 
def complete(id):
    task = session.query(Task).filter(Task.id == id).first()
    if task:
        task.completada = True
        session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    task = session.query(Task).filter(Task.id == id).first()  # Usa session.query para mantener consistencia
    if task:
        session.delete(task)
        session.commit()
    return redirect(url_for('index'))

@app.route('/save', methods=['POST'])
def save():
    tasks = session.query(Task).all()
    task_list = [{"id": task.id, "titulo": task.titulo, "descripcion": task.descripcion, "completada": task.completada} for task in tasks]
    # Convertir los datos en un JSON
    json_data = json.dumps(task_list, indent=4)
    
    # Crear una respuesta de descarga
    response = Response(
        json_data,
        mimetype='application/json',
        headers={
            "Content-Disposition": "attachment;filename=tasks.json"
        }
    )
    return response

@app.route('/load', methods=['POST'])
def load():
    if 'file' not in request.files:
        flash('No se encontró un archivo en la solicitud.')
        return redirect(url_for('index'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No se seleccionó un archivo.')
        return redirect(url_for('index'))
    
    if file and file.filename.endswith('.json'):
        try:
            # Leer el contenido del archivo JSON
            data = json.load(file)
            
            # Validar que sea una lista
            if not isinstance(data, list):
                flash('El archivo JSON debe contener una lista de tareas.')
                return redirect(url_for('index'))
            
            # Limpiar las tareas existentes
            session.query(Task).delete()
            session.commit()
            
            # Agregar las nuevas tareas
            for task_data in data:
                # Validar que los campos esperados existan en el JSON
                if all(key in task_data for key in ['id', 'titulo', 'descripcion', 'completada']):
                    new_task = Task(
                        id=task_data['id'],
                        titulo=task_data['titulo'],
                        descripcion=task_data['descripcion'],
                        completada=task_data['completada']
                    )
                    session.add(new_task)
                else:
                    flash('El archivo JSON contiene una tarea con datos incompletos.')
                    return redirect(url_for('index'))
            
            session.commit()
            flash('Archivo JSON cargado exitosamente.')
        except json.JSONDecodeError:
            flash('Error al leer el archivo JSON. Asegúrate de que sea válido.')
        except Exception as e:
            flash(f'Error inesperado: {str(e)}')
    else:
        flash('El archivo debe ser un JSON válido.')
    
    return redirect(url_for('index'))


if (__name__) == '__main__' :
    app.run(debug=True, port=5000)