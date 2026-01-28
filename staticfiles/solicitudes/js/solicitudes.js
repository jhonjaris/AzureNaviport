/* NaviPort RD - JavaScript específico para Solicitudes */

// === VARIABLES GLOBALES === //
let personalData = [];
let vehiculosData = [];

// === FUNCIONES DE FORMATEO === //
function formatCedula(input) {
    // Remover todo lo que no sea número
    let value = input.value.replace(/\D/g, '');
    
    // Limitar a 11 dígitos máximo
    if (value.length > 11) {
        value = value.substring(0, 11);
    }
    
    // Aplicar formato XXX-XXXXXXX-X
    let formatted = '';
    if (value.length > 0) {
        if (value.length <= 3) {
            formatted = value;
        } else if (value.length <= 10) {
            formatted = value.substring(0, 3) + '-' + value.substring(3);
        } else {
            formatted = value.substring(0, 3) + '-' + value.substring(3, 10) + '-' + value.substring(10);
        }
    }
    
    // Actualizar el valor del input
    input.value = formatted;
}

function formatTelefono(input) {
    // Remover todo lo que no sea número
    let value = input.value.replace(/\D/g, '');
    
    // Limitar a 10 dígitos máximo
    if (value.length > 10) {
        value = value.substring(0, 10);
    }
    
    // Aplicar formato XXX-XXX-XXXX
    let formatted = '';
    if (value.length > 0) {
        if (value.length <= 3) {
            formatted = value;
        } else if (value.length <= 6) {
            formatted = value.substring(0, 3) + '-' + value.substring(3);
        } else {
            formatted = value.substring(0, 3) + '-' + value.substring(3, 6) + '-' + value.substring(6);
        }
    }
    
    // Actualizar el valor del input
    input.value = formatted;
}

function formatRNC(input) {
    // Remover todo lo que no sea número
    let value = input.value.replace(/\D/g, '');
    
    // Limitar a 9 dígitos máximo
    if (value.length > 9) {
        value = value.substring(0, 9);
    }
    
    // Aplicar formato XXX-XXXXX-X
    let formatted = '';
    if (value.length > 0) {
        if (value.length <= 3) {
            formatted = value;
        } else if (value.length <= 8) {
            formatted = value.substring(0, 3) + '-' + value.substring(3);
        } else {
            formatted = value.substring(0, 3) + '-' + value.substring(3, 8) + '-' + value.substring(8);
        }
    }
    
    // Actualizar el valor del input
    input.value = formatted;
}

function getCleanValue(formattedValue, type) {
    // Función helper para obtener valor limpio sin guiones
    if (type === 'cedula' || type === 'telefono' || type === 'rnc') {
        return formattedValue.replace(/\D/g, '');
    }
    return formattedValue;
}

// === FUNCIONES DE VALIDACIÓN === //
function setupDateValidation() {
    // Obtener la fecha actual en formato YYYY-MM-DD
    const today = new Date();
    const todayString = today.toISOString().split('T')[0];
    
    console.log('Configurando validación de fechas. Fecha mínima:', todayString);
    
    // Buscar campos de fecha por diferentes selectores posibles
    const fechaIngresoSelectors = [
        'input[name="fecha_ingreso"]',
        '#id_fecha_ingreso',
        'input[type="date"][name*="fecha_ingreso"]',
        'input[type="date"][id*="fecha_ingreso"]'
    ];
    
    const fechaSalidaSelectors = [
        'input[name="fecha_salida"]', 
        '#id_fecha_salida',
        'input[type="date"][name*="fecha_salida"]',
        'input[type="date"][id*="fecha_salida"]'
    ];
    
    let fechaIngresoInput = null;
    let fechaSalidaInput = null;
    
    // Buscar campo de fecha de ingreso
    for (const selector of fechaIngresoSelectors) {
        fechaIngresoInput = document.querySelector(selector);
        if (fechaIngresoInput) {
            console.log('Campo fecha ingreso encontrado con selector:', selector);
            break;
        }
    }
    
    // Buscar campo de fecha de salida
    for (const selector of fechaSalidaSelectors) {
        fechaSalidaInput = document.querySelector(selector);
        if (fechaSalidaInput) {
            console.log('Campo fecha salida encontrado con selector:', selector);
            break;
        }
    }
    
    // Configurar fecha de ingreso
    if (fechaIngresoInput) {
        fechaIngresoInput.setAttribute('min', todayString);
        fechaIngresoInput.addEventListener('change', function() {
            validateFechaIngreso(this, todayString);
        });
        console.log('✅ Validación configurada para fecha de ingreso');
    } else {
        console.warn('⚠️ No se encontró el campo fecha_ingreso');
    }
    
    // Configurar fecha de salida
    if (fechaSalidaInput) {
        fechaSalidaInput.setAttribute('min', todayString);
        fechaSalidaInput.addEventListener('change', function() {
            validateFechaSalida(this, fechaIngresoInput);
        });
        console.log('✅ Validación configurada para fecha de salida');
    } else {
        console.warn('⚠️ No se encontró el campo fecha_salida');
    }
    
    // Si encontramos ambos campos, configurar validación cruzada
    if (fechaIngresoInput && fechaSalidaInput) {
        fechaIngresoInput.addEventListener('change', function() {
            if (fechaSalidaInput.value && fechaSalidaInput.value < this.value) {
                fechaSalidaInput.value = '';
                alert('La fecha de salida debe ser posterior a la fecha de ingreso');
            }
            fechaSalidaInput.setAttribute('min', this.value);
        });
    }
}

function validateFechaIngreso(input, todayString) {
    const selectedDate = input.value;
    
    if (selectedDate < todayString) {
        input.value = '';
        alert('La fecha de ingreso no puede ser anterior a hoy');
        input.focus();
        return false;
    }
    
    console.log('✅ Fecha de ingreso válida:', selectedDate);
    return true;
}

function validateFechaSalida(input, fechaIngresoInput) {
    const selectedDate = input.value;
    const today = new Date().toISOString().split('T')[0];
    
    // Validar que no sea anterior a hoy
    if (selectedDate < today) {
        input.value = '';
        alert('La fecha de salida no puede ser anterior a hoy');
        input.focus();
        return false;
    }
    
    // Validar que no sea anterior a la fecha de ingreso
    if (fechaIngresoInput && fechaIngresoInput.value && selectedDate < fechaIngresoInput.value) {
        input.value = '';
        alert('La fecha de salida debe ser posterior a la fecha de ingreso');
        input.focus();
        return false;
    }
    
    console.log('✅ Fecha de salida válida:', selectedDate);
    return true;
}

// === FUNCIONES DE GESTIÓN DE PERSONAL === //
function abrirModalPersonal() {
    document.getElementById('modalAgregarPersonalLabel').textContent = '➕ Agregar Personal';
    document.getElementById('formPersonal').reset();
    delete document.getElementById('formPersonal').dataset.editIndex;
    
    // Limpiar campos de búsqueda
    document.getElementById('modalResultadosBusqueda').innerHTML = '';
    document.getElementById('modalBuscarPersonal').value = '';
    
    const modal = new bootstrap.Modal(document.getElementById('modalAgregarPersonal'));
    modal.show();
}

function buscarPersonalModal() {
    const query = document.getElementById('modalBuscarPersonal').value.trim();
    const resultsContainer = document.getElementById('modalResultadosBusqueda');
    
    if (query.length < 3) {
        resultsContainer.innerHTML = '<div class="alert alert-info">Escriba al menos 3 caracteres para buscar</div>';
        return;
    }
    
    // Simular búsqueda (aquí iría una llamada AJAX real)
    resultsContainer.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin"></i> Buscando...</div>';
    
    // Simulación de resultados después de 1 segundo
    setTimeout(() => {
        resultsContainer.innerHTML = `
            <div class="alert alert-warning">
                No se encontraron resultados para "${query}". 
                Complete el formulario para registrar una nueva persona.
            </div>
        `;
    }, 1000);
}

function seleccionarPersonal(personalData) {
    document.getElementById('personalId').value = personalData.id;
    document.getElementById('personalNombre').value = personalData.nombre;
    document.getElementById('personalCedula').value = personalData.cedula;
    document.getElementById('personalCargo').value = personalData.cargo || '';
    document.getElementById('personalLicencia').value = personalData.licencia_conducir || '';
    document.getElementById('personalTelefono').value = personalData.telefono || '';
    
    // Deshabilitar campos editables para personal existente
    document.getElementById('personalNombre').readOnly = true;
    document.getElementById('personalCedula').readOnly = true;
    
    // Limpiar resultados
    document.getElementById('modalResultadosBusqueda').innerHTML = '';
    document.getElementById('modalBuscarPersonal').value = '';
}

function limpiarFormularioPersonal() {
    document.getElementById('formPersonal').reset();
    
    // Habilitar todos los campos
    document.getElementById('personalNombre').readOnly = false;
    document.getElementById('personalCedula').readOnly = false;
    
    // Limpiar resultados de búsqueda
    document.getElementById('modalResultadosBusqueda').innerHTML = '';
    document.getElementById('modalBuscarPersonal').value = '';
}

function guardarPersonal() {
    const form = document.getElementById('formPersonal');
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    const personalId = document.getElementById('personalId').value;
    const nombre = document.getElementById('personalNombre').value.trim();
    const cedula = document.getElementById('personalCedula').value.trim();
    
    // Verificar si ya existe en la tabla (solo si no estamos editando)
    const editIndex = form.dataset.editIndex;
    const cedulaLimpia = getCleanValue(cedula, 'cedula');
    if (editIndex === undefined && personalData.find(p => getCleanValue(p.cedula, 'cedula') === cedulaLimpia)) {
        alert('Ya existe una persona con esta cédula');
        return;
    }
    
    const persona = {
        id: personalId || null,
        nombre: nombre,
        cedula: cedula,  // Ya viene formateado del input
        cargo: document.getElementById('personalCargo').value.trim(),
        licencia_conducir: document.getElementById('personalLicencia').value.trim(),
        telefono: document.getElementById('personalTelefono').value.trim(),  // Ya viene formateado del input
        rol_operacion: document.getElementById('personalRolOperacion').value.trim()
    };
    
    if (editIndex !== undefined) {
        // Editando persona existente
        personalData[parseInt(editIndex)] = persona;
        delete form.dataset.editIndex;
    } else {
        // Agregando nueva persona
        personalData.push(persona);
    }
    
    updatePersonalTable();
    
    // Cerrar modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('modalAgregarPersonal'));
    modal.hide();
}

function updatePersonalTable() {
    const tbody = document.getElementById('tablaPersonalBody');
    
    if (personalData.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-muted">
                    No hay personal asignado. Haga clic en "Agregar Personal" para comenzar.
                </td>
            </tr>
        `;
    } else {
        tbody.innerHTML = personalData.map((persona, index) => `
            <tr>
                <td><strong>${persona.nombre}</strong></td>
                <td>${persona.cedula}</td>
                <td>${persona.cargo || '<span class="text-muted">No especificado</span>'}</td>
                <td>${persona.licencia_conducir || '<span class="text-muted">No especificado</span>'}</td>
                <td>
                    <button class="btn-action btn-docs" onclick="abrirModalDocumentosPersonal(${index}, '${persona.nombre}')" title="Gestionar Documentos">
                        📄
                    </button>
                </td>
                <td class="btn-actions">
                    <button class="btn-action btn-edit" onclick="editarPersonal(${index})" title="Editar">✏️</button>
                    <button class="btn-action btn-delete" onclick="abrirModalEliminar('personal', ${index}, '${persona.nombre}')" title="Eliminar">🗑️</button>
                </td>
            </tr>
        `).join('');
    }
    
    updateHiddenFields();
}

function editarPersonal(index) {
    const persona = personalData[index];
    
    document.getElementById('modalAgregarPersonalLabel').textContent = '✏️ Editar Personal';
    document.getElementById('formPersonal').dataset.editIndex = index;
    
    document.getElementById('personalId').value = persona.id || '';
    document.getElementById('personalNombre').value = persona.nombre;
    
    // Aplicar formateo a cédula y teléfono
    const cedulaInput = document.getElementById('personalCedula');
    const telefonoInput = document.getElementById('personalTelefono');
    
    cedulaInput.value = persona.cedula;
    formatCedula(cedulaInput);
    
    telefonoInput.value = persona.telefono || '';
    if (telefonoInput.value) {
        formatTelefono(telefonoInput);
    }
    
    document.getElementById('personalCargo').value = persona.cargo || '';
    document.getElementById('personalLicencia').value = persona.licencia_conducir || '';
    document.getElementById('personalRolOperacion').value = persona.rol_operacion || '';
    
    // Habilitar todos los campos para edición
    document.getElementById('personalNombre').readOnly = false;
    document.getElementById('personalCedula').readOnly = false;
    document.getElementById('personalCargo').readOnly = false;
    document.getElementById('personalLicencia').readOnly = false;
    document.getElementById('personalTelefono').readOnly = false;
    
    const modal = new bootstrap.Modal(document.getElementById('modalAgregarPersonal'));
    modal.show();
}

function eliminarPersonal(index) {
    if (index < 0 || index >= personalData.length) {
        alert('Error: Índice inválido');
        return;
    }
    
    const persona = personalData[index];
    const mensaje = `¿Está seguro de quitar a ${persona.nombre} de la lista?`;
    
    if (confirm(mensaje)) {
        personalData.splice(index, 1);
        updatePersonalTable();
    }
}

// === FUNCIONES DE GESTIÓN DE VEHÍCULOS === //
function abrirModalVehiculo() {
    document.getElementById('modalAgregarVehiculoLabel').textContent = '🚗 Agregar Vehículo';
    document.getElementById('formVehiculo').reset();
    delete document.getElementById('formVehiculo').dataset.editIndex;
    
    const modal = new bootstrap.Modal(document.getElementById('modalAgregarVehiculo'));
    modal.show();
}

function guardarVehiculo() {
    const form = document.getElementById('formVehiculo');
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    const placa = document.getElementById('vehiculoPlaca').value.trim().toUpperCase();
    
    // Verificar si ya existe en la tabla (solo si no estamos editando)
    const editIndex = form.dataset.editIndex;
    if (editIndex === undefined && vehiculosData.find(v => v.placa.toUpperCase() === placa)) {
        alert('Ya existe un vehículo con esta placa');
        return;
    }
    
    const vehiculo = {
        placa: placa,
        tipo: document.getElementById('vehiculoTipo').value,
        conductor: document.getElementById('vehiculoConductor').value.trim(),
        licencia: document.getElementById('vehiculoLicencia').value.trim(),
    };
    
    if (editIndex !== undefined) {
        // Editando vehículo existente
        vehiculosData[parseInt(editIndex)] = vehiculo;
        delete form.dataset.editIndex;
    } else {
        // Agregando nuevo vehículo
        vehiculosData.push(vehiculo);
    }
    
    updateVehiculosTable();
    
    // Cerrar modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('modalAgregarVehiculo'));
    modal.hide();
}

function updateVehiculosTable() {
    const tbody = document.getElementById('tablaVehiculosBody');
    
    if (vehiculosData.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-muted">
                    No hay vehículos registrados. Haga clic en "Agregar Vehículo" para comenzar.
                </td>
            </tr>
        `;
    } else {
        tbody.innerHTML = vehiculosData.map((vehiculo, index) => `
            <tr>
                <td><strong>${vehiculo.placa}</strong></td>
                <td>${vehiculo.tipo}</td>
                <td>${vehiculo.conductor || '<span class="text-muted">No asignado</span>'}</td>
                <td>${vehiculo.licencia || '<span class="text-muted">No especificada</span>'}</td>
                <td>
                    <button class="btn-action btn-docs" onclick="abrirModalDocumentosVehiculo(${index}, '${vehiculo.placa}')" title="Gestionar Documentos">
                        📄
                    </button>
                </td>
                <td class="btn-actions">
                    <button class="btn-action btn-edit" onclick="editarVehiculo(${index})" title="Editar">✏️</button>
                    <button class="btn-action btn-delete" onclick="abrirModalEliminar('vehiculo', ${index}, '${vehiculo.placa}')" title="Eliminar">🗑️</button>
                </td>
            </tr>
        `).join('');
    }
    
    updateVehiculosHiddenFields();
}

function editarVehiculo(index) {
    const vehiculo = vehiculosData[index];
    
    document.getElementById('modalAgregarVehiculoLabel').textContent = '✏️ Editar Vehículo';
    document.getElementById('formVehiculo').dataset.editIndex = index;
    
    document.getElementById('vehiculoPlaca').value = vehiculo.placa;
    document.getElementById('vehiculoTipo').value = vehiculo.tipo;
    document.getElementById('vehiculoConductor').value = vehiculo.conductor || '';
    document.getElementById('vehiculoLicencia').value = vehiculo.licencia || '';
    
    const modal = new bootstrap.Modal(document.getElementById('modalAgregarVehiculo'));
    modal.show();
}

// === MODAL UNIFICADO DE ELIMINACIÓN === //
function abrirModalEliminar(tipo, index, nombre, extra) {
    const modal = document.getElementById('modalEliminar');
    const titulo = document.getElementById('modalEliminarLabel');
    const mensaje = document.getElementById('mensajeEliminar');
    const btnSimple = document.getElementById('btnEliminarSimple');
    const btnPermanente = document.getElementById('btnEliminarPermanente');
    
    // Configurar título
    if (tipo === 'personal') {
        titulo.textContent = `Eliminar Personal: ${nombre}`;
        mensaje.innerHTML = `
            <p>¿Cómo desea eliminar a <strong>${nombre}</strong>?</p>
            <ul class="text-muted" style="font-size: 14px;">
                <li><strong>De la lista:</strong> Solo se remueve de esta solicitud</li>
                <li><strong>Permanente:</strong> Se elimina completamente del sistema</li>
            </ul>
        `;
    } else if (tipo === 'vehiculo') {
        titulo.textContent = `Eliminar Vehículo: ${nombre}`;
        mensaje.innerHTML = `
            <p>¿Cómo desea eliminar el vehículo <strong>${nombre}</strong>?</p>
            <ul class="text-muted" style="font-size: 14px;">
                <li><strong>De la lista:</strong> Solo se remueve de esta solicitud</li>
                <li><strong>Permanente:</strong> Se elimina completamente del sistema</li>
            </ul>
        `;
    }
    
    // Configurar botones
    btnSimple.onclick = function() {
        if (tipo === 'personal') {
            eliminarPersonal(index);
        } else if (tipo === 'vehiculo') {
            eliminarVehiculo(index);
        }
        bootstrap.Modal.getInstance(modal).hide();
    };
    
    btnPermanente.onclick = function() {
        const confirmText = document.getElementById('confirmacionEliminar').value.toLowerCase();
        if (confirmText === 'eliminar') {
            if (tipo === 'personal') {
                eliminarPersonal(index);
            } else if (tipo === 'vehiculo') {
                eliminarVehiculo(index);
            }
            bootstrap.Modal.getInstance(modal).hide();
            document.getElementById('confirmacionEliminar').value = '';
        } else {
            alert('Debe escribir "eliminar" para confirmar la eliminación permanente');
        }
    };
    
    // Mostrar modal
    new bootstrap.Modal(modal).show();
}

function eliminarVehiculo(index) {
    if (index < 0 || index >= vehiculosData.length) {
        alert('Error: Índice inválido');
        return;
    }
    
    const vehiculo = vehiculosData[index];
    vehiculosData.splice(index, 1);
    updateVehiculosTable();
}

// === FUNCIONES DE DOCUMENTOS === //
function abrirModalDocumentosPersonal(index, nombre) {
    document.getElementById('nombrePersonalDocs').textContent = nombre;
    // Aquí iría la lógica para cargar/gestionar documentos del personal
    const modal = new bootstrap.Modal(document.getElementById('modalDocumentosPersonal'));
    modal.show();
}

function abrirModalDocumentosVehiculo(index, placa) {
    document.getElementById('nombreVehiculoDocs').textContent = placa;
    // Aquí iría la lógica para cargar/gestionar documentos del vehículo
    const modal = new bootstrap.Modal(document.getElementById('modalDocumentosVehiculo'));
    modal.show();
}

// === FUNCIONES DE CAMPOS OCULTOS === //
function updateHiddenFields() {
    const container = document.getElementById('personalHiddenFields');
    if (!container) return;
    
    container.innerHTML = '';
    
    personalData.forEach((persona, index) => {
        const fields = [
            { name: `personal-${index}-id`, value: persona.id || '' },
            { name: `personal-${index}-nombre`, value: persona.nombre },
            { name: `personal-${index}-cedula`, value: getCleanValue(persona.cedula, 'cedula') },
            { name: `personal-${index}-cargo`, value: persona.cargo || '' },
            { name: `personal-${index}-licencia`, value: persona.licencia_conducir || '' },
            { name: `personal-${index}-telefono`, value: getCleanValue(persona.telefono, 'telefono') },
            { name: `personal-${index}-rol_operacion`, value: persona.rol_operacion || '' }
        ];
        
        fields.forEach(field => {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = field.name;
            input.value = field.value;
            container.appendChild(input);
        });
    });
}

function updateVehiculosHiddenFields() {
    const container = document.getElementById('vehiculosHiddenFields');
    if (!container) return;
    
    container.innerHTML = '';
    
    vehiculosData.forEach((vehiculo, index) => {
        const fields = [
            { name: `vehiculos-${index}-placa`, value: vehiculo.placa },
            { name: `vehiculos-${index}-tipo_vehiculo`, value: vehiculo.tipo },
            { name: `vehiculos-${index}-conductor`, value: vehiculo.conductor || '' },
            { name: `vehiculos-${index}-licencia_conducir`, value: vehiculo.licencia || '' }
        ];
        
        fields.forEach(field => {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = field.name;
            input.value = field.value;
            container.appendChild(input);
        });
    });
}

// === INICIALIZACIÓN === //
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Inicializando funciones de solicitudes...');
    
    // Configurar formateo automático para todos los inputs
    document.querySelectorAll('input[id*="cedula"], input[id*="Cedula"]').forEach(input => {
        input.addEventListener('input', function() {
            formatCedula(this);
        });
        input.classList.add('input-formateado', 'input-cedula');
    });
    
    document.querySelectorAll('input[id*="telefono"], input[id*="Telefono"]').forEach(input => {
        input.addEventListener('input', function() {
            formatTelefono(this);
        });
        input.classList.add('input-formateado', 'input-telefono');
    });
    
    document.querySelectorAll('input[id*="rnc"], input[id*="RNC"]').forEach(input => {
        input.addEventListener('input', function() {
            formatRNC(this);
        });
        input.classList.add('input-formateado');
    });
    
    // Configurar validación de fechas
    setupDateValidation();
    
    // Inicializar tablas
    updatePersonalTable();
    updateVehiculosTable();
    
    // Configurar eventos de modales
    const btnBuscarPersonal = document.getElementById('modalBtnBuscarPersonal');
    if (btnBuscarPersonal) {
        btnBuscarPersonal.addEventListener('click', buscarPersonalModal);
    }
    
    const btnGuardarPersonal = document.getElementById('btnGuardarPersonal');
    if (btnGuardarPersonal) {
        btnGuardarPersonal.addEventListener('click', guardarPersonal);
    }
    
    const btnGuardarVehiculo = document.getElementById('btnGuardarVehiculo');
    if (btnGuardarVehiculo) {
        btnGuardarVehiculo.addEventListener('click', guardarVehiculo);
    }
    
    const btnLimpiarPersonal = document.getElementById('btnLimpiarPersonal');
    if (btnLimpiarPersonal) {
        btnLimpiarPersonal.addEventListener('click', limpiarFormularioPersonal);
    }
    
    console.log('✅ Funciones de solicitudes inicializadas');
    console.log('📋 Personal array:', personalData);
    console.log('🚗 Vehículos array:', vehiculosData);
});

// === EXPOSICIÓN GLOBAL === //
window.SolicitudesJS = {
    formatCedula,
    formatTelefono,
    formatRNC,
    getCleanValue,
    setupDateValidation,
    abrirModalPersonal,
    guardarPersonal,
    editarPersonal,
    eliminarPersonal,
    abrirModalVehiculo,
    guardarVehiculo,
    editarVehiculo,
    eliminarVehiculo,
    abrirModalEliminar,
    updatePersonalTable,
    updateVehiculosTable,
    personalData,
    vehiculosData
};