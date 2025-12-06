document.addEventListener('DOMContentLoaded', () => {
    // URL base del API de FastAPI
    const API_URL = 'http://127.0.0.1:8000/api/citas/'; 

    const form = document.getElementById('cita-form');
    const tableBody = document.querySelector('#citas-table tbody');
    const messageDisplay = document.getElementById('mensaje-form');
    
    // Función para manejar datos nulos/vacíos y asegurar la alineación
    const getCellContent = (data) => {
        // Usa data.toString().trim() === '' para detectar cadenas vacías
        if (data === null || data === undefined || (typeof data === 'string' && data.trim() === '')) {
            return '-'; // Devuelve un guion para celdas vacías
        }
        return data;
    };

    // -----------------------------------------------------
    // A. READ (Obtener y Mostrar todas las citas)
    // -----------------------------------------------------
    async function fetchCitas() {
        try {
            const response = await fetch(API_URL);
            const citas = await response.json();
            renderCitas(citas);
        } catch (error) {
            console.error('Error al obtener citas:', error);
            // Mensaje de error si la API no responde
            tableBody.innerHTML = '<tr><td colspan="6">❌ Error al cargar las citas de la API. Asegúrese de que el servidor FastAPI está corriendo.</td></tr>';
        }
    }

function renderCitas(citas) {
        tableBody.innerHTML = ''; // Limpiar tabla antes de redibujar
        if (citas.length === 0) {
            // Colspan debe reducirse a 5 porque quitamos la columna ID
            tableBody.innerHTML = '<tr><td colspan="5">No hay citas programadas.</td></tr>';
            return;
        }

        citas.forEach(cita => {
            const row = tableBody.insertRow();
            
            // Obtenemos el ID, pero NO lo insertamos en la fila
            const id = getCellContent(cita.CITA_ID || cita.cita_id);
            
            // 1. PACIENTE
            row.insertCell().textContent = getCellContent(cita.PACIENTE_NOMBRE || cita.paciente_nombre);
            
            // 2. FECHA/HORA
            row.insertCell().textContent = getCellContent(cita.FECHA_CITA || cita.fecha_cita); 
            
            // 3. MOTIVO
            row.insertCell().textContent = getCellContent(cita.MOTIVO || cita.motivo);
            
            // 4. ESTADO
            const estadoText = cita.ESTADO || cita.estado || 'Programada';
            const estadoCell = row.insertCell();
            estadoCell.innerHTML = `<span class="estado-${estadoText}">${estadoText}</span>`;
            
            // 5. ACCIONES (Botones)
            const accionesCell = row.insertCell();

            const citaIdToUse = cita.CITA_ID || cita.cita_id;
            const id_valido = typeof citaIdToUse === 'number' && citaIdToUse > 0;
            
            if (id_valido) {
                const completeBtn = document.createElement('button');
                completeBtn.textContent = 'Completar';
                completeBtn.className = 'btn-secondary btn-completar'; 
                completeBtn.onclick = () => updateCita(citaIdToUse, 'Completada');
                accionesCell.appendChild(completeBtn);

                const deleteBtn = document.createElement('button');
                deleteBtn.textContent = 'Eliminar';
                deleteBtn.className = 'btn-secondary btn-eliminar';     
                deleteBtn.onclick = () => deleteCita(citaIdToUse);
                accionesCell.appendChild(deleteBtn);
            } else {
                accionesCell.textContent = 'ID nulo';
                accionesCell.style.color = '#e74c3c';
            }
        });
    }
    // --- Resto de las funciones (CREATE, UPDATE, DELETE) ---

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        // Recolección de datos del formulario para el POST
        const data = {
            paciente_nombre: document.getElementById('paciente_nombre').value,
            // Envío de la fecha/hora en formato string ISO para que Pydantic la valide
            fecha_cita: document.getElementById('fecha_cita').value, 
            motivo: document.getElementById('motivo').value
        };
        
        try {
            const response = await fetch(API_URL, {
                method: 'POST', // Operación CREATE en el API
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                form.reset();
                messageDisplay.textContent = '✅ Cita creada con éxito.';
                fetchCitas(); // Recargar la tabla
            } else {
                const errorData = await response.json();
                messageDisplay.textContent = `❌ Error al crear cita: ${errorData.detail || 'Fallo de servidor'}`;
            }
        } catch (error) {
            console.error('Error de red:', error);
            messageDisplay.textContent = '❌ Error de conexión al servidor.';
        }
    });

    async function updateCita(id, newStatus) {
        if (!confirm(`¿Estás seguro de cambiar el estado de la cita ${id} a ${newStatus}?`)) return;

        try {
            const response = await fetch(`${API_URL}${id}`, {
                method: 'PUT', // Operación UPDATE en el API
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ estado: newStatus })
            });

            if (response.ok) {
                alert(`Estado de la cita ${id} actualizado a ${newStatus}.`);
                fetchCitas(); 
            } else {
                alert('Error al actualizar la cita.');
            }
        } catch (error) {
            console.error('Error de red:', error);
            alert('Error de conexión al servidor.');
        }
    }

    async function deleteCita(id) {
        if (!confirm(`¿Estás seguro de eliminar la cita con ID ${id}?`)) return;

        try {
            const response = await fetch(`${API_URL}${id}`, {
                method: 'DELETE' // Operación DELETE en el API
            });

            if (response.ok) {
                alert(`Cita ${id} eliminada con éxito.`);
                fetchCitas(); 
            } else {
                alert('Error al eliminar la cita.');
            }
        } catch (error) {
            console.error('Error de red:', error);
            alert('Error de conexión al servidor.');
        }
    }

    // Inicio de la aplicación: Carga las citas al cargar la página
    fetchCitas();
});