import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'sistema_reservas.db')

def cargar_datos_prueba():
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()

    # 1. Usuarios Administradores
    cursor.execute('''
    INSERT OR IGNORE INTO Usuarios (id_usuario, nombre_completo, email, telefono, rol)
    VALUES 
        (1, 'Admin General', 'admin@club.com', '3624000000', 'Admin_Club'),
        (2, 'Admin Costa Padel', 'costa@club.com', '3794112233', 'Admin_Club'),
        (3, 'Admin Arena', 'arena@club.com', '3624556677', 'Admin_Club')
    ''')

    # 2. Clubes adheridos en varias ciudades (Corrientes, Resistencia, Córdoba, Rosario, Buenos Aires)
    cursor.execute('''
    INSERT OR IGNORE INTO Clubes (id_club, id_admin, nombre_club, ciudad, direccion, hora_apertura, hora_cierre)
    VALUES 
        (1, 1, 'Punto Norte Sport Complex', 'Resistencia', 'Ruta Nicolas Avellaneda km 13.4', '08:00', '00:00'),
        (2, 2, 'Costa Pádel & Fútbol Club', 'Corrientes', 'Av. Costanera Sur y Necochea', '08:00', '00:00'),
        (3, 3, 'Arena Multideportes', 'Resistencia', 'Av. Sarmiento 1850', '08:00', '00:00'),
        (4, 1, 'Parque Norte Deportivo', 'Buenos Aires', 'Av. Cantilo y Guiraldes', '08:00', '00:00'),
        (5, 2, 'Córdoba Athletic Padel & Hockey', 'Córdoba', 'Av. Richieri 2880', '08:00', '00:00'),
        (6, 3, 'Rosario Tenis & Squash Center', 'Rosario', 'Bv. Oroño 1400', '08:00', '00:00')
    ''')

    # 3. Catálogo Amplio de Deportes solicitados por el usuario
    deportes = [
        (1, 'Pádel', 90),
        (2, 'Fútbol 5', 60),
        (3, 'Fútbol 6', 60),
        (4, 'Fútbol 7', 60),
        (5, 'Fútbol 8', 60),
        (6, 'Fútbol 9', 60),
        (7, 'Fútbol 11', 90),
        (8, 'Tenis', 90),
        (9, 'Básquet 3x3', 60),
        (10, 'Básquet 5x5', 60),
        (11, 'Squash', 60),
        (12, 'Natación', 60),
        (13, 'Hockey', 90),
        (14, 'Rugby', 90)
    ]

    for id_dep, nom_dep, duracion in deportes:
        cursor.execute('''
        INSERT OR REPLACE INTO Deportes (id_deporte, nombre_deporte, duracion_turno_minutos)
        VALUES (?, ?, ?)
        ''', (id_dep, nom_dep, duracion))

    # 4. Instalaciones variadas
    instalaciones = [
        (1, 1, 1, 'Cancha 1 Pádel (Cristal)', 'Blindex panorámico y césped sintético azul | Techada'),
        (2, 1, 1, 'Cancha 2 Pádel (Muro)', 'Muro tradicional y césped sintético | Iluminación LED'),
        (3, 1, 9, 'Cancha Básquet 3x3 Urbana', 'Piso de parquet flotante profesional | Tableros de cristal'),
        (4, 2, 1, 'Pista Central Costa Pádel', 'Pista oficial WPT panorámica | Climatizada'),
        (5, 2, 2, 'Cancha Fútbol 5 Sintético', 'Césped sintético 50mm con caucho | Iluminación LED'),
        (6, 2, 8, 'Cancha 1 Tenis (Polvo de ladrillo)', 'Polvo de ladrillo oficial con riego automático'),
        (7, 3, 10, 'Microestadio Básquet 5x5', 'Estadio techado con gradas para 200 personas'),
        (8, 3, 4, 'Cancha Fútbol 7 Césped Natural', 'Césped bermuda con iluminación nocturna HD'),
        (9, 3, 12, 'Piscina Semi-Olímpica 25m', 'Natación 6 andariveles climatizada | Guardavidas'),
        (10, 4, 7, 'Cancha Fútbol 11 Profesional', 'Medidas reglamentarias AFA | Vestuarios de primera'),
        (11, 5, 13, 'Cancha Sintética de Hockey', 'Césped sintético de agua profesional'),
        (12, 6, 11, 'Cancha Squash 1 Vidrio', 'Cancha reglamentaria con frontón de cristal')
    ]

    for id_inst, id_club, id_dep, nom_int, carac in instalaciones:
        cursor.execute('''
        INSERT OR REPLACE INTO Instalaciones (id_instalacion, id_club, id_deporte, nombre_interno, caracteristicas)
        VALUES (?, ?, ?, ?, ?)
        ''', (id_inst, id_club, id_dep, nom_int, carac))

    conexion.commit()
    conexion.close()
    print("¡Catálogo ampliado de deportes e instalaciones actualizado!")

if __name__ == '__main__':
    cargar_datos_prueba()
