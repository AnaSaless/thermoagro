const hamBtn = document.querySelector('.toggle-btn');
if (hamBtn) {
    hamBtn.addEventListener('click', () => {
        document.getElementById('sidebar')?.classList.toggle('expand');
    });
}

const socket = io();

const sensorMap = { temperature: 'temp', humidity: 'hum', silo: 'silo' };
const unitMap = { temp: ' °C', hum: ' %', silo: '' };

socket.on('sensor_update', ({ sensor, value, color }) => {
    const key = sensorMap[sensor];
    if (!key) return;

    const valueEl = document.getElementById(`${key}-value`);
    if (valueEl)
        valueEl.textContent = value.toFixed(2) + (unitMap[key] || '');

    const cardEl = document.getElementById(`card-${key}`);
    if (cardEl)
        cardEl.className = cardEl.className.replace(/bg-\w+/, `bg-${color}`);

    const statusEl = document.getElementById(`${key}-status-text`);
    if (statusEl) {
        let text = 'Desconhecido';
        if (color === 'green') {
            text = 'Não há nada com o que se preocupar!';
        } else if (color === 'yellow') {
            text = key === 'temp' ? 'Atenção: variação de temperatura detectada!'
                : key === 'hum' ? 'Atenção: variação de umidade detectada!'
                    : 'Atenção: alteração no silo detectada!';
        } else if (color === 'red') {
            text = key === 'temp' ? 'ALERTA! Temperatura crítica!'
                : key === 'hum' ? 'ALERTA! Umidade crítica!'
                    : 'ALERTA! Silo crítico!';
        }
        statusEl.textContent = text;
    }

    const tbody = document.querySelector('#histTable tbody');
  if (tbody) {
    const now = new Date().toLocaleString();
    const tr  = document.createElement('tr');
    tr.innerHTML =
      `<td>${now}</td>
       <td>${value.toFixed(2)}${unitMap[key]||''}</td>
       <td><span class="badge bg-${color}">${color}</span></td>`;
    tbody.prepend(tr);
  }
});

const post = url => fetch(url, { method: 'POST', credentials: 'include' });
document.getElementById('btn-open')?.addEventListener('click', () => post('/actuator/servo/open'));
document.getElementById('btn-close')?.addEventListener('click', () => post('/actuator/servo/close'));

const input = document.getElementById('searchInput');
const clear = document.getElementById('clearSearch');
if (input) {
    input.oninput = () => {
        const q = input.value.toLowerCase();
        document.querySelectorAll('#histTable tbody tr').forEach(tr => {
            tr.style.display = tr.innerText.toLowerCase().includes(q) ? '' : 'none';
        });
    };
    clear?.addEventListener('click', () => { input.value = ''; input.oninput(); });
}
