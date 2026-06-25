/**
 * ui.js — funciones puras de renderizado del DOM.
 * No contiene lógica de negocio ni llamadas a la API; solo pinta estado.
 */

const UI = {};

/* ---------- Utilidades ---------- */

function escapeHtml(str) {
  return (str || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function formatDate(isoString) {
  try {
    const date = new Date(isoString);
    return date.toLocaleDateString("es-ES", { day: "2-digit", month: "short", year: "numeric" });
  } catch (_) {
    return "";
  }
}

const LANGUAGE_LABELS = { es: "ES", en: "EN", fr: "FR", de: "DE", it: "IT", pt: "PT" };
const SUMMARY_TYPE_LABELS = { executive: "Ejecutivo", detailed: "Detallado", bullet_points: "Viñetas" };

/* ---------- Render del cuerpo del resumen (markdown ligero, seguro) ---------- */

UI.renderSummaryBody = function (text) {
  if (!text) return "<p>—</p>";
  const lines = text.split("\n");
  let html = "";
  let inList = false;

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line) {
      if (inList) {
        html += "</ul>";
        inList = false;
      }
      continue;
    }
    if (line.startsWith("## ")) {
      if (inList) {
        html += "</ul>";
        inList = false;
      }
      html += `<h2>${escapeHtml(line.slice(3))}</h2>`;
    } else if (line.startsWith("- ") || line.startsWith("• ")) {
      if (!inList) {
        html += "<ul>";
        inList = true;
      }
      html += `<li>${escapeHtml(line.slice(2))}</li>`;
    } else {
      if (inList) {
        html += "</ul>";
        inList = false;
      }
      html += `<p>${escapeHtml(line)}</p>`;
    }
  }
  if (inList) html += "</ul>";
  return html;
};

/* ---------- Historial (sidebar) ---------- */

UI.renderHistory = function (items, activeId, { onSelect, onDelete }) {
  const container = document.getElementById("historyList");
  container.innerHTML = "";

  if (!items || items.length === 0) {
    container.innerHTML =
      '<div class="history-empty">Aún no tienes resúmenes. Pega el enlace de un video para empezar.</div>';
    return;
  }

  for (const item of items) {
    const el = document.createElement("div");
    el.className = "history-item" + (item.id === activeId ? " active" : "");
    el.innerHTML = `
      <img class="history-thumb" src="${item.thumbnail_url || ""}" alt="" loading="lazy" />
      <div class="history-info">
        <div class="history-title">${escapeHtml(item.title || item.video_url)}</div>
        <div class="history-meta">${LANGUAGE_LABELS[item.language] || item.language} · ${formatDate(item.created_at)}</div>
      </div>
      <button class="history-delete" title="Eliminar" aria-label="Eliminar del historial">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m3 0-1 14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2L4 6"/>
        </svg>
      </button>
    `;
    el.querySelector(".history-info").addEventListener("click", () => onSelect(item));
    el.querySelector(".history-thumb").addEventListener("click", () => onSelect(item));
    el.querySelector(".history-delete").addEventListener("click", (evt) => {
      evt.stopPropagation();
      onDelete(item);
    });
    container.appendChild(el);
  }
};

/* ---------- Resultado principal ---------- */

UI.renderResult = function (result) {
  document.getElementById("resultThumb").src = result.thumbnail_url || "";
  document.getElementById("resultThumb").alt = result.title || "";
  document.getElementById("resultTitle").textContent = result.title || "Video sin título";
  document.getElementById("resultChannel").textContent = result.channel || "Canal desconocido";

  const metaChips = document.getElementById("resultMetaChips");
  const cachedChip = result.cached ? '<span class="cc-chip accent">Desde caché</span>' : "";
  metaChips.innerHTML = `
    <span class="cc-chip">${LANGUAGE_LABELS[result.language] || result.language}</span>
    <span class="cc-chip">${SUMMARY_TYPE_LABELS[result.summary_type] || result.summary_type}</span>
    ${cachedChip}
  `;

  document.getElementById("summaryBody").innerHTML = UI.renderSummaryBody(result.summary);

  // Tabs activos
  document.querySelectorAll(".tab").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.type === result.summary_type);
  });

  // Validación
  const validationNote = document.getElementById("validationNote");
  const v = result.validation;
  if (v && ((v.issues && v.issues.length) || (v.warnings && v.warnings.length))) {
    const parts = [...(v.issues || []), ...(v.warnings || [])];
    validationNote.textContent = "⚠ " + parts.join(" · ");
    validationNote.classList.add("warn");
  } else {
    validationNote.textContent = "";
    validationNote.classList.remove("warn");
  }

  // Keywords y tags (estilo caption-chip)
  UI.renderChipList("keywordsRow", result.keywords);
  UI.renderChipList("tagsRow", result.tags);

  // Entidades
  const entities = result.entities || {};
  UI.renderEntityList("entitiesPeople", entities.people);
  UI.renderEntityList("entitiesOrgs", entities.organizations);
  UI.renderEntityList("entitiesPlaces", entities.places);

  // Sentimiento
  UI.renderSentiment(result.sentiment);

  // Traducciones
  UI.renderTranslations(result.translations);

  document.getElementById("resultSection").hidden = false;
  document.getElementById("heroSection").style.display = "none";
};

UI.renderChipList = function (containerId, items) {
  const container = document.getElementById(containerId);
  container.innerHTML = "";
  (items || []).forEach((item) => {
    const chip = document.createElement("span");
    chip.className = "cc-chip";
    chip.textContent = item;
    container.appendChild(chip);
  });
};

UI.renderEntityList = function (containerId, items) {
  const container = document.getElementById(containerId);
  container.innerHTML = "";
  (items || []).forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    container.appendChild(li);
  });
};

UI.renderSentiment = function (sentiment) {
  const marker = document.getElementById("gaugeMarker");
  const positions = { negative: "8%", neutral: "50%", positive: "92%" };
  marker.style.left = positions[sentiment] || "50%";
};

UI.renderTranslations = function (translations) {
  const block = document.getElementById("translationsBlock");
  const container = document.getElementById("translationsContainer");
  const entries = Object.entries(translations || {});

  if (entries.length === 0) {
    block.hidden = true;
    return;
  }

  container.innerHTML = "";
  for (const [lang, text] of entries) {
    const item = document.createElement("div");
    item.className = "translation-item";
    item.innerHTML = `
      <div class="translation-item-header">
        <span class="cc-chip">${LANGUAGE_LABELS[lang] || lang}</span>
      </div>
      <div class="translation-body">${escapeHtml(text)}</div>
    `;
    container.appendChild(item);
  }
  block.hidden = false;
};

/* ---------- Loader de "captions en vivo" ---------- */

UI.captionLoader = (function () {
  let timeoutId = null;
  let messageIndex = 0;
  let charIndex = 0;
  let messages = [];

  function typeStep() {
    const el = document.getElementById("captionText");
    const current = messages[messageIndex % messages.length];

    if (charIndex <= current.length) {
      el.textContent = current.slice(0, charIndex);
      charIndex += 1;
      timeoutId = setTimeout(typeStep, 28);
    } else {
      timeoutId = setTimeout(() => {
        messageIndex += 1;
        charIndex = 0;
        typeStep();
      }, 1100);
    }
  }

  return {
    start(customMessages) {
      messages = customMessages;
      messageIndex = 0;
      charIndex = 0;
      document.getElementById("captionLoader").hidden = false;
      typeStep();
    },
    stop() {
      clearTimeout(timeoutId);
      document.getElementById("captionLoader").hidden = true;
      document.getElementById("captionText").textContent = "";
    },
  };
})();

/* ---------- Errores ---------- */

UI.showError = function (message) {
  const banner = document.getElementById("errorBanner");
  banner.textContent = message;
  banner.hidden = false;
};

UI.hideError = function () {
  document.getElementById("errorBanner").hidden = true;
};

/* ---------- Toast de copiado ---------- */

UI.showCopyToast = function (text) {
  const toast = document.getElementById("copyToast");
  toast.textContent = text || "Copiado al portapapeles";
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 1800);
};
