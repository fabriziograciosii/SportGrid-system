from flask import Flask, jsonify, render_template
import sqlite3
from datetime import datetime, timedelta # <--- NUEVO: Herramientas matemáticas para el tiempo

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('sistema_reservas.db')
    conn.row_factory = sqlite3.Row 
    return conn

@app.route('/')
def inicio():
    return render_template('index.html')

@app.route('/api/canchas', methods=['GET'])
def obtener_canchas():
    conn = get_db_connection()
    canchas_db = conn.execute('SELECT * FROM Instalaciones').fetchall()
    conn.close()
    
    lista_canchas = [dict(cancha) for cancha in canchas_db]
    return jsonify(lista_canchas)

# ==========================================
# NUEVO ENDPOINT: Generador de grilla de turnos
# ==========================================
# ==========================================
# ENDPOINT ACTUALIZADO: Grilla dinámica por cancha
# ==========================================
@app.route('/api/horarios/<int:id_instalacion>', methods=['GET'])
def obtener_horarios(id_instalacion):
    # 1. Vamos a la base de datos a preguntar por esta cancha en particular
    conn = get_db_connection()
    cancha = conn.execute('SELECT * FROM Instalaciones WHERE id_instalacion = ?', (id_instalacion,)).fetchone()
    conn.close()

    if not cancha:
        return jsonify({'error': 'Cancha no encontrada'}), 404

    # 2. Definimos la duración del turno según el deporte y el club
    id_deporte = cancha['id_deporte']
    
    # Lógica de negocio dinámica:
    if id_deporte == 2:
        # Si es Fútbol 5 (ID 2), siempre 60 minutos
        minutos_turno = 60
    else:
        # Si es Pádel (ID 1), depende del club.
        # Idealmente esto se lee de otra columna en la DB (ej: 'duracion_minutos'), 
        # pero por ahora hacemos una regla: Cancha 3 dura 60m, el resto 90m.
        if id_instalacion == 3:
            minutos_turno = 60
        else:
            minutos_turno = 90

    # 3. Matemática de horarios
    hora_inicio = datetime.strptime('09:00', '%H:%M')
    hora_cierre = datetime.strptime('02:00', '%H:%M') + timedelta(days=1)
    duracion_turno = timedelta(minutes=minutos_turno)
    
    turnos = []
    hora_actual = hora_inicio
    
    while hora_actual + duracion_turno <= hora_cierre:
        turnos.append(hora_actual.strftime('%H:%M'))
        hora_actual += duracion_turno
        
    return jsonify(turnos)
    
    # Mientras el turno termine antes de la hora de cierre, lo agregamos a la lista
    while hora_actual + duracion_turno <= hora_cierre:
        # Guardamos solo la hora y minuto en texto (ej: "09:00")
        turnos.append(hora_actual.strftime('%H:%M'))
        # Avanzamos 90 minutos para el próximo ciclo
        hora_actual += duracion_turno
        
    return jsonify(turnos)

if __name__ == '__main__':
    print("Iniciando el servidor de reservas...")
    app.run(debug=True, port=5000)