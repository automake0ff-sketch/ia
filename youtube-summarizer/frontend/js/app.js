/**
 * app.js — estado de la aplicación y manejo de eventos.
 * Conecta api.js (datos) con ui.js (presentación).
 */

(function () {
  "use strict";

  /* ---------- Identidad anónima persistente (solo local, sin backend) ---------- */

  function getUserId() {
    let userId = localStorage.getItem("subtexto_user_id");
    if (!userId) {
      userId = (crypto.randomUUID && crypto.randomUUID()) || `user_${Date.now()}_${Math.random().toString(16).slice(2)}`;
      localStorage.setItem("subtexto_user_id", userId);
    }
    return userId;
  }

  const USER_ID = getUserId();

  /* ---------- Estado en memoria ---------- */

  const state = {
    currentVideoUrl: null,
    currentLanguage: "es",
    currentProvider: "openai",
    currentExtraLanguages: [],
    currentHistoryId: null,
    isLoading: false,
    history: [],
  };

  const LOADING_MESSAGES = [
    "Extrayendo subtítulos del video...",
    "Detectando idioma de origen...",
    "Generando el resumen...",
    "Verificando calidad y formato...",
    "Extrayendo palabras clave y temas...",
  ];

  /* ---------- Referencias al DOM ---------- */

  const els = {
    videoUrlInput: document.getElementById("videoUrlInput"),
    summarizeBtn: document.getElementById("summarizeBtn"),
    languageSelect: document.getElementById("languageSelect"),
    summaryTypeSelect: document.getElementById("summaryTypeSelect"),
    providerSelect: document.getElementById("providerSelect"),
    extraLangRow: document.getElementById("extraLangRow"),
    recIndicator: document.getElementById("recIndicator"),
    heroSection: document.getElementById("heroSection"),
    resultSection: document.getElementById("resultSection"),
    summaryTypeTabs: document.getElementById("summaryTypeTabs"),
    copyBtn: document.getElementById("copyBtn"),
    exportBtn: document.getElementById("exportBtn"),
    exportOptions: document.getElementById("exportOptions"),
    newSummaryBtn: document.getElementById("newSummaryBtn"),
    clearHistoryBtn: document.getElementById("clearHistoryBtn"),
    themeToggleBtn: document.getElementById("themeToggleBtn"),
    sidebarOpenBtn: document.getElementById("sidebarOpenBtn"),
    sidebarCloseBtn: document.getElementById("sidebarCloseBtn"),
    sidebar: document.getElementById("sidebar"),
    mainOverlay: document.getElementById("mainOverlay"),
  };

  /* ---------- Tema claro/oscuro ---------- */

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("subtexto_theme", theme);
    document.getElementById("themeIconMoon").style.display = theme === "dark" ? "block" : "none";
    document.getElementById("themeIconSun").style.display = theme === "light" ? "block" : "none";
  }

  function initTheme() {
    const saved = localStorage.getItem("subtexto_theme");
    if (saved) {
      applyTheme(saved);
      return;
    }
    const prefersLight = window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches;
    applyTheme(prefersLight ? "light" : "dark");
  }

  els.themeToggleBtn.addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme");
    applyTheme(current === "dark" ? "light" : "dark");
  });

  /* ---------- Sidebar móvil ---------- */

  function openSidebar() {
    els.sidebar.classList.add("open");
    els.mainOverlay.classList.add("open");
  }

  function closeSidebar() {
    els.sidebar.classList.remove("open");
    els.mainOverlay.classList.remove("open");
  }

  els.sidebarOpenBtn.addEventListener("click", openSidebar);
  els.sidebarCloseBtn.addEventListener("click", closeSidebar);
  els.mainOverlay.addEventListener("click", closeSidebar);

  /* ---------- Idiomas extra para traducción ---------- */

  els.extraLangRow.addEventListener("click", (evt) => {
    const chip = evt.target.closest(".lang-chip");
    if (!chip) return;
    const lang = chip.dataset.lang;
    chip.classList.toggle("selected");
    if (chip.classList.contains("selected")) {
      if (!state.currentExtraLanguages.includes(lang)) state.currentExtraLanguages.push(lang);
    } else {
      state.currentExtraLanguages = state.currentExtraLanguages.filter((l) => l !== lang);
    }
  });

  /* ---------- Historial ---------- */

  async function loadHistory() {
    try {
      const items = await Api.getHistory(USER_ID);
      state.history = items;
      renderHistoryList();
    } catch (err) {
      console.error("No se pudo cargar el historial:", err);
    }
  }

  function renderHistoryList() {
    UI.renderHistory(state.history, state.currentHistoryId, {
      onSelect: showHistoryItem,
      onDelete: removeHistoryItem,
    });
  }

  function showHistoryItem(item) {
    let keywords = [];
    let tags = [];
    try {
      keywords = JSON.parse(item.keywords || "[]");
    } catch (_) {}
    try {
      tags = JSON.parse(item.tags || "[]");
    } catch (_) {}

    state.currentVideoUrl = item.video_url;
    state.currentLanguage = item.language;
    state.currentHistoryId = item.id;

    els.videoUrlInput.value = item.video_url;
    els.languageSelect.value = item.language;
    els.summaryTypeSelect.value = item.summary_type;

    UI.hideError();
    UI.renderResult({
      history_id: item.id,
      video_id: item.video_id,
      video_url: item.video_url,
      title: item.title,
      channel: item.channel,
      thumbnail_url: item.thumbnail_url,
      language: item.language,
      summary_type: item.summary_type,
      summary: item.summary,
      keywords,
      tags,
      topics: [],
      sentiment: item.sentiment,
      entities: {},
      translations: {},
      validation: null,
      cached: true,
    });

    renderHistoryList();
    closeSidebar();
  }

  async function removeHistoryItem(item) {
    try {
      await Api.deleteHistoryItem(item.id);
      state.history = state.history.filter((h) => h.id !== item.id);
      if (state.currentHistoryId === item.id) {
        resetToHero();
      }
      renderHistoryList();
    } catch (err) {
      console.error("No se pudo eliminar el elemento del historial:", err);
    }
  }

  els.clearHistoryBtn.addEventListener("click", async () => {
    if (!confirm("¿Borrar todo tu historial de resúmenes? Esta acción no se puede deshacer.")) return;
    try {
      await Api.clearHistory(USER_ID);
      state.history = [];
      resetToHero();
      renderHistoryList();
    } catch (err) {
      console.error("No se pudo borrar el historial:", err);
    }
  });

  /* ---------- Resetear a estado inicial ---------- */

  function resetToHero() {
    state.currentVideoUrl = null;
    state.currentHistoryId = null;
    els.videoUrlInput.value = "";
    els.resultSection.hidden = true;
    els.heroSection.style.display = "";
    UI.hideError();
  }

  els.newSummaryBtn.addEventListener("click", () => {
    resetToHero();
    closeSidebar();
    els.videoUrlInput.focus();
  });

  /* ---------- Resumir un video ---------- */

  function setLoading(isLoading) {
    state.isLoading = isLoading;
    els.summarizeBtn.disabled = isLoading;
    els.recIndicator.classList.toggle("live", isLoading);
    if (isLoading) {
      UI.captionLoader.start(LOADING_MESSAGES);
    } else {
      UI.captionLoader.stop();
    }
  }

  async function runSummarize({ videoUrl, language, summaryType, provider, extraLanguages, useCache = true }) {
    if (!videoUrl || !videoUrl.trim()) {
      UI.showError("Pega primero el enlace de un video de YouTube.");
      return;
    }

    UI.hideError();
    setLoading(true);

    try {
      const result = await Api.summarize({
        video_url: videoUrl.trim(),
        language,
        summary_type: summaryType,
        provider,
        user_id: USER_ID,
        use_cache: useCache,
        extra_languages: extraLanguages || [],
      });

      state.currentVideoUrl = result.video_url;
      state.currentLanguage = result.language;
      state.currentProvider = provider;
      state.currentHistoryId = result.history_id;

      UI.renderResult(result);
      await loadHistory();
    } catch (err) {
      console.error(err);
      UI.showError(err.message || "Ocurrió un error al procesar el video. Intenta nuevamente.");
    } finally {
      setLoading(false);
    }
  }

  els.summarizeBtn.addEventListener("click", () => {
    runSummarize({
      videoUrl: els.videoUrlInput.value,
      language: els.languageSelect.value,
      summaryType: els.summaryTypeSelect.value,
      provider: els.providerSelect.value,
      extraLanguages: state.currentExtraLanguages,
    });
  });

  els.videoUrlInput.addEventListener("keydown", (evt) => {
    if (evt.key === "Enter") {
      evt.preventDefault();
      els.summarizeBtn.click();
    }
  });

  /* ---------- Tabs de tipo de resumen (re-resumir con la misma URL) ---------- */

  els.summaryTypeTabs.addEventListener("click", (evt) => {
    const btn = evt.target.closest(".tab");
    if (!btn || state.isLoading) return;
    const summaryType = btn.dataset.type;
    if (!state.currentVideoUrl) return;

    els.summaryTypeSelect.value = summaryType;
    runSummarize({
      videoUrl: state.currentVideoUrl,
      language: state.currentLanguage,
      summaryType,
      provider: els.providerSelect.value,
      extraLanguages: state.currentExtraLanguages,
    });
  });

  /* ---------- Copiar al portapapeles ---------- */

  els.copyBtn.addEventListener("click", async () => {
    const summaryText = document.getElementById("summaryBody").innerText;
    try {
      await navigator.clipboard.writeText(summaryText);
      UI.showCopyToast("Copiado al portapapeles");
    } catch (err) {
      UI.showCopyToast("No se pudo copiar");
    }
  });

  /* ---------- Exportar ---------- */

  els.exportBtn.addEventListener("click", (evt) => {
    evt.stopPropagation();
    if (!state.currentHistoryId) {
      UI.showCopyToast("Genera un resumen antes de exportar");
      return;
    }
    els.exportOptions.classList.toggle("open");
  });

  els.exportOptions.addEventListener("click", (evt) => {
    const btn = evt.target.closest("button[data-format]");
    if (!btn || !state.currentHistoryId) return;
    const url = Api.exportUrl(state.currentHistoryId, btn.dataset.format);
    window.location.href = url;
    els.exportOptions.classList.remove("open");
  });

  document.addEventListener("click", (evt) => {
    if (!els.exportOptions.contains(evt.target) && evt.target !== els.exportBtn) {
      els.exportOptions.classList.remove("open");
    }
  });

  /* ---------- Inicialización ---------- */

  initTheme();
  loadHistory();
})();
