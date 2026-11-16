// ====== Paramètres de la plage OK ======
const MIN_OK = 2;
const MAX_OK = 8;

// ====== Variables "mémoire" côté navigateur ======
let lastTimestamp = null;
let alertCounter = 0;
let operatorActions = {};

// ====== LocalStorage Helpers ======
function loadFromStorage() {
  // Load persisted values (default to initial values if not found)
  alertCounter = parseInt(localStorage.getItem('alertCounter')) || 0;
  lastTimestamp = localStorage.getItem('lastTimestamp') || null;
  operatorActions = JSON.parse(localStorage.getItem('operatorActions')) || {};
}

function saveToStorage() {
  // Save current values
  localStorage.setItem('alertCounter', alertCounter);
  localStorage.setItem('lastTimestamp', lastTimestamp);
  localStorage.setItem('operatorActions', JSON.stringify(operatorActions));
}

// ====== Format durée ======
function formatAge(seconds) {
  const s = Math.max(0, seconds);
  const days = Math.floor(s / 86400);
  const hours = Math.floor((s % 86400) / 3600);
  const mins = Math.floor((s % 3600) / 60);
  const secs = s % 60;
  if (days > 0) return `${days}j ${hours}h ${mins}min ${secs}s`;
  if (hours > 0) return `${hours}h ${mins}min ${secs}s`;
  if (mins > 0) return `${mins}min ${secs}s`;
  return `${secs}s`;
}

// ====== UI Incident ======
function setIncidentUI(isIncident) {
  const badge = document.getElementById("incident-badge");
  const status = document.getElementById("incident-status");
  const counterEl = document.getElementById("incident-counter");
  const op1 = document.getElementById("op1");
  const op2 = document.getElementById("op2");
  const op3 = document.getElementById("op3");

  if (!badge || !status || !counterEl || !op1 || !op2 || !op3) {
    console.warn("Incident UI elements not found");
    return;
  }

  counterEl.textContent = alertCounter;

  if (!isIncident) {
    badge.textContent = "OK";
    badge.classList.remove("alert");
    badge.classList.add("ok");
    status.textContent = "Pas d'incident";
    op1.classList.add("hidden");
    op2.classList.add("hidden");
    op3.classList.add("hidden");
    return;
  }

  badge.textContent = "ALERTE";
  badge.classList.remove("ok");
  badge.classList.add("alert");
  status.textContent = "Incident en cours (T hors plage)";
  alertCounter > 0 ? op1.classList.remove("hidden") : op1.classList.add("hidden");
  alertCounter > 3 ? op2.classList.remove("hidden") : op2.classList.add("hidden");
  alertCounter > 6 ? op3.classList.remove("hidden") : op3.classList.add("hidden");
}

// ====== Chargement données ======
async function loadLatest() {
  const tempEl = document.getElementById("temp");
  const humEl = document.getElementById("hum");
  const tempTimeEl = document.getElementById("temp-time");
  const humTimeEl = document.getElementById("hum-time");

  if (!tempEl || !humEl || !tempTimeEl || !humTimeEl) {
    console.warn("Dashboard elements not found yet");
    return;
  }

  try {
    const res = await fetch("/latest/");
    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }
    
    const data = await res.json();
    if (!data || data.temperature === undefined || data.humidity === undefined || !data.timestamp) {
      console.error("Données API invalides:", data);
      return;
    }

    const t = Number(data.temperature);
    const h = Number(data.humidity);
    if (isNaN(t) || isNaN(h)) {
      console.error("Invalid numeric data:", data);
      return;
    }
    const timestamp = data.timestamp;

    tempEl.textContent = t.toFixed(1) + " °C";
    humEl.textContent = h.toFixed(1) + " %";

    const date = new Date(timestamp);
    const diffSec = Math.round((Date.now() - date.getTime()) / 1000);
    tempTimeEl.textContent = "il y a : " + formatAge(diffSec);
    humTimeEl.textContent = "il y a : " + formatAge(diffSec);

    // 🔥 compteur uniquement si nouvelle mesure
    if (timestamp !== lastTimestamp) {
      lastTimestamp = timestamp;
      if (t < MIN_OK || t > MAX_OK) {
        alertCounter++;
      } else {
        alertCounter = 0;
      }
      // Save after updating
      saveToStorage();
    }

    const isIncident = (t < MIN_OK || t > MAX_OK);
    setIncidentUI(isIncident);

  } catch (e) {
    console.error("Erreur API :", e);
    if (tempEl) tempEl.textContent = "Erreur";
    if (humEl) humEl.textContent = "Erreur";
  }
}

// ====== Fonctions utilitaires ======
function showNotification(message, duration = 3000) {
  const notification = document.getElementById('notification');
  notification.textContent = message;
  notification.style.display = 'block';

  setTimeout(() => {
    notification.style.display = 'none';
  }, duration);
}

function addCommentToChat(opNumber, comment, type = 'validation') {
  const chatContainer = document.getElementById(`chat-op${opNumber}`);
  const messageDiv = document.createElement('div');
  messageDiv.className = 'chat-message';

  const timestamp = new Date().toLocaleString('fr-FR');
  const action = type === 'ack' ? 'Accusé de réception' : 'Validation';

  messageDiv.innerHTML = `
    <strong>${action}:</strong> ${comment}
    <div class="chat-timestamp">${timestamp}</div>
  `;

  chatContainer.appendChild(messageDiv);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

function loadOperatorActions() {
  // Load and display persisted operator actions
  for (let opNumber = 1; opNumber <= 3; opNumber++) {
    const actions = operatorActions[opNumber] || [];
    const chatContainer = document.getElementById(`chat-op${opNumber}`);
    const opCard = document.getElementById(`op${opNumber}`);

    actions.forEach(action => {
      const messageDiv = document.createElement('div');
      messageDiv.className = 'chat-message';

      messageDiv.innerHTML = `
        <strong>${action.type === 'ack' ? 'Accusé de réception' : 'Validation'}:</strong> ${action.comment}
        <div class="chat-timestamp">${action.timestamp}</div>
      `;

      chatContainer.appendChild(messageDiv);
    });

    // If operator has been validated, keep the card visible but disable buttons
    const hasValidation = actions.some(action => action.type === 'validation');
    if (hasValidation) {
      opCard.classList.remove('hidden');
      const ackBtn = opCard.querySelector('.ack-btn');
      const valBtn = opCard.querySelector('.validation-btn');
      const textarea = opCard.querySelector('textarea');

      if (ackBtn) ackBtn.disabled = true;
      if (valBtn) valBtn.disabled = true;
      if (textarea) textarea.disabled = true;
    }
  }
}

// ====== Validation des opérateurs ======
function acknowledgeAlert(opNumber) {
  console.log(`Opérateur ${opNumber} a accusé réception de l'alerte`);
  showNotification(`Opérateur ${opNumber} a accusé réception de l'alerte`);

  // Ajouter au chat
  addCommentToChat(opNumber, 'Alerte reçue et prise en compte', 'ack');
}

function validateOperator(opNumber) {
  const opCard = document.getElementById(`op${opNumber}`);
  const textarea = opCard.querySelector('textarea');
  const comment = textarea.value.trim();

  if (!comment) {
    alert('Veuillez ajouter un commentaire avant de valider.');
    return;
  }

  // Ici, vous pouvez envoyer le commentaire à l'API ou le stocker localement
  console.log(`Opérateur ${opNumber} a ajouté un commentaire: ${comment}`);
  showNotification(`Opérateur ${opNumber} a ajouté un commentaire`);

  // Ajouter au chat
  addCommentToChat(opNumber, comment, 'validation');

  // Vider le textarea
  textarea.value = '';

  // Masquer la carte de l'opérateur après validation
  opCard.classList.add('hidden');

  // Optionnel: envoyer à l'API
  // sendValidationToAPI(opNumber, comment);
}

// ====== Lancement ======
console.log("Dashboard initialized");
// Load persisted data on startup
loadFromStorage();
// Load operator actions
loadOperatorActions();
// Initial load
loadLatest();
// Periodic updates
setInterval(loadLatest, 5000);
