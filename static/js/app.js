/**
 * SPORTGRID - LÓGICA FRONTEND E INTERACTIVIDAD
 * 
 * Este archivo maneja la interacción del usuario:
 * 1. Selector horizontal de fechas estilo ATC Sports.
 * 2. Carga y renderizado de canchas desde la API.
 * 3. Filtros de búsqueda (Deporte, Ciudad, Fecha).
 * 4. Despliegue de turnos disponibles y ocupados.
 * 5. Modal de reserva con formulario y pantalla de éxito.
 */

// Estado global de la aplicación en el navegador
const AppState = {
    canchas: [],           // Lista completa de canchas obtenidas de la base de datos
    canchasFiltradas: [],  // Canchas que cumplen los filtros actuales
    horariosPorCancha: {}, // Caché temporal de turnos por ID de cancha
    reservaEnCurso: null   // Datos del turno que el usuario está reservando
};

// =========================================================
// 1. INICIALIZACIÓN
// =========================================================
document.addEventListener('DOMContentLoaded', () => {
    inicializarFiltroFecha();
    inicializarCarruselDias();
    vincularEventosFiltros();
    vincularEventosModal();
    cargarCanchas();
});

/**
 * Configura el campo de fecha con el día de hoy por defecto
 * y restringe para que no se puedan elegir fechas pasadas.
 */
function inicializarFiltroFecha() {
    const inputFecha = document.getElementById('filtro-fecha');
    if (!inputFecha) return;

    const hoy = new Date();
    const año = hoy.getFullYear();
    const mes = String(hoy.getMonth() + 1).padStart(2, '0');
    const dia = String(hoy.getDate()).padStart(2, '0');
    const fechaHoy = `${año}-${mes}-${dia}`;

    inputFecha.min = fechaHoy;
    inputFecha.value = fechaHoy;
}

/**
 * Genera el carrusel horizontal de fechas estilo ATC Sports
 * (HOY, MAÑANA y próximos días con un toque)
 */
function inicializarCarruselDias() {
    const contenedor = document.getElementById('carrusel-dias');
    if (!contenedor) return;

    contenedor.innerHTML = '';
    const hoy = new Date();
    const diasSemana = ['DOM', 'LUN', 'MAR', 'MIÉ', 'JUE', 'VIE', 'SÁB'];
    const meses = ['ENE', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC'];

    for (let i = 0; i < 7; i++) {
        const fecha = new Date();
        fecha.setDate(hoy.getDate() + i);

        const año = fecha.getFullYear();
        const mesIso = String(fecha.getMonth() + 1).padStart(2, '0');
        const diaIso = String(fecha.getDate()).padStart(2, '0');
        const fechaIso = `${año}-${mesIso}-${diaIso}`;

        const nombreDia = i === 0 ? 'HOY' : diasSemana[fecha.getDay()];
        const numeroDia = `${fecha.getDate()} ${meses[fecha.getMonth()]}`;

        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = `btn-dia ${i === 0 ? 'activo' : ''}`;
        btn.dataset.fecha = fechaIso;
        btn.innerHTML = `
            <span class="dia-nombre">${nombreDia}</span>
            <span class="dia-numero">${numeroDia}</span>
        `;

        btn.onclick = () => {
            document.querySelectorAll('.btn-dia').forEach(b => b.classList.remove('activo'));
            btn.classList.add('activo');

            // Sincronizar el input de fecha del buscador
            const inputFecha = document.getElementById('filtro-fecha');
            if (inputFecha) inputFecha.value = fechaIso;

            // Recargar horarios de las tarjetas que estén desplegadas
            document.querySelectorAll('.btn-toggle-horarios.activo').forEach(boton => {
                boton.click(); // Cerrar
                setTimeout(() => boton.click(), 150); // Reabrir con fecha actualizada
            });
        };

        contenedor.appendChild(btn);
    }
}

// =========================================================
// 2. OBTENER Y RENDERIZAR CANCHAS
// =========================================================
/**
 * Llama a la API de Flask para traer las canchas de la base de datos
 */
async function cargarCanchas() {
    const contenedor = document.getElementById('contenedor-canchas');
    contenedor.innerHTML = `
        <div class="empty-state">
            <p>Cargando disponibilidad de canchas...</p>
        </div>
    `;

    try {
        const respuesta = await fetch('/api/canchas');
        if (!respuesta.ok) throw new Error('Error al conectar con el servidor');
        
        const data = await respuesta.json();
        AppState.canchas = data;
        AppState.canchasFiltradas = [...data];

        renderizarCanchas(AppState.canchasFiltradas);
    } catch (error) {
        console.error('Error al cargar canchas:', error);
        contenedor.innerHTML = `
            <div class="empty-state">
                <h3>Hubo un problema al cargar las canchas</h3>
                <p>Verifica que el servidor de Flask esté ejecutándose en http://localhost:5001</p>
            </div>
        `;
    }
}

/**
 * Dibuja las tarjetas de canchas en el DOM
 */
function renderizarCanchas(lista) {
    const contenedor = document.getElementById('contenedor-canchas');
    const contador = document.getElementById('contador-canchas');
    
    if (contador) {
        contador.innerText = `${lista.length} ${lista.length === 1 ? 'cancha encontrada' : 'canchas encontradas'}`;
    }

    if (lista.length === 0) {
        contenedor.innerHTML = `
            <div class="empty-state">
                <h3>No se encontraron canchas</h3>
                <p>Intenta cambiar los filtros de deporte o ciudad para ver más opciones.</p>
            </div>
        `;
        return;
    }

    contenedor.innerHTML = '';

    lista.forEach(cancha => {
        // Determinamos el nombre del deporte y tipo según el id_deporte
        const esPadel = cancha.id_deporte === 1;
        const nombreDeporte = esPadel ? 'Pádel' : 'Fútbol 5';
        
        // Extraemos si es cubierta o descubierta de las características
        const esCubierta = (cancha.caracteristicas || '').toLowerCase().includes('cubierta');
        const tipoInstalacion = esCubierta ? 'Cubierta' : 'Descubierta';

        const tarjeta = document.createElement('div');
        tarjeta.className = 'cancha-card';
        tarjeta.id = `card-cancha-${cancha.id_instalacion}`;
        
        tarjeta.innerHTML = `
            <div class="cancha-card-header">
                <span class="badge-deporte">${nombreDeporte}</span>
                <span class="badge-tipo">${tipoInstalacion}</span>
            </div>
            
            <h3 class="cancha-titulo">${cancha.nombre_interno}</h3>
            <div class="cancha-club">📍 Club Punto Norte · Resistencia</div>
            <p class="cancha-desc">${cancha.caracteristicas || 'Instalación deportiva con iluminación y césped sintético de primera calidad.'}</p>
            
            <button class="btn-toggle-horarios" onclick="toggleHorarios(${cancha.id_instalacion}, '${cancha.nombre_interno}', '${nombreDeporte}')">
                <span>Ver Horarios Disponibles</span>
                <span id="icono-toggle-${cancha.id_instalacion}">▼</span>
            </button>
            
            <!-- Contenedor desplegable de turnos -->
            <div id="wrapper-horarios-${cancha.id_instalacion}" class="horarios-wrapper" style="display: none;">
                <div class="horarios-titulo">
                    <span>Turnos disponibles</span>
                    <span style="font-size: 0.75rem; color: var(--text-muted);">Selecciona uno para reservar</span>
                </div>
                <div id="horarios-${cancha.id_instalacion}" class="horarios-container">
                    <span style="font-size: 13px; color: gray;">Consultando grilla...</span>
                </div>
            </div>
        `;

        contenedor.appendChild(tarjeta);
    });
}

// =========================================================
// 3. HORARIOS Y TURNOS
// =========================================================
/**
 * Abre o cierra la botonera de turnos tipo acordeón
 */
async function toggleHorarios(idCancha, nombreCancha, deporte) {
    const wrapper = document.getElementById(`wrapper-horarios-${idCancha}`);
    const icono = document.getElementById(`icono-toggle-${idCancha}`);
    const boton = wrapper.previousElementSibling;

    // Si ya está visible, lo cerramos
    if (wrapper.style.display === 'block') {
        wrapper.style.display = 'none';
        icono.innerText = '▼';
        boton.classList.remove('activo');
        return;
    }

    // Si está cerrado, lo abrimos y cargamos los turnos
    wrapper.style.display = 'block';
    icono.innerText = '▲';
    boton.classList.add('activo');

    const contenedorTurnos = document.getElementById(`horarios-${idCancha}`);
    contenedorTurnos.innerHTML = '<span style="font-size: 13px; color: gray;">Calculando turnos disponibles...</span>';

    try {
        const respuesta = await fetch(`/api/horarios/${idCancha}`);
        if (!respuesta.ok) throw new Error('No se pudieron obtener los horarios');
        
        const turnos = await respuesta.json();
        contenedorTurnos.innerHTML = '';

        if (turnos.length === 0) {
            contenedorTurnos.innerHTML = '<span style="font-size: 13px; color: gray;">No hay turnos disponibles para este día.</span>';
            return;
        }

        // Simulamos algunos turnos ocupados (ej. horarios pico como 19:30 o 21:00)
        // para que en el diseño frontend se aprecie la diferencia visual entre turnos libres y ocupados
        const horariosSimuladosOcupados = ['19:30', '21:00', '20:00'];

        turnos.forEach(hora => {
            const btnTurno = document.createElement('button');
            btnTurno.type = 'button';
            btnTurno.innerText = hora;
            
            const estaOcupado = horariosSimuladosOcupados.includes(hora) && idCancha === 1;

            if (estaOcupado) {
                btnTurno.className = 'btn-turno ocupado';
                btnTurno.disabled = true;
                btnTurno.title = 'Horario no disponible';
            } else {
                btnTurno.className = 'btn-turno disponible';
                btnTurno.title = `Reservar turno a las ${hora}`;
                btnTurno.onclick = () => seleccionarTurnoParaReserva(idCancha, nombreCancha, deporte, hora, btnTurno);
            }

            contenedorTurnos.appendChild(btnTurno);
        });

    } catch (error) {
        console.error('Error al cargar horarios:', error);
        contenedorTurnos.innerHTML = '<span style="color: #ef4444; font-size: 13px;">Error al cargar los horarios.</span>';
    }
}

// =========================================================
// 4. MODAL DE CONFIRMACIÓN DE RESERVA
// =========================================================
/**
 * Guarda los datos del turno clickeado y abre el modal
 */
function seleccionarTurnoParaReserva(idCancha, nombreCancha, deporte, hora, botonElemento) {
    // Desmarcar otros botones seleccionados previamente
    document.querySelectorAll('.btn-turno.seleccionado').forEach(b => b.classList.remove('seleccionado'));
    botonElemento.classList.add('seleccionado');

    const inputFecha = document.getElementById('filtro-fecha');
    const fechaSeleccionada = inputFecha ? inputFecha.value : new Date().toISOString().split('T')[0];

    // Duración estimada según deporte
    const duracion = deporte === 'Fútbol 5' ? '60 minutos' : '90 minutos';

    AppState.reservaEnCurso = {
        idCancha,
        nombreCancha,
        deporte,
        hora,
        fecha: fechaSeleccionada,
        duracion,
        botonTurno: botonElemento
    };

    abrirModal();
}

function abrirModal() {
    const data = AppState.reservaEnCurso;
    if (!data) return;

    // Llenar los datos del resumen en el modal
    document.getElementById('modal-resumen-cancha').innerText = data.nombreCancha;
    document.getElementById('modal-resumen-deporte').innerText = data.deporte;
    document.getElementById('modal-resumen-fecha').innerText = formatearFecha(data.fecha);
    document.getElementById('modal-resumen-hora').innerText = `${data.hora} hs (${data.duracion})`;

    // Asegurar que se vea el formulario y no la pantalla de éxito previa
    document.getElementById('modal-vista-formulario').style.display = 'block';
    document.getElementById('modal-vista-exito').style.display = 'none';

    // Abrir modal con clase CSS
    const overlay = document.getElementById('modal-reserva');
    overlay.classList.add('abierto');
    document.body.style.overflow = 'hidden'; // Evitar scroll del fondo

    // Foco en el primer campo
    setTimeout(() => {
        const inputNombre = document.getElementById('reserva-nombre');
        if (inputNombre) inputNombre.focus();
    }, 150);
}

function cerrarModal() {
    const overlay = document.getElementById('modal-reserva');
    overlay.classList.remove('abierto');
    document.body.style.overflow = ''; // Restaurar scroll

    // Desmarcar selección si no confirmó
    if (AppState.reservaEnCurso && AppState.reservaEnCurso.botonTurno) {
        AppState.reservaEnCurso.botonTurno.classList.remove('seleccionado');
    }

    // Limpiar formulario
    const form = document.getElementById('form-reserva');
    if (form) form.reset();
}

/**
 * Vincula el cierre por backdrop y tecla ESC
 */
function vincularEventosModal() {
    const overlay = document.getElementById('modal-reserva');
    const btnCerrar = document.getElementById('btn-cerrar-modal');
    const btnCancelar = document.getElementById('btn-cancelar-modal');
    const form = document.getElementById('form-reserva');

    if (btnCerrar) btnCerrar.onclick = cerrarModal;
    if (btnCancelar) btnCancelar.onclick = cerrarModal;

    // Cerrar al hacer clic en el fondo oscuro
    if (overlay) {
        overlay.onclick = (e) => {
            if (e.target === overlay) cerrarModal();
        };
    }

    // Cerrar con tecla Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && overlay.classList.contains('abierto')) {
            cerrarModal();
        }
    });

    // Envío del formulario de reserva
    if (form) {
        form.onsubmit = ejecutarConfirmacionReserva;
    }
}

/**
 * Simula la confirmación y muestra el ticket de éxito en el modal
 */
function ejecutarConfirmacionReserva(e) {
    e.preventDefault();

    const btnSubmit = document.getElementById('btn-confirmar-reserva');
    const nombre = document.getElementById('reserva-nombre').value.trim();
    const telefono = document.getElementById('reserva-telefono').value.trim();
    const email = document.getElementById('reserva-email').value.trim();

    if (!nombre || !telefono) {
        alert('Por favor completa al menos tu nombre y un teléfono de contacto.');
        return;
    }

    // Estado de carga en el botón
    btnSubmit.disabled = true;
    btnSubmit.innerHTML = '<span>Confirmando turno...</span>';

    // Simulamos una respuesta del servidor (500ms)
    setTimeout(() => {
        btnSubmit.disabled = false;
        btnSubmit.innerHTML = '<span>Confirmar Reserva</span>';

        const data = AppState.reservaEnCurso;
        const codigoReserva = 'SG-' + Math.floor(1000 + Math.random() * 9000);

        // Actualizar datos del ticket de éxito
        document.getElementById('ticket-codigo').innerText = codigoReserva;
        document.getElementById('ticket-cancha').innerText = `${data.nombreCancha} (${data.deporte})`;
        document.getElementById('ticket-horario').innerText = `${formatearFecha(data.fecha)} a las ${data.hora} hs`;
        document.getElementById('ticket-titular').innerText = nombre;

        // Ocultar formulario y mostrar pantalla de éxito
        document.getElementById('modal-vista-formulario').style.display = 'none';
        document.getElementById('modal-vista-exito').style.display = 'block';

        // Marcar el turno como ocupado en la interfaz para dar feedback visual
        if (data.botonTurno) {
            data.botonTurno.classList.remove('disponible', 'seleccionado');
            data.botonTurno.classList.add('ocupado');
            data.botonTurno.disabled = true;
            data.botonTurno.title = 'Turno reservado recientemente';
        }
    }, 600);
}

// =========================================================
// 5. FILTROS DE BÚSQUEDA
// =========================================================
function vincularEventosFiltros() {
    const btnBuscar = document.querySelector('.btn-buscar');
    const selectDeporte = document.getElementById('filtro-deporte');
    const selectCiudad = document.getElementById('filtro-ciudad');

    if (btnBuscar) {
        btnBuscar.onclick = aplicarFiltros;
    }

    // Filtro instantáneo al cambiar selectores
    if (selectDeporte) selectDeporte.onchange = aplicarFiltros;
    if (selectCiudad) selectCiudad.onchange = aplicarFiltros;
}

function aplicarFiltros() {
    const deporteVal = document.getElementById('filtro-deporte').value;
    
    // Filtramos en memoria las canchas según el deporte seleccionado
    AppState.canchasFiltradas = AppState.canchas.filter(cancha => {
        if (deporteVal === 'todos') return true;
        return String(cancha.id_deporte) === String(deporteVal);
    });

    renderizarCanchas(AppState.canchasFiltradas);
}

// =========================================================
// 6. UTILIDADES
// =========================================================
function formatearFecha(fechaIso) {
    if (!fechaIso) return '';
    const partes = fechaIso.split('-');
    if (partes.length !== 3) return fechaIso;
    
    // Creamos fecha local para evitar desfasajes horarios
    const fecha = new Date(partes[0], partes[1] - 1, partes[2]);
    const opciones = { weekday: 'long', day: 'numeric', month: 'long' };
    const formateada = fecha.toLocaleDateString('es-AR', opciones);
    
    // Capitalizar primera letra
    return formateada.charAt(0).toUpperCase() + formateada.slice(1);
}
