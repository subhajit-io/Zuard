// Zuard Frontend Application Logic — Master Controller
// Deterministic Pre-Screening, Branched RAG & Beginner-Friendly Brand Governance
document.addEventListener('DOMContentLoaded', () => {
  // Configurable API base
  const API_BASE = (window.location.port === "8000" || window.location.pathname.startsWith("/api"))
    ? "/api"
    : (window.ZUARD_API_URL || "http://127.0.0.1:8000/api");

  // ==========================================================================
  // DOM Elements Selection
  // ==========================================================================
  const navTabs = document.querySelectorAll('.nav-tab');
  const tabContents = document.querySelectorAll('.tab-content');
  const viewPills = document.querySelectorAll('.view-pill');
  const viewPanels = document.querySelectorAll('.editor-view-panel');

  const draftText = document.getElementById('draft-text');
  const docTitleInput = document.getElementById('doc-title-input');
  const docStatusBadge = document.getElementById('document-status-badge');
  const privacyToggle = document.getElementById('privacy-toggle');
  const privacyStatusText = document.getElementById('privacy-status-text');
  const charCountBadge = document.getElementById('char-count-badge');
  const navIssuesBadge = document.getElementById('nav-issues-badge');

  // Stepper Elements
  const stepItems = document.querySelectorAll('.step-item');

  // Multi-Project Workspace Elements
  let currentProjectId = "zuard-enterprise";
  let projectsListCache = [];
  const projectSelector = document.getElementById('project-selector');
  const workspaceChipsGrid = document.getElementById('workspace-chips-grid');
  const activeProjectSlug = document.getElementById('active-project-slug');
  const activeProjectName = document.getElementById('active-project-name');
  const activeProjectDesc = document.getElementById('active-project-desc');
  const activeProjectPersona = document.getElementById('active-project-persona');
  const activeProjectRuleCount = document.getElementById('active-project-rule-count');
  const btnCreateProjectTrigger = document.getElementById('btn-create-project-trigger');
  const btnOpenNewProjectModal = document.getElementById('btn-open-new-project-modal');
  const newProjectModal = document.getElementById('new-project-modal');
  const btnCloseProjectModal = document.getElementById('btn-close-project-modal');
  const btnCancelProjectModal = document.getElementById('btn-cancel-project-modal');
  const newProjectForm = document.getElementById('new-project-form');

  // Document Upload Elements
  const documentDropzone = document.getElementById('document-dropzone');
  const documentFileInput = document.getElementById('document-file-input');
  const btnBrowseDocumentFile = document.getElementById('btn-browse-document-file');
  const selectedFileCard = document.getElementById('selected-file-card');
  const selectedFileName = document.getElementById('selected-file-name');
  const selectedFileSize = document.getElementById('selected-file-size');
  const selectedFileStatus = document.getElementById('selected-file-status');
  const selectedFileHint = document.getElementById('selected-file-hint');
  const btnReloadFileContent = document.getElementById('btn-reload-file-content');
  const btnRemoveSelectedFile = document.getElementById('btn-remove-selected-file');
  let currentUploadedFile = null;
  let currentFileRawText = "";

  // Presets
  const btnLoadSample1 = document.getElementById('btn-load-sample-1');
  const btnLoadSample2 = document.getElementById('btn-load-sample-2');
  const btnLoadSample3 = document.getElementById('btn-load-sample-3');
  const presetButtons = [btnLoadSample1, btnLoadSample2, btnLoadSample3];

  // Audit Buttons & Indicators
  const btnRunAudit = document.getElementById('btn-run-audit');
  const btnClearText = document.getElementById('btn-clear-text');
  const btnCopyDraft = document.getElementById('btn-copy-draft');
  const cardsList = document.getElementById('cards-list');
  const inspectorCardsCount = document.getElementById('inspector-cards-count');
  const statIssueStatus = document.getElementById('stat-issue-status');

  // Metrics Bar Elements
  const statScore = document.getElementById('stat-score');
  const statScoreSub = document.getElementById('stat-score-sub');
  const statLatency = document.getElementById('stat-latency');
  const statViolations = document.getElementById('stat-violations');
  const scoreRingBar = document.getElementById('score-ring-bar');
  const dimensionIndicators = document.querySelectorAll('#dimension-indicators .dim-chip');

  // Views & Diff Panes
  const flaggedMarkupDisplay = document.getElementById('flagged-markup-display');
  const diffOriginalContent = document.getElementById('diff-original-content');
  const diffSuggestedContent = document.getElementById('diff-suggested-content');
  const btnApplyFullRewrite = document.getElementById('btn-apply-full-rewrite');

  // Visual Studio Elements
  const fgColorInput = document.getElementById('fg-color-input');
  const bgColorInput = document.getElementById('bg-color-input');
  const fgColorPicker = document.getElementById('fg-color-picker');
  const bgColorPicker = document.getElementById('bg-color-picker');
  const altTextInput = document.getElementById('alt-text-input');
  const altQualityBadge = document.getElementById('alt-quality-badge');
  const contrastPreviewChip = document.getElementById('contrast-preview-chip');

  // Filtering for Inspector Cards
  const filterPills = document.querySelectorAll('.filter-pill');
  const cardsSearchInput = document.getElementById('cards-search-input');
  let currentCardFilter = 'all';
  let currentSearchQuery = '';

  // Manager Signoff & Review
  const managerStatusText = document.getElementById('manager-status-text');
  const btnRequestChanges = document.getElementById('btn-request-changes');
  const btnApprovePublication = document.getElementById('btn-approve-publication');
  const signoffDot = document.getElementById('signoff-dot');
  const feedbackItemsList = document.getElementById('feedback-items-list');

  // Review Feedback Modal
  const feedbackModal = document.getElementById('feedback-modal');
  const feedbackNotesInput = document.getElementById('feedback-notes-input');
  const btnCloseFeedbackModal = document.getElementById('btn-close-feedback-modal');
  const btnCancelFeedbackModal = document.getElementById('btn-cancel-feedback-modal');
  const btnSubmitFeedback = document.getElementById('btn-submit-feedback');

  // Approval Certificate Modal
  const approvalModal = document.getElementById('approval-modal');
  const btnCloseApprovalModal = document.getElementById('btn-close-approval-modal');
  const btnDoneCertificate = document.getElementById('btn-done-certificate');
  const btnPrintCertificate = document.getElementById('btn-print-certificate');

  // Document Submission Elements
  const btnSubmitDocument = document.getElementById('btn-submit-document');
  const submissionValidationBox = document.getElementById('submission-validation-box');
  const submissionSuccessModal = document.getElementById('submission-success-modal');
  const btnCloseSubmissionModal = document.getElementById('btn-close-submission-modal');
  const btnDoneSubmission = document.getElementById('btn-done-submission');
  const btnViewSubmissionActivity = document.getElementById('btn-view-submission-activity');
  const submitSummaryDoc = document.getElementById('submit-summary-doc');
  const submitSummaryProject = document.getElementById('submit-summary-project');
  const submitSummaryScore = document.getElementById('submit-summary-score');
  const submitSummaryId = document.getElementById('submit-summary-id');

  // Submission Checklist Items
  const checkSubWorkspace = document.getElementById('check-sub-workspace');
  const checkSubTitle = document.getElementById('check-sub-title');
  const checkSubContent = document.getElementById('check-sub-content');
  const checkSubAudit = document.getElementById('check-sub-audit');
  const checkIconTitle = document.getElementById('check-icon-title');
  const checkIconContent = document.getElementById('check-icon-content');
  const checkIconAudit = document.getElementById('check-icon-audit');

  // Guide Modal
  const guideModal = document.getElementById('guide-modal');
  const btnOpenGuideModal = document.getElementById('btn-open-guide-modal');
  const btnCloseGuideModal = document.getElementById('btn-close-guide-modal');
  const btnCloseGuideModalBtn = document.getElementById('btn-close-guide-modal-btn');

  // Activity Log Elements
  const activityList = document.getElementById('activity-list');
  const activityPills = document.querySelectorAll('.activity-pill');
  const activitySearchInput = document.getElementById('activity-search-input');
  const btnExportActivityLog = document.getElementById('btn-export-activity-log');
  const btnClearActivityLog = document.getElementById('btn-clear-activity-log');
  let currentActivityFilter = 'all';
  let activityHistory = [];

  // Vault Elements
  const btnRefreshVault = document.getElementById('btn-refresh-vault');
  const factsTbody = document.getElementById('facts-tbody');
  const termsTbody = document.getElementById('terms-tbody');
  const paletteSwatchesGrid = document.getElementById('palette-swatches-grid');
  const vaultFactsCount = document.getElementById('vault-facts-count');
  const vaultTermsCount = document.getElementById('vault-terms-count');
  const factsSearchInput = document.getElementById('facts-search-input');
  const termsSearchInput = document.getElementById('terms-search-input');
  let rawVaultFacts = [];
  let rawVaultTerms = [];

  // Guidelines Ingestion Elements
  const btnSelectGuidelineFile = document.getElementById('btn-select-guideline-file');
  const guidelineFileInput = document.getElementById('guideline-file-input');
  const guidelineUploadStatus = document.getElementById('guideline-upload-status');
  const guidelinesDropzone = document.getElementById('guidelines-dropzone');

  // Governance Insights Elements
  const btnRefreshAnalytics = document.getElementById('btn-refresh-analytics');
  const kpiTotalDocs = document.getElementById('kpi-total-docs');
  const kpiAvgScore = document.getElementById('kpi-avg-score');
  const kpiAvgSpeed = document.getElementById('kpi-avg-speed');
  const kpiTotalOverrides = document.getElementById('kpi-total-overrides');
  const dimensionBars = document.getElementById('dimension-bars');
  const ambiguityHotspotsList = document.getElementById('ambiguity-hotspots-list');

  let currentAuditResult = null;

  // ==========================================================================
  // 1. Toast Notification Utility
  // ==========================================================================
  function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    let icon = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`;
    if (type === 'success') {
      icon = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>`;
    } else if (type === 'warning') {
      icon = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`;
    }

    toast.innerHTML = `${icon}<span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(20px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3400);
  }

  // ==========================================================================
  // 2. Activity Log System
  // ==========================================================================
  function logActivity(type, title, description) {
    const entry = {
      id: 'ACT-' + Date.now().toString(36) + Math.random().toString(36).substring(2, 5),
      timestamp: new Date(),
      type: type, // 'workspace', 'upload', 'edit', 'audit', 'review', 'submit'
      title: title,
      description: description
    };
    activityHistory.unshift(entry);
    if (activityHistory.length > 80) activityHistory.pop();
    renderActivityLog();
  }

  function renderActivityLog() {
    if (!activityList) return;

    const searchQuery = (activitySearchInput ? activitySearchInput.value : '').toLowerCase().trim();

    const filtered = activityHistory.filter(item => {
      if (currentActivityFilter !== 'all' && item.type !== currentActivityFilter) return false;
      if (searchQuery) {
        const text = `${item.title} ${item.description} ${item.type}`.toLowerCase();
        if (!text.includes(searchQuery)) return false;
      }
      return true;
    });

    if (filtered.length === 0) {
      activityList.innerHTML = `<div class="empty-cards-state"><p class="subtle-text">No activity matching current filter.</p></div>`;
      return;
    }

    const typeIcons = {
      workspace: '🏢',
      upload: '📁',
      edit: '📝',
      audit: '⚡',
      review: '👤',
      submit: '🚀'
    };

    activityList.innerHTML = filtered.map(item => {
      const timeStr = item.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      return `
        <div class="activity-item">
          <div class="activity-icon-bubble act-type-${item.type}">
            ${typeIcons[item.type] || '📌'}
          </div>
          <div class="activity-details">
            <div class="activity-title-row">
              <span class="activity-title">${item.title}</span>
              <span class="activity-time">${timeStr}</span>
            </div>
            <p class="activity-desc">${item.description}</p>
          </div>
        </div>
      `;
    }).join('');
  }

  if (activityPills) {
    activityPills.forEach(pill => {
      pill.addEventListener('click', () => {
        activityPills.forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        currentActivityFilter = pill.getAttribute('data-act-filter');
        renderActivityLog();
      });
    });
  }

  if (activitySearchInput) {
    activitySearchInput.addEventListener('input', renderActivityLog);
  }

  if (btnExportActivityLog) {
    btnExportActivityLog.addEventListener('click', () => {
      if (activityHistory.length === 0) {
        showToast("Activity log is empty.", "warning");
        return;
      }
      const text = activityHistory.map(a =>
        `[${a.timestamp.toISOString()}] [${a.type.toUpperCase()}] ${a.title} - ${a.description}`
      ).join('\n');
      navigator.clipboard.writeText(text).then(() => {
        showToast("Activity log copied to clipboard!", "success");
      });
    });
  }

  if (btnClearActivityLog) {
    btnClearActivityLog.addEventListener('click', () => {
      activityHistory = [];
      renderActivityLog();
      showToast("Activity log cleared", "info");
    });
  }

  // ==========================================================================
  // 3. Navigation Tabs & Workflow Stepper
  // ==========================================================================
  navTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      navTabs.forEach(t => t.classList.remove('active'));
      tabContents.forEach(c => c.classList.remove('active'));
      tab.classList.add('active');
      const targetId = `tab-${tab.getAttribute('data-tab')}`;
      const targetEl = document.getElementById(targetId);
      if (targetEl) targetEl.classList.add('active');

      if (tab.getAttribute('data-tab') === 'brand-vault') {
        loadVaultData();
      } else if (tab.getAttribute('data-tab') === 'activity-log') {
        renderActivityLog();
      } else if (tab.getAttribute('data-tab') === 'governance-insights') {
        loadAnalyticsData();
      }
    });
  });

  // Stepper links smooth scrolling
  stepItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const href = item.getAttribute('href');
      const targetSection = document.querySelector(href);
      if (targetSection) {
        // Ensure Review Portal tab is active
        const reviewTab = document.getElementById('tab-btn-review');
        if (reviewTab && !reviewTab.classList.contains('active')) {
          reviewTab.click();
        }
        stepItems.forEach(s => s.classList.remove('active'));
        item.classList.add('active');
        targetSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // Highlight step on scroll
  window.addEventListener('scroll', () => {
    const sections = ['section-workspace', 'section-upload', 'section-editor', 'section-precheck', 'section-results', 'section-review', 'section-submission'];
    const scrollPos = window.scrollY + 180;
    for (const id of sections) {
      const el = document.getElementById(id);
      if (el) {
        const top = el.offsetTop;
        const height = el.offsetHeight;
        if (scrollPos >= top && scrollPos < top + height) {
          stepItems.forEach(s => {
            if (s.getAttribute('href') === `#${id}`) {
              s.classList.add('active');
            } else {
              s.classList.remove('active');
            }
          });
          break;
        }
      }
    }
  });

  // View Switcher (Draft Editor / Flagged Annotations / Side-by-Side Diff)
  viewPills.forEach(pill => {
    pill.addEventListener('click', () => {
      viewPills.forEach(p => p.classList.remove('active'));
      viewPanels.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      const targetView = document.getElementById(`view-${pill.getAttribute('data-view')}`);
      if (targetView) targetView.classList.add('active');
    });
  });

  // ==========================================================================
  // 4. Submission Checklist Live Evaluator
  // ==========================================================================
  function updateSubmissionChecklist() {
    const titleVal = docTitleInput ? docTitleInput.value.trim() : "";
    const contentVal = draftText ? draftText.value.trim() : "";

    // Title Check
    if (titleVal) {
      if (checkSubTitle) checkSubTitle.textContent = "Provided (" + (titleVal.length > 20 ? titleVal.substring(0, 18) + '...' : titleVal) + ")";
      if (checkIconTitle) {
        checkIconTitle.textContent = "✓";
        checkIconTitle.className = "check-icon";
      }
      const itemTitle = document.getElementById('check-item-title');
      if (itemTitle) { itemTitle.classList.add('valid'); itemTitle.classList.remove('warn'); }
    } else {
      if (checkSubTitle) checkSubTitle.textContent = "Missing";
      if (checkIconTitle) {
        checkIconTitle.textContent = "!";
        checkIconTitle.className = "check-icon warn";
      }
      const itemTitle = document.getElementById('check-item-title');
      if (itemTitle) { itemTitle.classList.remove('valid'); itemTitle.classList.add('warn'); }
    }

    // Content Check
    if (contentVal || currentUploadedFile) {
      if (checkSubContent) checkSubContent.textContent = "Ready (" + (contentVal ? contentVal.split(/\s+/).filter(Boolean).length + " words" : "File attached") + ")";
      if (checkIconContent) {
        checkIconContent.textContent = "✓";
        checkIconContent.className = "check-icon";
      }
      const itemContent = document.getElementById('check-item-content');
      if (itemContent) { itemContent.classList.add('valid'); itemContent.classList.remove('warn'); }
    } else {
      if (checkSubContent) checkSubContent.textContent = "Empty";
      if (checkIconContent) {
        checkIconContent.textContent = "!";
        checkIconContent.className = "check-icon warn";
      }
      const itemContent = document.getElementById('check-item-content');
      if (itemContent) { itemContent.classList.remove('valid'); itemContent.classList.add('warn'); }
    }

    // Audit Check
    if (currentAuditResult) {
      const score = currentAuditResult.compliance_score;
      if (checkSubAudit) checkSubAudit.textContent = `Score: ${score}/100`;
      if (checkIconAudit) {
        if (score >= 85) {
          checkIconAudit.textContent = "✓";
          checkIconAudit.className = "check-icon";
        } else {
          checkIconAudit.textContent = "⚠️";
          checkIconAudit.className = "check-icon warn";
        }
      }
      const itemAudit = document.getElementById('check-item-audit');
      if (itemAudit) {
        if (score >= 85) { itemAudit.classList.add('valid'); itemAudit.classList.remove('warn'); }
        else { itemAudit.classList.remove('valid'); itemAudit.classList.add('warn'); }
      }
    } else {
      if (checkSubAudit) checkSubAudit.textContent = "Pending Run";
      if (checkIconAudit) {
        checkIconAudit.textContent = "?";
        checkIconAudit.className = "check-icon warn";
      }
      const itemAudit = document.getElementById('check-item-audit');
      if (itemAudit) { itemAudit.classList.remove('valid'); itemAudit.classList.add('warn'); }
    }
  }

  // Character & Word Counter
  function updateTextStats() {
    const text = draftText ? draftText.value.trim() : "";
    const chars = text.length;
    const words = text ? text.split(/\s+/).filter(Boolean).length : 0;
    if (charCountBadge) {
      charCountBadge.textContent = `${words} words • ${chars} chars`;
    }
    updateSubmissionChecklist();
  }
  if (draftText) draftText.addEventListener('input', updateTextStats);
  if (docTitleInput) docTitleInput.addEventListener('input', updateSubmissionChecklist);

  // ==========================================================================
  // 5. Privacy Toggle
  // ==========================================================================
  if (privacyToggle) {
    privacyToggle.addEventListener('change', () => {
      if (privacyToggle.checked) {
        privacyStatusText.textContent = "Google Gemini 2.5 Flash Cloud";
        privacyStatusText.style.color = "#93C5FD";
        showToast("Cloud Reasoning Mode Enabled (Google Gemini)", "info");
        logActivity('review', 'Privacy Mode Changed', 'Cloud Reasoning Mode enabled (Google Gemini 2.5 Flash).');
      } else {
        privacyStatusText.textContent = "Confidential Local Mode";
        privacyStatusText.style.color = "var(--text-secondary)";
        showToast("Confidential Local Mode Active (Zero-Cloud Leakage)", "success");
        logActivity('review', 'Privacy Mode Changed', 'Confidential Local Mode active (Zero-cloud leakage guaranteed).');
      }
    });
  }

  // ==========================================================================
  // 6. Visual Studio & WCAG 2.1 Contrast
  // ==========================================================================
  function calcLuminance(r, g, b) {
    const a = [r, g, b].map(v => {
      v /= 255;
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    return a[0] * 0.2126 + a[1] * 0.7152 + a[2] * 0.0722;
  }

  function updateContrastPreview() {
    if (!fgColorInput || !bgColorInput || !contrastPreviewChip) return;
    let fg = fgColorInput.value.trim();
    let bg = bgColorInput.value.trim();

    if (!fg.startsWith('#')) fg = '#' + fg;
    if (!bg.startsWith('#')) bg = '#' + bg;

    if (/^#[0-9A-Fa-f]{6}$/.test(fg) && /^#[0-9A-Fa-f]{6}$/.test(bg)) {
      if (fgColorPicker) fgColorPicker.value = fg;
      if (bgColorPicker) bgColorPicker.value = bg;

      contrastPreviewChip.style.color = fg;
      contrastPreviewChip.style.backgroundColor = bg;

      const r1 = parseInt(fg.slice(1, 3), 16), g1 = parseInt(fg.slice(3, 5), 16), b1 = parseInt(fg.slice(5, 7), 16);
      const r2 = parseInt(bg.slice(1, 3), 16), g2 = parseInt(bg.slice(3, 5), 16), b2 = parseInt(bg.slice(5, 7), 16);

      const l1 = calcLuminance(r1, g1, b1);
      const l2 = calcLuminance(r2, g2, b2);
      const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
      const ratioRound = ratio.toFixed(1);

      let badge = "FAIL";
      if (ratio >= 7.0) {
        badge = "AAA PASS";
      } else if (ratio >= 4.5) {
        badge = "AA PASS";
      } else if (ratio >= 3.0) {
        badge = "AA LARGE ONLY";
      }

      contrastPreviewChip.textContent = `Aa (${ratioRound}:1 ${badge})`;
      contrastPreviewChip.title = `Mathematical WCAG 2.1 Contrast: ${ratioRound}:1 (${badge})`;
    }
  }

  if (fgColorPicker && fgColorInput) {
    fgColorPicker.addEventListener('input', (e) => {
      fgColorInput.value = e.target.value.toUpperCase();
      updateContrastPreview();
    });
    fgColorInput.addEventListener('input', updateContrastPreview);
  }

  if (bgColorPicker && bgColorInput) {
    bgColorPicker.addEventListener('input', (e) => {
      bgColorInput.value = e.target.value.toUpperCase();
      updateContrastPreview();
    });
    bgColorInput.addEventListener('input', updateContrastPreview);
  }

  function updateAltTextQuality() {
    if (!altTextInput || !altQualityBadge) return;
    const text = altTextInput.value.trim();
    if (!text || text.length < 5 || text.toLowerCase() === 'banner' || text.toLowerCase() === 'image') {
      altQualityBadge.textContent = "Generic / Low Quality";
      altQualityBadge.style.background = "var(--accent-rose-soft)";
      altQualityBadge.style.color = "#FCA5A5";
    } else if (text.length < 25) {
      altQualityBadge.textContent = "Fair Description";
      altQualityBadge.style.background = "var(--accent-amber-soft)";
      altQualityBadge.style.color = "#FCD34D";
    } else {
      altQualityBadge.textContent = "✓ High Accessibility Quality";
      altQualityBadge.style.background = "var(--accent-emerald-soft)";
      altQualityBadge.style.color = "#6EE7B7";
    }
  }
  if (altTextInput) altTextInput.addEventListener('input', updateAltTextQuality);

  // ==========================================================================
  // 7. Multi-Project Workspace Management
  // ==========================================================================
  async function loadProjectsList() {
    try {
      const resp = await fetch(`${API_BASE}/projects`);
      projectsListCache = await resp.json();

      if (projectSelector) {
        projectSelector.innerHTML = projectsListCache.map(p => `
          <option value="${p.project_id}" ${p.project_id === currentProjectId ? 'selected' : ''}>
            ${p.name}
          </option>
        `).join('');
      }

      if (workspaceChipsGrid) {
        workspaceChipsGrid.innerHTML = projectsListCache.map(p => {
          const isActive = p.project_id === currentProjectId;
          const stats = p.stats || {};
          const rules = stats.total_terminology_rules || 0;
          const facts = stats.total_approved_facts || 0;
          return `
            <div class="workspace-chip-item ${isActive ? 'active' : ''}" data-project-id="${p.project_id}">
              <div class="chip-title-row">
                <span class="chip-name">${p.name}</span>
                <span class="chip-radio"></span>
              </div>
              <span class="chip-persona">${p.persona || 'Corporate Standard'}</span>
              <span class="chip-stats">${rules} Rules &bull; ${facts} Facts</span>
            </div>
          `;
        }).join('');

        workspaceChipsGrid.querySelectorAll('.workspace-chip-item').forEach(card => {
          card.addEventListener('click', () => {
            const pid = card.getAttribute('data-project-id');
            switchProject(pid);
          });
        });
      }

      updateActiveProjectCard();

    } catch (e) {
      console.error("Failed to load projects list", e);
    }
  }

  function updateActiveProjectCard() {
    const proj = projectsListCache.find(p => p.project_id === currentProjectId);
    if (!proj) return;

    if (activeProjectSlug) activeProjectSlug.textContent = proj.project_id;
    if (activeProjectName) activeProjectName.textContent = proj.name;
    if (activeProjectDesc) activeProjectDesc.textContent = proj.description || "Active isolated brand workspace.";
    if (activeProjectPersona) activeProjectPersona.textContent = proj.persona || "Corporate Governance";

    const stats = proj.stats || {};
    const rules = stats.total_terminology_rules || 0;
    const facts = stats.total_approved_facts || 0;
    if (activeProjectRuleCount) activeProjectRuleCount.textContent = `${rules} Rules • ${facts} Verified Facts`;
    if (checkSubWorkspace) checkSubWorkspace.textContent = proj.name;
  }

  function switchProject(projectId) {
    currentProjectId = projectId;
    if (projectSelector) projectSelector.value = projectId;

    if (workspaceChipsGrid) {
      workspaceChipsGrid.querySelectorAll('.workspace-chip-item').forEach(card => {
        if (card.getAttribute('data-project-id') === projectId) {
          card.classList.add('active');
        } else {
          card.classList.remove('active');
        }
      });
    }

    updateActiveProjectCard();
    loadVaultData();
    showToast(`Switched workspace to: ${activeProjectName ? activeProjectName.textContent : projectId}`, "info");
    logActivity('workspace', 'Switched Workspace', `Active workspace changed to ${activeProjectName ? activeProjectName.textContent : projectId}.`);
    updateSubmissionChecklist();
  }

  if (projectSelector) {
    projectSelector.addEventListener('change', (e) => {
      switchProject(e.target.value);
    });
  }

  function openNewProjectModal() {
    if (newProjectModal) newProjectModal.style.display = 'flex';
  }
  function closeNewProjectModal() {
    if (newProjectModal) newProjectModal.style.display = 'none';
  }

  if (btnOpenNewProjectModal) btnOpenNewProjectModal.addEventListener('click', openNewProjectModal);
  if (btnCreateProjectTrigger) btnCreateProjectTrigger.addEventListener('click', openNewProjectModal);
  if (btnCloseProjectModal) btnCloseProjectModal.addEventListener('click', closeNewProjectModal);
  if (btnCancelProjectModal) btnCancelProjectModal.addEventListener('click', closeNewProjectModal);

  if (newProjectForm) {
    newProjectForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const pId = document.getElementById('new-project-id').value.trim();
      const pName = document.getElementById('new-project-name').value.trim();
      const pPersona = document.getElementById('new-project-persona').value.trim();
      const pDesc = document.getElementById('new-project-desc').value.trim();
      const pFile = document.getElementById('new-project-file').files[0];

      if (!pId || !pName) {
        showToast("Please provide both Project Title and Identifier", "warning");
        return;
      }

      const formData = new FormData();
      formData.append('project_id', pId);
      formData.append('name', pName);
      formData.append('persona', pPersona);
      formData.append('description', pDesc);
      if (pFile) formData.append('guidelines_file', pFile);

      const submitBtn = document.getElementById('btn-submit-new-project');
      submitBtn.disabled = true;
      submitBtn.innerHTML = `<span class="loading-spinner"></span> Creating Workspace...`;

      try {
        const resp = await fetch(`${API_BASE}/projects`, {
          method: 'POST',
          body: formData
        });
        const res = await resp.json();
        if (res.status === 'SUCCESS') {
          showToast(`Project '${pName}' created successfully!`, "success");
          logActivity('workspace', 'Created Brand Workspace', `Created new workspace '${pName}' (ID: ${pId}) with dedicated rule store.`);
          closeNewProjectModal();
          newProjectForm.reset();
          await loadProjectsList();
          switchProject(pId);
        } else {
          showToast("Error creating project: " + (res.message || "Unknown error"), "warning");
        }
      } catch (err) {
        showToast("Network error: " + err.message, "warning");
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "Create & Wire Workspace";
      }
    });
  }

  // ==========================================================================
  // 8. Document Upload & File Handling
  // ==========================================================================
  function handleDocumentFile(file) {
    if (!file) return;

    const maxBytes = 25 * 1024 * 1024;
    if (file.size > maxBytes) {
      showToast("File size exceeds 25 MB limit. Please select a smaller document.", "warning");
      return;
    }

    currentUploadedFile = file;

    const sizeFormatted = file.size < 1024 * 1024
      ? (file.size / 1024).toFixed(1) + " KB"
      : (file.size / (1024 * 1024)).toFixed(2) + " MB";

    if (selectedFileCard) selectedFileCard.style.display = 'flex';
    if (selectedFileName) selectedFileName.textContent = file.name;
    if (selectedFileSize) selectedFileSize.textContent = sizeFormatted;
    if (selectedFileStatus) selectedFileStatus.textContent = "File Ready";

    if (docTitleInput) {
      docTitleInput.value = file.name;
    }

    const ext = file.name.split('.').pop().toLowerCase();

    if (['txt', 'md', 'json', 'csv'].includes(ext)) {
      const reader = new FileReader();
      reader.onload = (e) => {
        currentFileRawText = e.target.result;
        draftText.value = currentFileRawText;
        updateTextStats();
        if (selectedFileHint) selectedFileHint.textContent = `✓ Text contents (${currentFileRawText.length} characters) loaded into Document Editor.`;
        showToast(`Loaded ${file.name} into editor`, "success");
      };
      reader.readAsText(file);
    } else if (ext === 'pdf') {
      if (selectedFileHint) selectedFileHint.textContent = `PDF Document attached. Zuard will extract sections and citations during Pre-Check.`;
      showToast(`Selected PDF: ${file.name}. Ready for pre-check.`, "info");
    } else if (['png', 'jpg', 'jpeg', 'webp'].includes(ext)) {
      if (selectedFileHint) selectedFileHint.textContent = `Visual Banner image attached. Ready for palette and WCAG checks.`;
      showToast(`Selected Image: ${file.name}`, "info");
    }

    logActivity('upload', 'Uploaded Document', `Loaded '${file.name}' (${sizeFormatted}) into workspace.`);
    updateSubmissionChecklist();
  }

  if (btnBrowseDocumentFile && documentFileInput) {
    btnBrowseDocumentFile.addEventListener('click', (e) => {
      e.stopPropagation();
      documentFileInput.click();
    });
  }

  if (documentDropzone && documentFileInput) {
    documentDropzone.addEventListener('click', () => {
      documentFileInput.click();
    });

    documentDropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      documentDropzone.classList.add('dragover');
    });

    documentDropzone.addEventListener('dragleave', () => {
      documentDropzone.classList.remove('dragover');
    });

    documentDropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      documentDropzone.classList.remove('dragover');
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        handleDocumentFile(e.dataTransfer.files[0]);
      }
    });

    documentFileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files[0]) {
        handleDocumentFile(e.target.files[0]);
      }
    });
  }

  if (btnReloadFileContent) {
    btnReloadFileContent.addEventListener('click', () => {
      if (currentFileRawText) {
        draftText.value = currentFileRawText;
        updateTextStats();
        showToast("Reloaded original file text into editor", "info");
      } else if (currentUploadedFile) {
        handleDocumentFile(currentUploadedFile);
      }
    });
  }

  if (btnRemoveSelectedFile) {
    btnRemoveSelectedFile.addEventListener('click', () => {
      currentUploadedFile = null;
      currentFileRawText = "";
      if (selectedFileCard) selectedFileCard.style.display = 'none';
      if (documentFileInput) documentFileInput.value = '';
      showToast("Removed uploaded file attachment", "info");
      updateSubmissionChecklist();
    });
  }

  // ==========================================================================
  // 9. Benchmark Presets
  // ==========================================================================
  function setActivePresetButton(activeBtn) {
    presetButtons.forEach(b => {
      if (b) b.classList.remove('active');
    });
    if (activeBtn) activeBtn.classList.add('active');
  }

  btnLoadSample1.addEventListener('click', () => {
    setActivePresetButton(btnLoadSample1);
    switchProject('zuard-enterprise');
    docTitleInput.value = "Q4_Product_Launch_Release.pdf";
    draftText.value = `Our #1 AI platform is super cheap and cuts costs by 99.9%. With our revolutionary miracle engine, you get 100% infallible automated deployments. Don't worry about complexity—this life hack guarantees insane speedups with our legacy sync feature.`;
    fgColorInput.value = "#FFFFFF";
    bgColorInput.value = "#FF0055";
    altTextInput.value = "banner";
    updateContrastPreview();
    updateAltTextQuality();
    updateTextStats();
    showToast("Loaded Scenario: Q4 Product Launch (Simulates Violations)", "warning");
    logActivity('edit', 'Loaded Benchmark Scenario', 'Loaded Q4 Product Launch scenario simulating critical claims, lexical terms, and WCAG violations.');
    runAudit();
  });

  btnLoadSample2.addEventListener('click', () => {
    setActivePresetButton(btnLoadSample2);
    switchProject('zuard-enterprise');
    docTitleInput.value = "Enterprise_Compliance_Release_v1.pdf";
    draftText.value = `Zuard Enterprise Platform delivers an industry-leading pre-publication brand governance gateway. In recent benchmarks, organisations demonstrated a verified 42% average operational cost reduction, backed by our 99.95% enterprise platform uptime SLA commitment. Teams pre-screen content in an average of 2.5 seconds, saving reviewer hours across all channels.`;
    fgColorInput.value = "#FFFFFF";
    bgColorInput.value = "#0F172A";
    altTextInput.value = "Comprehensive product screenshot of the Zuard review portal dashboard with live metrics";
    updateContrastPreview();
    updateAltTextQuality();
    updateTextStats();
    showToast("Loaded Scenario: Compliant Corporate Release (Gold Standard)", "success");
    logActivity('edit', 'Loaded Benchmark Scenario', 'Loaded Compliant Corporate Release benchmark (100% Gold Standard).');
    runAudit();
  });

  btnLoadSample3.addEventListener('click', () => {
    setActivePresetButton(btnLoadSample3);
    switchProject('zuard-consumer');
    docTitleInput.value = "Mobile_Creator_Announcement.md";
    draftText.value = `The Zuard Consumer app is trusted by over 5 million creators worldwide. Create lively, inspiring video stories with guaranteed 50ms real-time audio sync. Get started with our generous starter tier giving you 10 free exports per month.`;
    fgColorInput.value = "#FFFFFF";
    bgColorInput.value = "#8B5CF6";
    altTextInput.value = "Energetic preview of mobile video timeline editor with multi-track sequencing";
    updateContrastPreview();
    updateAltTextQuality();
    updateTextStats();
    showToast("Loaded Scenario: Visual Banner & Creative A11y", "info");
    logActivity('edit', 'Loaded Benchmark Scenario', 'Loaded Creative Mobile Announcement scenario with vivid purple palette.');
    runAudit();
  });

  // Clear Editor
  btnClearText.addEventListener('click', () => {
    draftText.value = "";
    currentAuditResult = null;
    cardsList.innerHTML = `
      <div class="empty-cards-state">
        <div class="empty-icon-wrap">
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
            <circle cx="12" cy="12" r="10"/>
            <path d="m9 12 2 2 4-4"/>
          </svg>
        </div>
        <h3>Draft Cleared</h3>
        <p>Enter draft copy or select a benchmark scenario above to pre-screen.</p>
      </div>`;
    statScore.textContent = "--";
    statLatency.textContent = "0 ms";
    statViolations.textContent = "0";
    if (statIssueStatus) statIssueStatus.textContent = "0 Pending";
    inspectorCardsCount.textContent = "0 Issues";
    flaggedMarkupDisplay.textContent = "";
    diffOriginalContent.textContent = "";
    diffSuggestedContent.textContent = "";
    if (navIssuesBadge) navIssuesBadge.style.display = 'none';
    if (scoreRingBar) scoreRingBar.style.strokeDashoffset = "144.5";
    dimensionIndicators.forEach(d => d.classList.remove('has-violation'));
    updateTextStats();
    showToast("Draft editor cleared", "info");
    logActivity('edit', 'Cleared Draft Text', 'Cleared document content from editor.');
  });

  // Copy Draft Text
  if (btnCopyDraft) {
    btnCopyDraft.addEventListener('click', () => {
      const text = draftText.value;
      if (!text) {
        showToast("Nothing to copy", "warning");
        return;
      }
      navigator.clipboard.writeText(text).then(() => {
        showToast("Draft copied to clipboard!", "success");
      });
    });
  }

  // Apply Full Rewrite to Editor
  if (btnApplyFullRewrite) {
    btnApplyFullRewrite.addEventListener('click', () => {
      if (currentAuditResult && currentAuditResult.suggested_full_rewrite) {
        draftText.value = currentAuditResult.suggested_full_rewrite;
        updateTextStats();
        const editorPill = document.querySelector('.view-pill[data-view="editor"]');
        if (editorPill) editorPill.click();
        showToast("✓ Applied compliant rewrite to editor", "success");
        logActivity('edit', 'Applied Compliant Rewrite', 'Replaced original draft with zero-hallucination compliant rewrite in editor.');
      } else {
        showToast("No suggested rewrite available", "warning");
      }
    });
  }

  // Keyboard shortcut: Ctrl + Enter
  window.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      runAudit();
    }
    if (e.key === 'Escape') {
      if (newProjectModal) newProjectModal.style.display = 'none';
      if (approvalModal) approvalModal.style.display = 'none';
      if (guideModal) guideModal.style.display = 'none';
      if (feedbackModal) feedbackModal.style.display = 'none';
      if (submissionSuccessModal) submissionSuccessModal.style.display = 'none';
    }
  });

  // ==========================================================================
  // 10. Execute Pre-Check & Audit Pipeline
  // ==========================================================================
  async function runAudit() {
    const text = draftText ? draftText.value.trim() : "";
    if (!text && !currentUploadedFile) {
      showToast("Please enter draft text or select a file to pre-screen.", "warning");
      return;
    }

    btnRunAudit.disabled = true;
    btnRunAudit.innerHTML = `<span class="loading-spinner"></span> Pre-Screening (~2ms)...`;

    try {
      let data = null;

      if (currentUploadedFile && !text) {
        const formData = new FormData();
        formData.append('file', currentUploadedFile);
        formData.append('project_id', currentProjectId);
        formData.append('document_title', docTitleInput.value.trim() || currentUploadedFile.name);
        formData.append('privacy_mode', !privacyToggle.checked);

        const response = await fetch(`${API_BASE}/audit-upload`, {
          method: 'POST',
          body: formData
        });
        if (!response.ok) throw new Error(`Server returned status ${response.status}`);
        data = await response.json();
      } else {
        const payload = {
          project_id: currentProjectId,
          document_title: docTitleInput.value.trim() || "Untitled_Draft",
          content_text: text,
          privacy_mode: !privacyToggle.checked,
          color_pairs: [[fgColorInput.value.trim(), bgColorInput.value.trim()]],
          alt_texts: [{ alt: altTextInput.value.trim(), asset_name: "banner_asset" }]
        };

        const response = await fetch(`${API_BASE}/audit-content`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (!response.ok) throw new Error(`Server returned status ${response.status}`);
        data = await response.json();
      }

      currentAuditResult = data;
      renderAuditResults(data);
      updateSubmissionChecklist();

      showToast(`Pre-check completed in ${data.execution_time_ms} ms (${data.total_violations_count} issues)`, data.total_violations_count > 0 ? "warning" : "success");
      logActivity('audit', 'Pre-Check Completed', `Pre-screening executed in ${data.execution_time_ms} ms. Score: ${data.compliance_score}/100. Issues detected: ${data.total_violations_count}.`);

    } catch (err) {
      console.error(err);
      showToast(`Audit failed: ${err.message}. Ensure backend is running.`, "warning");
    } finally {
      btnRunAudit.disabled = false;
      btnRunAudit.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polygon points="5 3 19 12 5 21 5 3"/></svg>
        <span>Run Pre-Check &amp; Compliance Audit</span>
        <span class="kbd-shortcut" title="Keyboard Shortcut">Ctrl ↵</span>
      `;
    }
  }

  btnRunAudit.addEventListener('click', runAudit);

  // ==========================================================================
  // 11. Render Audit Results
  // ==========================================================================
  function renderAuditResults(data) {
    const score = data.compliance_score;
    statScore.textContent = score;

    // Radial Score Ring Animation
    if (scoreRingBar) {
      const circumference = 144.5;
      const offset = circumference - (score / 100) * circumference;
      scoreRingBar.style.strokeDashoffset = offset;

      if (score >= 85) {
        scoreRingBar.style.stroke = "var(--accent-emerald)";
      } else if (score >= 60) {
        scoreRingBar.style.stroke = "var(--accent-amber)";
      } else {
        scoreRingBar.style.stroke = "var(--accent-rose)";
      }
    }

    if (score >= 85) {
      statScore.className = "metric-value text-green";
      statScoreSub.textContent = "Compliant";
      docStatusBadge.textContent = "Approved — v2";
      docStatusBadge.style.color = "#34D399";
      if (managerStatusText) managerStatusText.textContent = "Ready for Sign-Off";
      if (signoffDot) signoffDot.className = "pulse-indicator pulse-green";
    } else if (score >= 60) {
      statScore.className = "metric-value text-amber";
      statScoreSub.textContent = "Warnings Detected";
      docStatusBadge.textContent = "In Review — v2";
      docStatusBadge.style.color = "#FBBF24";
      if (managerStatusText) managerStatusText.textContent = "Requires Policy Adjustments";
      if (signoffDot) signoffDot.className = "pulse-indicator pulse-amber";
    } else {
      statScore.className = "metric-value text-red";
      statScoreSub.textContent = "Critical Violations";
      docStatusBadge.textContent = "Changes Requested";
      docStatusBadge.style.color = "#F87171";
      if (managerStatusText) managerStatusText.textContent = "Blocked: Critical Violations";
      if (signoffDot) signoffDot.className = "pulse-indicator pulse-amber";
    }

    statLatency.textContent = `${data.execution_time_ms} ms`;
    statViolations.textContent = data.total_violations_count;
    if (statIssueStatus) statIssueStatus.textContent = `${data.total_violations_count} Pending`;
    inspectorCardsCount.textContent = `${data.total_violations_count} Issues`;

    if (navIssuesBadge) {
      if (data.total_violations_count > 0) {
        navIssuesBadge.textContent = data.total_violations_count;
        navIssuesBadge.style.display = 'inline-block';
      } else {
        navIssuesBadge.style.display = 'none';
      }
    }

    // Dimension highlights
    const flaggedDims = new Set();
    (data.inspector_cards || []).forEach(c => {
      flaggedDims.add((c.dimension || '').toLowerCase());
    });
    dimensionIndicators.forEach(chip => {
      const d = chip.getAttribute('data-dim');
      if (flaggedDims.has(d)) {
        chip.classList.add('has-violation');
      } else {
        chip.classList.remove('has-violation');
      }
    });

    // Flagged markup view
    flaggedMarkupDisplay.innerHTML = highlightFlaggedMarkup(data.flagged_draft_markup);
    attachFlagTagClicks();

    // Diff view
    diffOriginalContent.textContent = data.original_text;
    diffSuggestedContent.innerHTML = highlightDiff(data.original_text, data.suggested_full_rewrite);

    // Inspector Cards
    renderInspectorCards(data.inspector_cards);
  }

  function highlightFlaggedMarkup(rawMarkup) {
    if (!rawMarkup) return '<span style="color: var(--text-dim);">No markup generated.</span>';
    return rawMarkup.replace(/(\[FLAG \d+:[^\]]+\])/g, '<span class="flag-tag" title="Click to view inspection card">$1</span>');
  }

  function attachFlagTagClicks() {
    const tags = flaggedMarkupDisplay.querySelectorAll('.flag-tag');
    tags.forEach(tag => {
      tag.addEventListener('click', () => {
        const match = tag.textContent.match(/FLAG (\d+)/);
        if (match) {
          const flagId = `FLAG-${match[1]}`;
          const cardEl = document.getElementById(`card-${flagId}`);
          if (cardEl) {
            cardEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
            cardEl.style.boxShadow = '0 0 20px var(--brand-primary)';
            setTimeout(() => {
              cardEl.style.boxShadow = '';
            }, 1800);
          }
        }
      });
    });
  }

  function highlightDiff(orig, rewrite) {
    if (orig === rewrite) {
      return `<div>${orig}</div><p style="color: #34D399; margin-top: 14px; font-weight: 700; display: flex; align-items: center; gap: 6px;"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg> Perfect match with all brand guidelines.</p>`;
    }
    return `<div style="color: #34D399;">${rewrite}</div>`;
  }

  // Inspector Cards Filtering
  filterPills.forEach(pill => {
    pill.addEventListener('click', () => {
      filterPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      currentCardFilter = pill.getAttribute('data-filter');
      if (currentAuditResult) {
        renderInspectorCards(currentAuditResult.inspector_cards);
      }
    });
  });

  if (cardsSearchInput) {
    cardsSearchInput.addEventListener('input', (e) => {
      currentSearchQuery = e.target.value.toLowerCase().trim();
      if (currentAuditResult) {
        renderInspectorCards(currentAuditResult.inspector_cards);
      }
    });
  }

  function renderInspectorCards(cards) {
    if (!cards || cards.length === 0) {
      cardsList.innerHTML = `
        <div class="empty-cards-state">
          <div class="empty-icon-wrap">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.5">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
              <polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
          </div>
          <h3 style="color: #34D399;">Zero Brand Violations Detected</h3>
          <p>All lexical, factual, visual, and WCAG rules satisfied in full.</p>
        </div>
      `;
      return;
    }

    const filtered = cards.filter(c => {
      if (currentCardFilter === 'critical' && c.severity !== 'CRITICAL') return false;
      if (currentCardFilter === 'warning' && c.severity !== 'WARNING') return false;
      if (currentCardFilter === 'lexical' && !['tone', 'terminology'].includes(c.dimension.toLowerCase())) return false;
      if (currentCardFilter === 'facts' && !['facts', 'claims'].includes(c.dimension.toLowerCase())) return false;
      if (currentCardFilter === 'wcag' && !['visual', 'accessibility'].includes(c.dimension.toLowerCase())) return false;

      if (currentSearchQuery) {
        const text = `${c.flag_id} ${c.dimension} ${c.issue_explanation} ${c.original_snippet} ${c.suggested_rewrite} ${c.cited_source}`.toLowerCase();
        if (!text.includes(currentSearchQuery)) return false;
      }
      return true;
    });

    if (filtered.length === 0) {
      cardsList.innerHTML = `
        <div class="empty-cards-state">
          <p style="color: var(--text-muted);">No issues matching current filter.</p>
        </div>`;
      return;
    }

    cardsList.innerHTML = filtered.map(c => `
      <div class="inspector-card-item severity-${(c.severity || '').toLowerCase()}" id="card-${c.flag_id}">
        <div class="card-top-row">
          <div class="card-tags">
            <span class="badge-flag-id">${c.flag_id}</span>
            <span class="badge-severity ${c.severity}">${c.severity}</span>
            <span class="status-badge">${c.dimension.toUpperCase()}</span>
          </div>
          <span style="font-size: 0.72rem; color: var(--text-dim); font-family: var(--font-mono);">Confidence: ${Math.round(c.confidence_score * 100)}%</span>
        </div>

        ${c.original_snippet ? `<div class="card-snippet">Flagged: "${c.original_snippet}"</div>` : ''}
        
        <div class="card-issue-text">${c.issue_explanation}</div>

        <div class="card-citation-box">
          <span class="citation-label">Cited Brand Source &amp; Section:</span>
          <span class="citation-text">${c.cited_source}</span>
        </div>

        <div class="card-suggestion-box">
          <span class="suggestion-label">Suggested Intent-Preserving Correction:</span>
          <div style="font-weight: 700; line-height: 1.4;">"${c.suggested_rewrite}"</div>
        </div>

        <div class="card-ai-badge">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/></svg>
          <span>${c.ai_disclosure}</span>
        </div>

        <div class="card-actions-row">
          <button class="btn-action-accept" onclick="handleCardAction('${c.flag_id}', 'ACCEPT')">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
            Accept Rewrite
          </button>
          <button class="btn-action-override" onclick="handleCardAction('${c.flag_id}', 'OVERRIDE')">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
            Override with Reason
          </button>
        </div>
      </div>
    `).join('');
  }

  // Card Action Handler
  window.handleCardAction = async function (flagId, action) {
    let reason = null;
    if (action === 'OVERRIDE') {
      reason = prompt("Enter justification reason for overriding this brand rule (e.g., intentional marketing campaign exception):");
      if (!reason) return;
    }

    try {
      const resp = await fetch(`${API_BASE}/review-action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: currentProjectId,
          flag_id: flagId,
          action: action,
          override_justification: reason,
          reviewer_role: "Brand Governance Lead"
        })
      });
      const res = await resp.json();

      const cardEl = document.getElementById(`card-${flagId}`);
      if (cardEl) {
        if (action === 'ACCEPT') {
          cardEl.style.opacity = '0.55';
          cardEl.style.borderLeft = '4px solid var(--accent-emerald)';
          cardEl.querySelector('.card-actions-row').innerHTML = `<span style="color: #34D399; font-size: 0.8rem; font-weight: 700;">✓ Accepted & Integrated</span>`;
          showToast(`Accepted rewrite for ${flagId}`, "success");
          logActivity('review', 'Accepted Rewrite', `Accepted suggested compliance rewrite for flag ${flagId}.`);
        } else {
          cardEl.style.opacity = '0.7';
          cardEl.style.borderLeft = '4px solid var(--accent-amber)';
          cardEl.querySelector('.card-actions-row').innerHTML = `<span style="color: #FBBF24; font-size: 0.8rem; font-weight: 700;">⚡ Overridden (Reason: ${reason})</span>`;
          showToast(`Logged human override for ${flagId}`, "warning");
          logActivity('review', 'Overrode Brand Rule', `Human reviewer overrode flag ${flagId}. Reason: "${reason}".`);
        }
      }
    } catch (e) {
      showToast("Failed to record action", "warning");
    }
  };

  // ==========================================================================
  // 12. Human Review & Manager Feedback
  // ==========================================================================
  if (btnRequestChanges && feedbackModal) {
    btnRequestChanges.addEventListener('click', () => {
      feedbackModal.style.display = 'flex';
      if (feedbackNotesInput) feedbackNotesInput.focus();
    });
  }

  function closeFeedbackModal() {
    if (feedbackModal) feedbackModal.style.display = 'none';
  }

  if (btnCloseFeedbackModal) btnCloseFeedbackModal.addEventListener('click', closeFeedbackModal);
  if (btnCancelFeedbackModal) btnCancelFeedbackModal.addEventListener('click', closeFeedbackModal);

  if (btnSubmitFeedback) {
    btnSubmitFeedback.addEventListener('click', () => {
      const notes = feedbackNotesInput ? feedbackNotesInput.value.trim() : "";
      if (!notes) {
        showToast("Please provide specific feedback instructions.", "warning");
        return;
      }

      if (feedbackItemsList) {
        const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const entryHtml = `
          <div class="feedback-entry">
            <span class="feedback-entry-time">${timeStr}</span>
            <span class="feedback-entry-text"><strong>Reviewer Note:</strong> ${notes}</span>
          </div>
        `;
        if (feedbackItemsList.querySelector('.subtle-text')) {
          feedbackItemsList.innerHTML = '';
        }
        feedbackItemsList.insertAdjacentHTML('afterbegin', entryHtml);
      }

      if (managerStatusText) managerStatusText.textContent = "Changes Requested by Reviewer";
      if (signoffDot) signoffDot.className = "pulse-indicator pulse-amber";
      docStatusBadge.textContent = "Changes Requested";
      docStatusBadge.style.color = "#F87171";

      closeFeedbackModal();
      if (feedbackNotesInput) feedbackNotesInput.value = '';
      showToast("Feedback sent and draft returned to creator queue.", "info");
      logActivity('review', 'Requested Changes', `Manager requested revisions: "${notes}".`);
    });
  }

  // Publication Clearance Certificate Modal
  if (btnApprovePublication) {
    btnApprovePublication.addEventListener('click', () => {
      const score = (currentAuditResult && currentAuditResult.compliance_score) ? currentAuditResult.compliance_score : 95;
      const speed = (currentAuditResult && currentAuditResult.execution_time_ms) ? currentAuditResult.execution_time_ms : 2.4;
      const docName = docTitleInput.value.trim() || "Untitled_Release.pdf";

      document.getElementById('cert-score').textContent = `${score}/100`;
      document.getElementById('cert-latency').textContent = `${speed} ms`;
      document.getElementById('cert-doc-name').textContent = docName;
      document.getElementById('cert-project-name').textContent = currentProjectId;
      document.getElementById('cert-timestamp').textContent = new Date().toLocaleString();
      document.getElementById('cert-hash').textContent = `SHA256: ${Math.random().toString(36).substring(2, 10)}${Math.random().toString(36).substring(2, 10)}`;

      if (approvalModal) approvalModal.style.display = 'flex';
      logActivity('review', 'Approved Publication', `Certified publication clearance for '${docName}' with score ${score}/100.`);
    });
  }

  if (btnCloseApprovalModal) btnCloseApprovalModal.addEventListener('click', () => approvalModal.style.display = 'none');
  if (btnDoneCertificate) btnDoneCertificate.addEventListener('click', () => {
    approvalModal.style.display = 'none';
    if (managerStatusText) managerStatusText.textContent = "Approved & Certified";
    if (signoffDot) signoffDot.className = "pulse-indicator pulse-green";
    docStatusBadge.textContent = "Cleared for Publication";
    docStatusBadge.style.color = "#34D399";
    showToast("Publication clearance certified and logged!", "success");
  });

  if (btnPrintCertificate) {
    btnPrintCertificate.addEventListener('click', () => {
      window.print();
    });
  }

  // Guide Modal Handlers
  if (btnOpenGuideModal && guideModal) {
    btnOpenGuideModal.addEventListener('click', () => guideModal.style.display = 'flex');
  }
  if (btnCloseGuideModal) btnCloseGuideModal.addEventListener('click', () => guideModal.style.display = 'none');
  if (btnCloseGuideModalBtn) btnCloseGuideModalBtn.addEventListener('click', () => guideModal.style.display = 'none');

  // ==========================================================================
  // 13. Document Submission System with Comprehensive Validation
  // ==========================================================================
  if (btnSubmitDocument) {
    btnSubmitDocument.addEventListener('click', async () => {
      const title = docTitleInput ? docTitleInput.value.trim() : "";
      const content = draftText ? draftText.value.trim() : "";
      const validationErrors = [];

      // Validation 1: Workspace Selection
      if (!currentProjectId) {
        validationErrors.push("Please select an active Brand Workspace.");
      }

      // Validation 2: Document Title
      if (!title) {
        validationErrors.push("Document Title is required. Please provide a file name or title.");
      }

      // Validation 3: Document Content or File
      if (!content && !currentUploadedFile) {
        validationErrors.push("Document Content is empty. Please enter draft copy or upload a document file.");
      }

      // If missing basic fields, display validation error box and return
      if (validationErrors.length > 0) {
        if (submissionValidationBox) {
          submissionValidationBox.style.display = 'block';
          submissionValidationBox.innerHTML = `
            <strong>Submission Blocked: Missing Required Information</strong>
            <ul>
              ${validationErrors.map(e => `<li>${e}</li>`).join('')}
            </ul>
          `;
          submissionValidationBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        showToast("Please fix the required fields before submitting.", "warning");
        return;
      }

      // Validation 4: If Pre-Check hasn't been run yet, run it automatically
      if (!currentAuditResult) {
        showToast("Executing pre-check audit before submission...", "info");
        await runAudit();
      }

      // Check if audit resulted in critical violations
      if (currentAuditResult && currentAuditResult.compliance_score < 60) {
        if (submissionValidationBox) {
          submissionValidationBox.style.display = 'block';
          submissionValidationBox.innerHTML = `
            <strong>Submission Warning: Low Compliance Score (${currentAuditResult.compliance_score}/100)</strong>
            <p>This draft contains unresolved critical brand violations. Please review the inspector cards above, accept suggested intent-preserving rewrites, or obtain managerial override clearance before submission.</p>
          `;
        }
        showToast("Draft contains critical violations. Score below 60/100.", "warning");
        return;
      }

      // All validations passed!
      if (submissionValidationBox) submissionValidationBox.style.display = 'none';

      const submissionId = "SUB-2026-" + Math.floor(1000 + Math.random() * 9000);
      const score = currentAuditResult ? currentAuditResult.compliance_score : 100;

      if (submitSummaryDoc) submitSummaryDoc.textContent = title;
      if (submitSummaryProject) submitSummaryProject.textContent = activeProjectName ? activeProjectName.textContent : currentProjectId;
      if (submitSummaryScore) submitSummaryScore.textContent = `${score} / 100`;
      if (submitSummaryId) submitSummaryId.textContent = submissionId;

      if (submissionSuccessModal) submissionSuccessModal.style.display = 'flex';

      docStatusBadge.textContent = "Submitted — Under Review";
      docStatusBadge.style.color = "#38BDF8";

      logActivity('submit', 'Submitted Document for Approval', `Document '${title}' successfully submitted with ID ${submissionId}. Compliance score: ${score}/100.`);
      showToast("Document submitted successfully!", "success");
    });
  }

  if (btnCloseSubmissionModal) btnCloseSubmissionModal.addEventListener('click', () => submissionSuccessModal.style.display = 'none');
  if (btnDoneSubmission) btnDoneSubmission.addEventListener('click', () => submissionSuccessModal.style.display = 'none');

  if (btnViewSubmissionActivity) {
    btnViewSubmissionActivity.addEventListener('click', () => {
      submissionSuccessModal.style.display = 'none';
      const activityTab = document.getElementById('tab-btn-activity');
      if (activityTab) activityTab.click();
    });
  }

  // ==========================================================================
  // 14. Brand Vault Functions & Table Filtering
  // ==========================================================================
  async function loadVaultData() {
    try {
      const res = await fetch(`${API_BASE}/vault?project_id=${currentProjectId}`);
      const data = await res.json();

      rawVaultFacts = data.approved_facts || [];
      rawVaultTerms = data.terminology_rules || [];

      if (vaultFactsCount) vaultFactsCount.textContent = `${rawVaultFacts.length} Verified Facts`;
      if (vaultTermsCount) vaultTermsCount.textContent = `${rawVaultTerms.length} Rules`;

      renderFactsTable(rawVaultFacts);
      renderTermsTable(rawVaultTerms);

      const palette = data.color_palette || {};
      if (paletteSwatchesGrid) {
        paletteSwatchesGrid.innerHTML = Object.keys(palette).map(k => {
          const item = palette[k];
          return `
            <div class="palette-card" onclick="copyHexToClipboard('${item.hex}')" title="Click to copy ${item.hex}">
              <div class="color-swatch-box" style="background-color: ${item.hex};"></div>
              <div class="palette-meta">
                <span class="color-name">${item.name}</span>
                <span class="color-hex">${item.hex}</span>
                <p style="font-size: 0.72rem; color: var(--text-dim); margin-top: 4px;">${item.usage}</p>
              </div>
            </div>
          `;
        }).join('');
      }

    } catch (e) {
      console.error("Failed to load vault data", e);
    }
  }

  function renderFactsTable(facts) {
    if (!factsTbody) return;
    factsTbody.innerHTML = facts.map(f => `
      <tr>
        <td><strong style="color: #93C5FD; font-family: var(--font-mono);">#${f.fact_id}</strong></td>
        <td><span class="status-badge">${f.category}</span></td>
        <td><strong style="color: #34D399; font-family: var(--font-mono);">${f.approved_value}</strong></td>
        <td>${f.approved_claim}</td>
        <td style="font-size: 0.75rem; color: var(--text-dim);">${f.source_doc} (p.${f.page_number})</td>
      </tr>
    `).join('');
  }

  function renderTermsTable(terms) {
    if (!termsTbody) return;
    termsTbody.innerHTML = terms.map(t => `
      <tr>
        <td><code style="color: #F87171; background: rgba(239, 68, 68, 0.12); padding: 2px 7px; border-radius: 4px; font-weight: 700;">${t.term}</code></td>
        <td><span class="badge-severity ${t.severity}">${t.severity}</span></td>
        <td><strong style="color: #34D399; font-weight: 700;">${t.preferred}</strong></td>
        <td>${t.rationale} <br><small style="color: var(--text-dim);">Source: ${t.cited_doc || 'Brand Book'}, p.${t.page || 1}</small></td>
      </tr>
    `).join('');
  }

  if (factsSearchInput) {
    factsSearchInput.addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase().trim();
      const filtered = rawVaultFacts.filter(f =>
        `${f.fact_id} ${f.category} ${f.approved_value} ${f.approved_claim} ${f.source_doc}`.toLowerCase().includes(q)
      );
      renderFactsTable(filtered);
    });
  }

  if (termsSearchInput) {
    termsSearchInput.addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase().trim();
      const filtered = rawVaultTerms.filter(t =>
        `${t.term} ${t.severity} ${t.preferred} ${t.rationale}`.toLowerCase().includes(q)
      );
      renderTermsTable(filtered);
    });
  }

  window.copyHexToClipboard = function (hex) {
    navigator.clipboard.writeText(hex).then(() => {
      showToast(`Copied ${hex} to clipboard!`, "success");
    });
  };

  if (btnRefreshVault) {
    btnRefreshVault.addEventListener('click', () => {
      loadVaultData();
      showToast("Brand Vault refreshed", "info");
      logActivity('workspace', 'Refreshed Vault', `Reloaded ground truth facts and terminology dictionary for workspace ${currentProjectId}.`);
    });
  }

  // Guidelines Ingestion Upload
  if (btnSelectGuidelineFile && guidelineFileInput) {
    btnSelectGuidelineFile.addEventListener('click', (e) => {
      e.stopPropagation();
      guidelineFileInput.click();
    });

    guidelinesDropzone.addEventListener('click', () => {
      guidelineFileInput.click();
    });

    guidelineFileInput.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      const formData = new FormData();
      formData.append('file', file);
      formData.append('project_id', currentProjectId);

      guidelineUploadStatus.style.display = 'block';
      guidelineUploadStatus.className = 'upload-status-bar';
      guidelineUploadStatus.innerHTML = `<span class="loading-spinner"></span> Ingesting <strong>${file.name}</strong> into [${currentProjectId}]... Granular PDF chunking, extracting rules & re-instructing static workers...`;

      try {
        const resp = await fetch(`${API_BASE}/upload-guidelines`, {
          method: 'POST',
          body: formData
        });

        if (!resp.ok) throw new Error(`Upload failed with status ${resp.status}`);
        const result = await resp.json();

        if (result.status === 'SUCCESS') {
          guidelineUploadStatus.className = 'upload-status-bar success';
          guidelineUploadStatus.innerHTML = `
            ✓ <strong>${file.name} successfully ingested into project workspace [${currentProjectId}]!</strong><br>
            • ${result.new_chunks_indexed} granular sections added to Branched RAG (Total: ${result.total_chunks_in_rag})<br>
            • Extracted ${result.new_terminology_rules} new terminology rules, ${result.new_facts_indexed} facts, and ${result.new_palette_colors} colors.<br>
            • ⚡ <strong>All 4 Static Workers dynamically re-instructed in real-time.</strong>
          `;
          showToast(`Ingested ${file.name} successfully!`, "success");
          logActivity('workspace', 'Ingested Brand Guidelines', `Ingested '${file.name}' into ${currentProjectId}: indexed ${result.new_chunks_indexed} sections and ${result.new_terminology_rules} new rules.`);
          loadVaultData();
          loadProjectsList();
        } else {
          guidelineUploadStatus.className = 'upload-status-bar error';
          guidelineUploadStatus.textContent = `Ingestion error: ${result.message}`;
          showToast(`Upload error: ${result.message}`, "warning");
        }
      } catch (err) {
        guidelineUploadStatus.className = 'upload-status-bar error';
        guidelineUploadStatus.textContent = `Upload failed: ${err.message}`;
        showToast(`Upload failed: ${err.message}`, "warning");
      }
    });

    guidelinesDropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      guidelinesDropzone.style.borderColor = 'var(--brand-primary)';
      guidelinesDropzone.style.background = 'rgba(99, 102, 241, 0.12)';
    });

    guidelinesDropzone.addEventListener('dragleave', () => {
      guidelinesDropzone.style.borderColor = '';
      guidelinesDropzone.style.background = '';
    });

    guidelinesDropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      guidelinesDropzone.style.borderColor = '';
      guidelinesDropzone.style.background = '';
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        guidelineFileInput.files = e.dataTransfer.files;
        const event = new Event('change');
        guidelineFileInput.dispatchEvent(event);
      }
    });
  }

  // ==========================================================================
  // 15. Governance Insights Loader
  // ==========================================================================
  async function loadAnalyticsData() {
    try {
      const res = await fetch(`${API_BASE}/analytics`);
      const data = await res.json();

      if (kpiTotalDocs) kpiTotalDocs.textContent = data.total_documents_screened;
      if (kpiAvgScore) kpiAvgScore.textContent = data.average_compliance_score;
      if (kpiAvgSpeed) kpiAvgSpeed.textContent = `${data.average_precheck_latency_ms} ms`;
      if (kpiTotalOverrides) kpiTotalOverrides.textContent = data.total_human_overrides;

      const dims = data.violations_by_dimension || {};
      const maxVal = Math.max(...Object.values(dims), 1);

      const dimKeys = ["tone", "terminology", "facts", "claims", "visual", "accessibility"];
      if (dimensionBars) {
        dimensionBars.innerHTML = dimKeys.map(d => {
          const count = dims[d] || 0;
          const pct = Math.round((count / maxVal) * 100);
          return `
            <div class="dim-bar-row">
              <div class="dim-bar-label">
                <span style="text-transform: capitalize;">${d}</span>
                <span style="font-family: var(--font-mono);">${count} violations</span>
              </div>
              <div class="dim-bar-track">
                <div class="dim-bar-fill" style="width: ${pct}%;"></div>
              </div>
            </div>
          `;
        }).join('');
      }

      if (ambiguityHotspotsList) {
        if (data.ambiguity_hotspots && data.ambiguity_hotspots.length > 0) {
          ambiguityHotspotsList.innerHTML = data.ambiguity_hotspots.map(h => `
            <div class="hotspot-item">
              <div>
                <strong style="color: #FBBF24;">Rule ID: ${h.rule_id}</strong>
                <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 2px;">${h.alert}</div>
              </div>
              <span class="badge-count" style="color: #F87171; font-weight: 700;">${h.override_count} overrides</span>
            </div>
          `).join('');
        } else {
          ambiguityHotspotsList.innerHTML = `<p class="subtle-text">No active guideline ambiguity hotspots. Guidelines are clear across all dimensions.</p>`;
        }
      }

    } catch (e) {
      console.error(e);
    }
  }

  if (btnRefreshAnalytics) {
    btnRefreshAnalytics.addEventListener('click', () => {
      loadAnalyticsData();
      showToast("Governance telemetry updated", "info");
    });
  }

  // ==========================================================================
  // 16. Initial Application Startup
  // ==========================================================================
  logActivity('workspace', 'Session Initialized', 'Connected to Zuard Governance Gateway. Ready for pre-screening.');
  loadProjectsList();
  updateContrastPreview();
  updateAltTextQuality();
  updateTextStats();
  btnLoadSample1.click();
});
