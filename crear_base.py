import sqlite3

def inicializar_base_datos():
    # Esto crea un archivo llamado 'sistema_reservas.db' en tu carpeta
    conexion = sqlite3.connect('sistema_reservas.db')
    cursor = conexion.cursor()

    # 1. Tabla Usuarios (Dueños y Jugadores)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Usuarios (
        id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_completo TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        telefono TEXT,
        rol TEXT NOT NULL -- Puede ser 'Jugador' o 'Admin_Club'
    )
    ''')

    # 2. Tabla Clubes
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Clubes (
        id_club INTEGER PRIMARY KEY AUTOINCREMENT,
        id_admin INTEGER,
        nombre_club TEXT NOT NULL,
        ciudad TEXT NOT NULL,
        direccion TEXT,
        hora_apertura TEXT NOT NULL,
        hora_cierre TEXT NOT NULL,
        FOREIGN KEY (id_admin) REFERENCES Usuarios(id_usuario)
    )
    ''')

    # 3. Tabla Deportes (El catálogo que lo hace escalable)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Deportes (
        id_deporte INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_deporte TEXT UNIQUE NOT NULL,
        duracion_turno_minutos INTEGER NOT NULL
    )
    ''')

    # 4. Tabla Instalaciones (Las canchas físicas de cada club)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Instalaciones (
        id_instalacion INTEGER PRIMARY KEY AUTOINCREMENT,
        id_club INTEGER,
        id_deporte INTEGER,
        nombre_interno TEXT NOT NULL, -- Ej: "Cancha 1 (Vidrio)"
        caracteristicas TEXT,
        FOREIGN KEY (id_club) REFERENCES Clubes(id_club),
        FOREIGN KEY (id_deporte) REFERENCES Deportes(id_deporte)
    )
    ''')

    # 5. Tabla Reservas (El corazón transaccional del sistema)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Reservas (
        id_reserva INTEGER PRIMARY KEY AUTOINCREMENT,
        id_usuario INTEGER,
        id_instalacion INTEGER,
        fecha TEXT NOT NULL,      -- Formato YYYY-MM-DD
        hora_inicio TEXT NOT NULL, -- Formato HH:MM
        hora_fin TEXT NOT NULL,    -- Formato HH:MM
        estado TEXT NOT NULL,      -- 'Confirmada', 'Pendiente', 'Cancelada'
        FOREIGN KEY (id_usuario) REFERENCES Usuarios(id_usuario),
        FOREIGN KEY (id_instalacion) REFERENCES Instalaciones(id_instalacion)
    )
    ''')

    conexion.commit()
    conexion.close()
    print("¡Base de datos y tablas creadas con éxito!")

# Ejecutamos la función
if __name__ == '__main__':
    inicializar_base_datos()