/**
 * Timeline interactivo para visualización de eventos de solicitudes
 * NaviPort RD - Sistema de Control de Acceso Portuario
 */

class SolicitudTimeline {
    constructor(containerId, eventos) {
        this.container = document.getElementById(containerId);
        this.eventos = eventos;
        this.filtroActivo = 'todos';

        if (!this.container) {
            console.error(`Timeline container '${containerId}' not found`);
            return;
        }

        this.init();
    }

    init() {
        this.renderTimeline();
        this.attachEventListeners();
    }

    renderTimeline() {
        if (!this.eventos || this.eventos.length === 0) {
            this.renderEmpty();
            return;
        }

        const filtrados = this.filtrarEventos();

        let html = `
            <div class="timeline-controls">
                <div class="timeline-filters">
                    <button class="filter-btn ${this.filtroActivo === 'todos' ? 'active' : ''}" data-filter="todos">
                        📋 Todos (${this.eventos.length})
                    </button>
                    <button class="filter-btn ${this.filtroActivo === 'importantes' ? 'active' : ''}" data-filter="importantes">
                        ⭐ Importantes
                    </button>
                    <button class="filter-btn ${this.filtroActivo === 'publicos' ? 'active' : ''}" data-filter="publicos">
                        👁️ Públicos
                    </button>
                    <button class="filter-btn ${this.filtroActivo === 'internos' ? 'active' : ''}" data-filter="internos">
                        🔒 Internos
                    </button>
                </div>
            </div>

            <div class="timeline-wrapper">
        `;

        // Agrupar eventos por fecha
        const eventosPorFecha = this.agruparPorFecha(filtrados);

        for (const [fecha, eventosDelDia] of Object.entries(eventosPorFecha)) {
            html += `
                <div class="timeline-date-group">
                    <div class="timeline-date-header">
                        <span class="timeline-date-label">${this.formatearFechaGrupo(fecha)}</span>
                        <span class="timeline-date-count">${eventosDelDia.length} evento${eventosDelDia.length !== 1 ? 's' : ''}</span>
                    </div>
                    <div class="timeline-events">
            `;

            eventosDelDia.forEach((evento, index) => {
                html += this.renderEvento(evento, index === eventosDelDia.length - 1);
            });

            html += `
                    </div>
                </div>
            `;
        }

        html += `</div>`;

        this.container.innerHTML = html;
    }

    renderEvento(evento, esUltimo) {
        const color = evento.color || '#95a5a6';
        const icono = evento.icono || '📌';
        const tiempo = this.formatearTiempo(evento.creado_el);
        const usuario = evento.usuario_nombre || 'Sistema Automático';

        const claseVisibilidad = evento.es_interno ? 'interno' : (evento.es_visible_solicitante ? 'publico' : 'staff');

        return `
            <div class="timeline-item ${claseVisibilidad}" data-tipo="${evento.tipo_evento}">
                <div class="timeline-marker" style="background: ${color};">
                    <span class="timeline-icon">${icono}</span>
                </div>
                ${!esUltimo ? '<div class="timeline-line"></div>' : ''}
                <div class="timeline-content">
                    <div class="timeline-header">
                        <div class="timeline-title-row">
                            <h4 class="timeline-title">${evento.titulo}</h4>
                            <span class="timeline-time">${tiempo}</span>
                        </div>
                        <div class="timeline-meta">
                            <span class="timeline-user">
                                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                                    <circle cx="12" cy="7" r="4"></circle>
                                </svg>
                                ${usuario}
                            </span>
                            ${this.renderBadgeVisibilidad(evento)}
                        </div>
                    </div>
                    ${evento.descripcion ? `
                        <div class="timeline-description">
                            ${evento.descripcion}
                        </div>
                    ` : ''}
                    ${evento.metadata && Object.keys(evento.metadata).length > 0 ? `
                        <div class="timeline-metadata">
                            ${this.renderMetadata(evento.metadata)}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    renderBadgeVisibilidad(evento) {
        if (evento.es_interno) {
            return '<span class="badge badge-interno">🔒 Interno</span>';
        } else if (evento.es_visible_solicitante) {
            return '<span class="badge badge-publico">👁️ Público</span>';
        } else {
            return '<span class="badge badge-staff">👁️‍🗨️ Staff</span>';
        }
    }

    renderMetadata(metadata) {
        let html = '<div class="metadata-grid">';

        // Filtrar y formatear metadata relevante
        const keysRelevantes = ['estado_anterior', 'estado_nuevo', 'evaluador_anterior_nombre', 'evaluador_nuevo_nombre'];

        for (const [key, value] of Object.entries(metadata)) {
            if (keysRelevantes.includes(key) && value) {
                const label = this.formatearLabelMetadata(key);
                html += `
                    <div class="metadata-item">
                        <span class="metadata-label">${label}:</span>
                        <span class="metadata-value">${value}</span>
                    </div>
                `;
            }
        }

        html += '</div>';
        return html;
    }

    renderEmpty() {
        this.container.innerHTML = `
            <div class="timeline-empty">
                <div class="empty-icon">⏰</div>
                <h3>Sin eventos registrados</h3>
                <p>No hay eventos en el historial de esta solicitud.</p>
            </div>
        `;
    }

    filtrarEventos() {
        switch (this.filtroActivo) {
            case 'importantes':
                const tiposImportantes = ['creacion', 'envio', 'asignacion', 'aprobacion', 'rechazo', 'escalacion'];
                return this.eventos.filter(e => tiposImportantes.includes(e.tipo_evento));

            case 'publicos':
                return this.eventos.filter(e => e.es_visible_solicitante);

            case 'internos':
                return this.eventos.filter(e => e.es_interno);

            case 'todos':
            default:
                return this.eventos;
        }
    }

    agruparPorFecha(eventos) {
        const grupos = {};

        eventos.forEach(evento => {
            const fecha = evento.creado_el.split('T')[0]; // YYYY-MM-DD
            if (!grupos[fecha]) {
                grupos[fecha] = [];
            }
            grupos[fecha].push(evento);
        });

        // Ordenar fechas descendente (más reciente primero)
        const gruposOrdenados = {};
        Object.keys(grupos).sort().reverse().forEach(fecha => {
            gruposOrdenados[fecha] = grupos[fecha];
        });

        return gruposOrdenados;
    }

    formatearFechaGrupo(fechaStr) {
        const fecha = new Date(fechaStr + 'T00:00:00');
        const hoy = new Date();
        const ayer = new Date(hoy);
        ayer.setDate(ayer.getDate() - 1);

        // Normalizar fechas para comparación (sin hora)
        const fechaNorm = new Date(fecha.getFullYear(), fecha.getMonth(), fecha.getDate());
        const hoyNorm = new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate());
        const ayerNorm = new Date(ayer.getFullYear(), ayer.getMonth(), ayer.getDate());

        if (fechaNorm.getTime() === hoyNorm.getTime()) {
            return '🔴 Hoy - ' + this.formatearFecha(fecha);
        } else if (fechaNorm.getTime() === ayerNorm.getTime()) {
            return '🟡 Ayer - ' + this.formatearFecha(fecha);
        } else {
            return '📅 ' + this.formatearFecha(fecha);
        }
    }

    formatearFecha(fecha) {
        const opciones = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        return fecha.toLocaleDateString('es-DO', opciones);
    }

    formatearTiempo(timestamp) {
        const fecha = new Date(timestamp);
        const horas = fecha.getHours().toString().padStart(2, '0');
        const minutos = fecha.getMinutes().toString().padStart(2, '0');
        return `${horas}:${minutos}`;
    }

    formatearLabelMetadata(key) {
        const labels = {
            'estado_anterior': 'Estado anterior',
            'estado_nuevo': 'Estado nuevo',
            'evaluador_anterior_nombre': 'Evaluador anterior',
            'evaluador_nuevo_nombre': 'Nuevo evaluador',
            'prioridad_anterior': 'Prioridad anterior',
            'prioridad_nueva': 'Nueva prioridad'
        };
        return labels[key] || key;
    }

    attachEventListeners() {
        // Event listener para filtros
        this.container.addEventListener('click', (e) => {
            if (e.target.classList.contains('filter-btn')) {
                const filtro = e.target.dataset.filter;
                this.filtroActivo = filtro;
                this.renderTimeline();
            }
        });
    }

    // Método público para actualizar eventos
    actualizarEventos(nuevosEventos) {
        this.eventos = nuevosEventos;
        this.renderTimeline();
    }

    // Método público para cambiar filtro programáticamente
    setFiltro(filtro) {
        this.filtroActivo = filtro;
        this.renderTimeline();
    }
}

// Exportar para uso global
window.SolicitudTimeline = SolicitudTimeline;
