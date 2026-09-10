import sqlite3

def cargar_datos_prueba():
    conexion = sqlite3.connect('sistema_reservas.db')
    cursor = conexion.cursor()

    # 1. Usuario Administrador
    cursor.execute('''
    INSERT OR IGNORE INTO Usuarios (id_usuario, nombre_completo, email, telefono, rol)
    VALUES (1, 'Admin General', 'admin@club.com', '3624000000', 'Admin_Club')
    ''')

    # 2. Club de prueba
    cursor.execute('''
    INSERT OR IGNORE INTO Clubes (id_club, id_admin, nombre_club, ciudad, direccion, hora_apertura, hora_cierre)
    VALUES (1, 1, 'Punto Norte', 'Resistencia', 'Ruta Nicolas Avellaneda km 13.4', '09:00', '02:00')
    ''')

    # 3. Deportes (Pádel a 90 min y Fútbol a 60 min)
    cursor.execute('''
    INSERT OR IGNORE INTO Deportes (id_deporte, nombre_deporte, duracion_turno_minutos)
    VALUES 
        (1, 'Pádel', 90),
        (2, 'Fútbol 5', 60)
    ''')

    # 4. Instalaciones (Canchas de Pádel)
    cursor.execute('''
    INSERT OR IGNORE INTO Instalaciones (id_instalacion, id_club, id_deporte, nombre_interno, caracteristicas)
    VALUES 
        (1, 1, 1, 'Cancha 1', 'Blindex y sintético | Cubierta'),
        (2, 1, 1, 'Cancha 2', 'Muro y sintético | Iluminación LED'),
        (3, 1, 1, 'Cancha 3', 'Blindex y sintético | Descubierta')
    ''')

    conexion.commit()
    conexion.close()
    print("¡Datos de prueba cargados exitosamente!")

if __name__ == '__main__':
    cargar_datos_prueba()