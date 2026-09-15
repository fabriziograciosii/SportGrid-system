# SPORTGRID · Red y Sistema de Gestión Deportiva de Argentina

Plataforma integral que conecta a jugadores con complejos deportivos y brinda a los dueños de clubes un sistema de gestión operativa para canchas, señas automatizadas con Mercado Pago, cantina/kiosco POS, matchmaking ("¿Falta Uno?"), abonos mensuales y comunicación directa por WhatsApp.

---

## 🚀 Módulos del Sistema

### 1. Portal Público / Marketplace (`/`)
* **Buscador Multideporte**: Búsqueda por Ciudad (con sugerencias y autocompletado en toda Argentina), Deporte, Fecha, Horario y Duración (60, 90 o 120 min).
* **Filtros Neutros y Bajo Demanda**: La grilla de clubes se despliega únicamente al presionar "Buscar".
* **Geolocalización "Cerca de mí"**: Detección de coordenadas GPS y cálculo de distancia física en kilómetros (fórmula de Haversine).
* **Barra de Filtros Secundarios con Multi-Selección**: Popovers flotantes con checkboxes para seleccionar múltiples servicios (Cantina, Vestuarios, LED, WiFi, Estacionamiento), superficies (Cristal, Sintético, Polvo, Cemento) y cerramiento (Techada / Aire libre).
* **Módulo "¿Falta Uno? / Partidos Abiertos" (Matchmaking)**: Feed en vivo de partidos incompletos en la ciudad del usuario con nivel de juego y botón para sumarse con un clic.

### 2. Detalle de Club y Reserva de Turnos (`/club/<id>`)
* **Matriz Horaria Interactiva (8:00 a 00:00 hs)**: Grilla por cancha y deporte con estados en tiempo real (Libre / Ocupado).
* **Señas con Mercado Pago**: Checkout Pro para congelar turnos abonando el 50% con código de operación `#MP-XXXXXXXX`.
* **Split Payment ("Dividir entre 4")**: Enlace directo para compartir el gasto del turno con el grupo de amigos.
* **Integración con "¿Falta Uno?"**: Opción dentro del modal de reserva para publicar el turno como partido abierto si faltan jugadores.
* **Calificaciones y Reseñas**: Sistema de 1 a 5 estrellas y opiniones de jugadores verificados.
* **Comprobantes y WhatsApp Directo**: Envío automático del comprobante al chat personal del jugador y al grupo de amigos.

### 3. Portal del Jugador: "Mis Reservas" (`/mis-reservas`)
* Historial de reservas confirmadas y pendientes, visible únicamente para usuarios autenticados.
* Consulta en vivo, botón de WhatsApp con el club y cancelación instantánea de turnos.

### 4. Software para Clubes (`/software`)
* Landing comercial B2B orientada a captar predios deportivos.
* Presentación de soluciones: automatización de turnos 24/7, cobro de señas y control de cantina.
* Planes, precios y calculadora de ahorro operativo.

### 5. Panel Operativo de Administración (`/admin`)
* **Pestaña 1: Agenda Diaria**: Grilla de turnos interactiva con reservas reales, bloqueo de canchas y métricas del día (turnos reservados, libres, ocupación % y señas recaudadas).
* **Pestaña 2: Cantina & Kiosco (POS)**: Punto de venta rápido para tercer tiempo (bebidas, cervezas, pizzas, pelotas, alquiler de paletas), comanda en vivo, control de stock y cobro en efectivo o QR.
* **Pestaña 3: Abonos Fijos Mensuales**: Gestión de turnos recurrentes semanales (ej: todos los jueves a las 20:00 hs) con control de cuota mensual ("Al día" / "Pendiente").
* **Pestaña 4: Arqueo de Caja Diario**: Balance financiero consolidado (Señas MP + Cobros en complejo + Ventas de Cantina en efectivo y MP).
* **Exportación de Reportes a CSV / Excel**: Descarga de planilla de turnos y señas en un clic.
* **Automatización de WhatsApp**: Envío de recordatorios, datos de pago/alias y cancelaciones cordiales.
* **Configuración del Complejo**: Modal para actualizar datos comerciales, horarios, comodidades y Alias de Mercado Pago.

---

## 🛠️ Endpoints API REST

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/api/clubes` | Lista de clubes con filtros opcionales de ciudad o deporte |
| `GET` | `/api/club/<id>` | Detalle completo de un club y sus instalaciones |
| `GET` | `/api/deportes` | Catálogo de deportes disponibles |
| `GET` | `/api/ciudades` | Lista de localidades adheridas en Argentina |
| `GET` | `/api/reservas` | Lista de reservas filtrables por club, fecha, cancha o usuario |
| `POST` | `/api/reservas` | Registro de nueva reserva con validación de solapamiento |
| `POST` | `/api/reservas/<id>/cancelar` | Cancelación de reserva y liberación de cancha |
| `GET/POST` | `/api/auth/login` / `/register` | Autenticación y sesión de jugadores |
| `GET/POST` | `/api/cantina/productos` | Catálogo y stock de productos de la cantina |
| `GET/POST` | `/api/cantina/ventas` | Registro de ventas del bar/kiosco y descuento de stock |
| `GET` | `/api/admin/caja` | Balance y arqueo de caja diario consolidado |
| `GET/POST` | `/api/partidos-abiertos` | Listado y publicación de partidos incompletos ("¿Falta Uno?") |
| `POST` | `/api/partidos-abiertos/<id>/unirse` | Inscripción de un jugador a un partido abierto |
| `GET/POST` | `/api/admin/abonos` | Gestión de abonos fijos semanales del complejo |
| `POST` | `/api/admin/abonos/<id>/estado-pago` | Alternar estado de pago de cuota mensual |
| `GET` | `/api/admin/reporte/reservas.csv` | Exportación de planilla de reservas a CSV |
| `POST` | `/api/mercadopago/crear-preferencia` | Generación de preferencia Checkout Pro de Mercado Pago |
| `GET/POST` | `/api/club/<id>/resenas` | Consulta y publicación de calificaciones y opiniones |
| `GET/POST` | `/api/admin/club/configuracion` | Consulta y actualización de datos operativos del club |

---

## 💻 Instalación y Ejecución Local

1. **Clonar o abrir el directorio del proyecto**:
   ```bash
   cd /Users/fabriziograciosi/Projects/SportGrid-system
   ```

2. **Crear y activar el entorno virtual**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Iniciar el servidor**:
   ```bash
   python3 app.py
   ```
   El sistema se iniciará en `http://localhost:5001/`.
