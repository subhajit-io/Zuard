/**
 * Zuard Brand Governance Engine — Frontend Application Logic
 * Pure Vanilla JavaScript (Zero External Frameworks)
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Configuration & API Base Detection
  const API_BASE = (window.location.protocol === 'file:' || !window.location.host)
    ? 'http://127.0.0.1:8000/api'
    : `${window.location.origin}/api`;

  // Application State (Two-Sided Architecture)
  const state = {
    currentProject: 'zuard-enterprise',
    currentRole: localStorage.getItem('zuard_role_mode') || 'Creator', // 'Creator' | 'Reviewer'
    reviewerRole: 'Reviewer',
    currentAuditResponse: null,
    activityLog: [],
    modalTargetFlag: null,
    submissions: [],
    submissionStatusFilter: 'all',
    activeDecisionSubId: null,
    selectedDecisionAction: 'APPROVE'
  };

  // Sample Presets
  const SAMPLES = {
    violations: "Our #1 AI platform is super cheap and guaranteed to save you 99% on costs. Using our revolutionary miracle engine you'll crush your competition.",
    borderline: "The Zuard Enterprise Platform delivers 70% faster review cycles. Our legacy sync pipeline reduces errors.",
    clean: "Zuard's governance engine pre-screens drafts in 2.5 seconds, demonstrating a verified 42% average operational cost reduction (Study ID #F-104)."
  };

  // DOM Elements Cache
  const el = {
    // Nav
    tabs: document.querySelectorAll('.nav-tab'),
    tabPanels: document.querySelectorAll('.tab-panel'),
    projectSelector: document.getElementById('projectSelector'),
    reviewerRoleSelector: document.getElementById('reviewerRoleSelector'),
    engineStatusBadge: document.getElementById('engineStatusBadge'),
    engineStatusText: document.getElementById('engineStatusText'),
    toastContainer: document.getElementById('toastContainer'),

    // Review Tab - Editor
    documentTitleInput: document.getElementById('documentTitleInput'),
    draftContentInput: document.getElementById('draftContentInput'),
    wordCountBadge: document.getElementById('wordCountBadge'),
    loadSample1: document.getElementById('loadSample1'),
    loadSample2: document.getElementById('loadSample2'),
    loadSample3: document.getElementById('loadSample3'),
    privacyModeCheckbox: document.getElementById('privacyModeCheckbox'),
    btnClearDraft: document.getElementById('btnClearDraft'),
    btnRunAudit: document.getElementById('btnRunAudit'),
    auditSpinner: document.getElementById('auditSpinner'),

    // Review Tab - Scorecard
    scoreRingCircle: document.getElementById('scoreRingCircle'),
    complianceScoreValue: document.getElementById('complianceScoreValue'),
    auditStatusBadge: document.getElementById('auditStatusBadge'),
    auditLatencyBadge: document.getElementById('auditLatencyBadge'),
    totalViolationsCount: document.getElementById('totalViolationsCount'),
    engineLatencyValue: document.getElementById('engineLatencyValue'),
    privacyShieldLabel: document.getElementById('privacyShieldLabel'),
    readabilityGradeValue: document.getElementById('readabilityGradeValue'),

    // Worker Timings
    w1Time: document.getElementById('w1Time'),
    w2Time: document.getElementById('w2Time'),
    w3Time: document.getElementById('w3Time'),
    w4Time: document.getElementById('w4Time'),

    // Dimensions
    dimToneCount: document.getElementById('dimToneCount'),
    dimTermCount: document.getElementById('dimTermCount'),
    dimFactsCount: document.getElementById('dimFactsCount'),
    dimClaimsCount: document.getElementById('dimClaimsCount'),
    dimWcagCount: document.getElementById('dimWcagCount'),

    // Inspector
    inspectorCardsCount: document.getElementById('inspectorCardsCount'),
    inspectorCardsContainer: document.getElementById('inspectorCardsContainer'),

    // Diff / Rewrite
    annotatedMarkupView: document.getElementById('annotatedMarkupView'),
    suggestedRewriteView: document.getElementById('suggestedRewriteView'),
    btnCopyRewrite: document.getElementById('btnCopyRewrite'),
    btnApplyRewriteToEditor: document.getElementById('btnApplyRewriteToEditor'),

    // Brand Vault Tab
    btnRefreshVault: document.getElementById('btnRefreshVault'),
    guidelineDropzone: document.getElementById('guidelineDropzone'),
    guidelineFileInput: document.getElementById('guidelineFileInput'),
    vStatFacts: document.getElementById('vStatFacts'),
    vStatTerms: document.getElementById('vStatTerms'),
    vStatColors: document.getElementById('vStatColors'),
    vStatChunks: document.getElementById('vStatChunks'),
    factsTableBody: document.getElementById('factsTableBody'),
    factsCountBadge: document.getElementById('factsCountBadge'),
    termsTableBody: document.getElementById('termsTableBody'),
    termsCountBadge: document.getElementById('termsCountBadge'),
    paletteSwatchesContainer: document.getElementById('paletteSwatchesContainer'),

    // Projects Tab
    projectsGridContainer: document.getElementById('projectsGridContainer'),
    createProjectForm: document.getElementById('createProjectForm'),
    newProjectId: document.getElementById('newProjectId'),
    newProjectName: document.getElementById('newProjectName'),
    newProjectPersona: document.getElementById('newProjectPersona'),
    newProjectGuidelinesFile: document.getElementById('newProjectGuidelinesFile'),
    newProjectDesc: document.getElementById('newProjectDesc'),

    // Analytics Tab
    btnRefreshAnalytics: document.getElementById('btnRefreshAnalytics'),
    kpiTotalAudits: document.getElementById('kpiTotalAudits'),
    kpiAvgCompliance: document.getElementById('kpiAvgCompliance'),
    kpiAvgLatency: document.getElementById('kpiAvgLatency'),
    kpiTotalViolations: document.getElementById('kpiTotalViolations'),
    analyticsDimensionStats: document.getElementById('analyticsDimensionStats'),
    analyticsActionsStats: document.getElementById('analyticsActionsStats'),

    // Activity Tab
    activityStreamContainer: document.getElementById('activityStreamContainer'),
    btnClearActivity: document.getElementById('btnClearActivity'),

    // Modals
    editFlagModal: document.getElementById('editFlagModal'),
    editModalSnippetDesc: document.getElementById('editModalSnippetDesc'),
    editSnippetInput: document.getElementById('editSnippetInput'),
    btnCancelEditModal: document.getElementById('btnCancelEditModal'),
    btnSaveEditModal: document.getElementById('btnSaveEditModal'),
    btnCloseEditModal: document.getElementById('btnCloseEditModal'),

    overrideFlagModal: document.getElementById('overrideFlagModal'),
    overrideModalSnippetDesc: document.getElementById('overrideModalSnippetDesc'),
    overrideJustificationInput: document.getElementById('overrideJustificationInput'),
    btnCancelOverrideModal: document.getElementById('btnCancelOverrideModal'),
    btnSaveOverrideModal: document.getElementById('btnSaveOverrideModal'),
    btnCloseOverrideModal: document.getElementById('btnCloseOverrideModal'),

    // Two-Sided Role & Queue Elements
    brandSubtitle: document.getElementById('brandSubtitle'),
    btnRoleCreator: document.getElementById('btnRoleCreator'),
    btnRoleReviewer: document.getElementById('btnRoleReviewer'),
    headerQueueBadge: document.getElementById('headerQueueBadge'),
    tabReviewLabel: document.getElementById('tabReviewLabel'),
    tabQueueLabel: document.getElementById('tabQueueLabel'),
    tabQueueBadge: document.getElementById('tabQueueBadge'),
    btnRunAuditText: document.getElementById('btnRunAuditText'),
    btnOpenSubmitModal: document.getElementById('btnOpenSubmitModal'),

    // Queue Panel
    queuePanelHeading: document.getElementById('queuePanelHeading'),
    queuePanelSubheading: document.getElementById('queuePanelSubheading'),
    btnRefreshSubmissions: document.getElementById('btnRefreshSubmissions'),
    qKpiPending: document.getElementById('qKpiPending'),
    qKpiApproved: document.getElementById('qKpiApproved'),
    qKpiChanges: document.getElementById('qKpiChanges'),
    qKpiTotal: document.getElementById('qKpiTotal'),
    queueStatusFilterGroup: document.getElementById('queueStatusFilterGroup'),
    submissionsTableContainer: document.getElementById('submissionsTableContainer'),

    // Submit Draft Modal
    submitDraftModal: document.getElementById('submitDraftModal'),
    subCreatorNameInput: document.getElementById('subCreatorNameInput'),
    subTitleInput: document.getElementById('subTitleInput'),
    subNotesInput: document.getElementById('subNotesInput'),
    modalPreScore: document.getElementById('modalPreScore'),
    modalPreViolations: document.getElementById('modalPreViolations'),
    modalPreWorkspace: document.getElementById('modalPreWorkspace'),
    btnCloseSubmitModal: document.getElementById('btnCloseSubmitModal'),
    btnCancelSubmitModal: document.getElementById('btnCancelSubmitModal'),
    btnConfirmSubmitDraft: document.getElementById('btnConfirmSubmitDraft'),

    // Decision Modal
    reviewDecisionModal: document.getElementById('reviewDecisionModal'),
    decSubId: document.getElementById('decSubId'),
    decCreator: document.getElementById('decCreator'),
    decWorkspace: document.getElementById('decWorkspace'),
    decStatusBadge: document.getElementById('decStatusBadge'),
    decCreatorNotes: document.getElementById('decCreatorNotes'),
    decContentPreview: document.getElementById('decContentPreview'),
    btnDecApproveTab: document.getElementById('btnDecApproveTab'),
    btnDecChangesTab: document.getElementById('btnDecChangesTab'),
    btnDecOverrideTab: document.getElementById('btnDecOverrideTab'),
    decReviewerNameInput: document.getElementById('decReviewerNameInput'),
    decFeedbackInput: document.getElementById('decFeedbackInput'),
    decFeedbackLabel: document.getElementById('decFeedbackLabel'),
    btnCloseDecisionModal: document.getElementById('btnCloseDecisionModal'),
    btnInspectInStudio: document.getElementById('btnInspectInStudio'),
    btnSubmitDecision: document.getElementById('btnSubmitDecision')
  };

  // =========================================================================
  // Toast Notifications
  // =========================================================================
  function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let iconSvg = '';
    if (type === 'success') {
      iconSvg = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>';
    } else if (type === 'error') {
      iconSvg = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>';
    } else {
      iconSvg = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>';
    }

    toast.innerHTML = `${iconSvg}<span>${escapeHtml(message)}</span>`;
    el.toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 250);
    }, 3500);
  }

  function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  // =========================================================================
  // Activity Logging
  // =========================================================================
  function logActivity(actionType, title, meta) {
    const item = {
      timestamp: new Date().toLocaleTimeString(),
      type: actionType,
      title: title,
      meta: meta
    };
    state.activityLog.unshift(item);
    renderActivityStream();
  }

  function renderActivityStream() {
    if (!el.activityStreamContainer) return;
    if (state.activityLog.length === 0) {
      el.activityStreamContainer.innerHTML = `
        <div class="empty-state-card">
          <p class="empty-state-title">No actions recorded yet</p>
          <p class="empty-state-desc">Run audits or accept/edit flags on the Review tab to view the live activity stream.</p>
        </div>`;
      return;
    }

    el.activityStreamContainer.innerHTML = state.activityLog.map(item => `
      <div class="activity-item">
        <span class="activity-time">${item.timestamp}</span>
        <div class="activity-content">
          <div class="activity-title">
            <span class="badge ${getActivityBadgeClass(item.type)}">${item.type}</span>
            <span>${escapeHtml(item.title)}</span>
          </div>
          <div class="activity-meta">${escapeHtml(item.meta)}</div>
        </div>
      </div>
    `).join('');
  }

  function getActivityBadgeClass(type) {
    switch (type) {
      case 'AUDIT': return 'badge-accent';
      case 'ACCEPT': return 'badge-success';
      case 'EDIT': return 'badge-warning';
      case 'OVERRIDE': return 'badge-danger';
      case 'INGEST': return 'badge-accent';
      default: return 'badge-neutral';
    }
  }

  // =========================================================================
  // Tab Navigation
  // =========================================================================
  function switchTab(tabId) {
    el.tabs.forEach(tab => {
      const isActive = tab.getAttribute('data-tab') === tabId;
      tab.classList.toggle('active', isActive);
      tab.setAttribute('aria-selected', isActive ? 'true' : 'false');
    });

    el.tabPanels.forEach(panel => {
      panel.classList.toggle('active', panel.id === `tab-${tabId}`);
    });

    if (tabId === 'queue') {
      loadSubmissions();
      loadSubmissionStats();
    }
    if (tabId === 'vault') loadVaultData();
    if (tabId === 'projects') loadProjects();
    if (tabId === 'analytics') loadAnalytics();
    if (tabId === 'activity') renderActivityStream();
  }

  el.tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const tabId = tab.getAttribute('data-tab');
      switchTab(tabId);
    });
  });

  // =========================================================================
  // Server Health & Status Check
  // =========================================================================
  async function checkServerHealth() {
    try {
      const res = await fetch(`${API_BASE}/health`);
      if (res.ok) {
        const data = await res.json();
        el.engineStatusBadge.className = 'status-indicator-badge online';
        el.engineStatusText.textContent = `${data.service} • ${data.privacy_mode}`;
      } else {
        throw new Error(`Server returned ${res.status}`);
      }
    } catch (err) {
      el.engineStatusBadge.className = 'status-indicator-badge offline';
      el.engineStatusText.textContent = 'Backend Offline';
      console.warn('Health check failed:', err);
    }
  }

  // =========================================================================
  // Workspace / Project Selector
  // =========================================================================
  async function loadProjectsDropdown() {
    try {
      const res = await fetch(`${API_BASE}/projects`);
      if (!res.ok) return;
      const projects = await res.json();
      
      el.projectSelector.innerHTML = '';
      projects.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.project_id;
        opt.textContent = `${p.name} (${p.project_id})`;
        if (p.project_id === state.currentProject) {
          opt.selected = true;
        }
        el.projectSelector.appendChild(opt);
      });
    } catch (err) {
      console.error('Failed to load projects list for dropdown:', err);
    }
  }

  el.projectSelector.addEventListener('change', (e) => {
    state.currentProject = e.target.value;
    showToast(`Workspace switched to: ${state.currentProject}`, 'info');
    loadVaultData();
    logActivity('SWITCH', `Workspace changed to ${state.currentProject}`, `User: ${state.reviewerRole}`);
  });

  if (el.reviewerRoleSelector) {
    el.reviewerRoleSelector.addEventListener('change', (e) => {
      state.reviewerRole = e.target.value;
      showToast(`Reviewer role: ${state.reviewerRole}`, 'info');
    });
  }

  // =========================================================================
  // Editor & Sample Text Buttons
  // =========================================================================
  function updateWordCount() {
    const text = el.draftContentInput.value.trim();
    const words = text ? text.split(/\s+/).length : 0;
    el.wordCountBadge.textContent = `${words} word${words === 1 ? '' : 's'}`;
  }

  el.draftContentInput.addEventListener('input', updateWordCount);

  function loadSample(sampleText, title) {
    el.draftContentInput.value = sampleText;
    el.documentTitleInput.value = title;
    updateWordCount();
    showToast(`Loaded: ${title}`, 'info');
  }

  el.loadSample1.addEventListener('click', () => {
    loadSample(SAMPLES.violations, 'High-Risk Marketing Draft (Violations)');
  });

  el.loadSample2.addEventListener('click', () => {
    loadSample(SAMPLES.borderline, 'Enterprise Launch Note (Borderline)');
  });

  el.loadSample3.addEventListener('click', () => {
    loadSample(SAMPLES.clean, 'Empirical Evidence Whitepaper (Clean)');
  });

  el.btnClearDraft.addEventListener('click', () => {
    el.draftContentInput.value = '';
    updateWordCount();
    showToast('Draft cleared', 'info');
  });

  // =========================================================================
  // Run Audit
  // =========================================================================
  async function runAudit() {
    const content = el.draftContentInput.value.trim();
    if (!content) {
      showToast('Please enter or load draft text to audit.', 'error');
      el.draftContentInput.focus();
      return;
    }

    const payload = {
      project_id: state.currentProject,
      document_title: el.documentTitleInput.value.trim() || 'Untitled_Draft',
      content_text: content,
      privacy_mode: el.privacyModeCheckbox.checked
    };

    // UI Loading state
    el.btnRunAudit.disabled = true;
    el.auditSpinner.classList.remove('hidden');

    try {
      const res = await fetch(`${API_BASE}/audit-content`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errDetail = await res.text();
        throw new Error(`Audit failed (${res.status}): ${errDetail}`);
      }

      const auditData = await res.json();
      state.currentAuditResponse = auditData;
      renderAuditResults(auditData);
      showToast(`Audit completed in ${auditData.execution_time_ms.toFixed(1)} ms`, 'success');
      logActivity(
        'AUDIT',
        `Audited "${auditData.document_title}"`,
        `Score: ${auditData.compliance_score}/100 • ${auditData.total_violations_count} flag(s) • ${auditData.execution_time_ms.toFixed(1)}ms`
      );
    } catch (err) {
      console.error('Audit execution error:', err);
      showToast(`Audit error: ${err.message}`, 'error');
    } finally {
      el.btnRunAudit.disabled = false;
      el.auditSpinner.classList.add('hidden');
    }
  }

  el.btnRunAudit.addEventListener('click', runAudit);

  // =========================================================================
  // Render Audit Results
  // =========================================================================
  function renderAuditResults(data) {
    // 1. Update Score Ring
    const score = Math.max(0, Math.min(100, data.compliance_score || 0));
    el.complianceScoreValue.textContent = score;

    const circumference = 2 * Math.PI * 48; // ~301.59
    const offset = circumference - (score / 100) * circumference;
    el.scoreRingCircle.style.strokeDashoffset = offset;

    if (score >= 85) {
      el.scoreRingCircle.style.stroke = 'var(--color-green)';
    } else if (score >= 60) {
      el.scoreRingCircle.style.stroke = 'var(--color-amber)';
    } else {
      el.scoreRingCircle.style.stroke = 'var(--color-red)';
    }

    // 2. Badges & Metrics
    el.auditLatencyBadge.textContent = `${data.execution_time_ms.toFixed(1)} ms`;
    el.engineLatencyValue.textContent = `${data.execution_time_ms.toFixed(1)} ms`;
    el.totalViolationsCount.textContent = data.total_violations_count;
    el.privacyShieldLabel.textContent = data.privacy_mode || 'Local Edge Mode';

    // Status Badge
    el.auditStatusBadge.textContent = (data.status || 'IN_REVIEW').replace(/_/g, ' ');
    el.auditStatusBadge.className = 'badge ' + (
      data.status === 'APPROVED' ? 'badge-success' :
      data.status === 'WARNINGS_DETECTED' ? 'badge-warning' : 'badge-danger'
    );

    // Readability
    if (data.metrics && data.metrics.readability) {
      const r = data.metrics.readability;
      el.readabilityGradeValue.textContent = `Grade ${r.flesch_kincaid_grade || '--'} (Ease: ${r.flesch_reading_ease || '--'})`;
    } else {
      el.readabilityGradeValue.textContent = '--';
    }

    // 3. Parallel Worker Timing Chips
    if (data.worker_latencies_ms) {
      el.w1Time.textContent = `${(data.worker_latencies_ms.worker_1_lexical_ms || 0).toFixed(1)} ms`;
      el.w2Time.textContent = `${(data.worker_latencies_ms.worker_2_facts_ms || 0).toFixed(1)} ms`;
      el.w3Time.textContent = `${(data.worker_latencies_ms.worker_3_visual_ms || 0).toFixed(1)} ms`;
      el.w4Time.textContent = `${(data.worker_latencies_ms.worker_4_wcag_ms || 0).toFixed(1)} ms`;
    }

    // 4. Dimension Breakdown
    if (data.dimension_breakdown) {
      el.dimToneCount.textContent = data.dimension_breakdown.tone || 0;
      el.dimTermCount.textContent = data.dimension_breakdown.terminology || 0;
      el.dimFactsCount.textContent = data.dimension_breakdown.facts || 0;
      el.dimClaimsCount.textContent = data.dimension_breakdown.claims || 0;
      el.dimWcagCount.textContent = (data.dimension_breakdown.accessibility || 0) + (data.dimension_breakdown.visual || 0);
    }

    // 5. Inspector Cards
    renderInspectorCards(data.inspector_cards || []);

    // 6. Diff & Suggested Rewrite Views
    renderDiffViews(data);
  }

  // =========================================================================
  // Inspector Cards Rendering & Actions
  // =========================================================================
  function renderInspectorCards(cards) {
    el.inspectorCardsCount.textContent = `${cards.length} Flag${cards.length === 1 ? '' : 's'} Found`;

    if (!cards || cards.length === 0) {
      el.inspectorCardsContainer.innerHTML = `
        <div class="empty-state-card">
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2" class="empty-state-icon">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            <path d="m9 12 2 2 4-4"/>
          </svg>
          <p class="empty-state-title">100% Brand Compliant</p>
          <p class="empty-state-desc">No terminology violations, unsubstantiated claims, or tone issues were detected by the 4 deterministic workers.</p>
        </div>`;
      return;
    }

    el.inspectorCardsContainer.innerHTML = cards.map((card, index) => {
      const sevClass = card.severity === 'CRITICAL' ? 'severity-CRITICAL' :
                       card.severity === 'WARNING' ? 'severity-WARNING' : 'severity-INFO';
      const sevBadge = card.severity === 'CRITICAL' ? 'badge-danger' :
                       card.severity === 'WARNING' ? 'badge-warning' : 'badge-accent';

      const isResolved = card.status && card.status !== 'PENDING';

      return `
        <div class="inspector-card ${sevClass} ${isResolved ? 'resolved' : ''}" id="card-${card.flag_id}">
          <div class="card-top-meta">
            <div class="meta-badges">
              <span class="flag-id-badge">${escapeHtml(card.flag_id)}</span>
              <span class="badge ${sevBadge}">${escapeHtml(card.severity)}</span>
              <span class="badge badge-neutral">${escapeHtml(card.dimension)}</span>
              <span class="badge badge-neutral">Conf: ${(card.confidence_score * 100).toFixed(0)}%</span>
            </div>
            <div class="status-tag">
              Status: <span id="status-tag-${card.flag_id}" class="text-accent">${escapeHtml(card.status || 'PENDING')}</span>
            </div>
          </div>

          <div class="card-body-content">
            <div class="snippet-block">
              <div class="snippet-label">Flagged Text Snippet</div>
              <div class="flagged-snippet-text">${escapeHtml(card.original_snippet)}</div>
              ${card.context_sentence ? `<div class="context-sentence">"${escapeHtml(card.context_sentence)}"</div>` : ''}
            </div>

            <div class="snippet-block">
              <div class="snippet-label">Issue &amp; Recommended Delta</div>
              <div class="issue-explanation-text">${escapeHtml(card.issue_explanation)}</div>
              <div class="suggested-snippet-text">${escapeHtml(card.suggested_rewrite)}</div>
            </div>
          </div>

          <div class="card-citations-row">
            <div class="citation-item">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="citation-icon"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
              <span><strong>Citation:</strong> ${escapeHtml(card.cited_source)}</span>
            </div>
            <div class="citation-item">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="citation-icon"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
              <span><strong>Verification:</strong> ${escapeHtml(card.ai_disclosure)}</span>
            </div>
          </div>

          <div class="card-footer-actions">
            <div class="text-muted" style="font-size: 0.75rem;">
              Allowed Actions: ${card.allowed_actions.join(', ')}
            </div>
            <div class="btn-actions-group">
              <button type="button" class="btn btn-success small" onclick="handleCardAction('${card.flag_id}', 'ACCEPT')">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>
                Accept
              </button>
              <button type="button" class="btn btn-secondary small" onclick="openEditModal('${card.flag_id}')">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
                Edit
              </button>
              <button type="button" class="btn btn-warning small" onclick="openOverrideModal('${card.flag_id}')">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                Override
              </button>
            </div>
          </div>
        </div>
      `;
    }).join('');
  }

  // Window-accessible action handlers
  window.handleCardAction = async function(flagId, action, extraPayload = {}) {
    const cardObj = (state.currentAuditResponse?.inspector_cards || []).find(c => c.flag_id === flagId);
    const cardEl = document.getElementById(`card-${flagId}`);
    const statusTag = document.getElementById(`status-tag-${flagId}`);

    const payload = {
      project_id: state.currentProject,
      flag_id: flagId,
      action: action,
      reviewer_role: state.reviewerRole,
      ...extraPayload
    };

    try {
      const res = await fetch(`${API_BASE}/review-action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) throw new Error(`Action failed with code ${res.status}`);
      const data = await res.json();

      if (statusTag) {
        statusTag.textContent = action;
        statusTag.className = action === 'ACCEPT' ? 'text-green' : action === 'EDIT' ? 'text-amber' : 'text-red';
      }
      if (cardEl) {
        cardEl.classList.add('resolved');
      }

      showToast(`Flag ${flagId} recorded as ${action}`, 'success');
      logActivity(action, `Flag ${flagId} ${action}`, `Role: ${state.reviewerRole} • Project: ${state.currentProject}`);

      // If user accepted, automatically apply replacement to the draft editor
      if (action === 'ACCEPT' && cardObj) {
        replaceInDraft(cardObj.original_snippet, cardObj.suggested_rewrite);
      } else if (action === 'EDIT' && extraPayload.edited_text && cardObj) {
        replaceInDraft(cardObj.original_snippet, extraPayload.edited_text);
      }

    } catch (err) {
      console.error('Failed to submit review action:', err);
      showToast(`Action failed: ${err.message}`, 'error');
    }
  };

  function replaceInDraft(target, replacement) {
    const current = el.draftContentInput.value;
    if (current.includes(target)) {
      el.draftContentInput.value = current.replace(target, replacement);
      updateWordCount();
      showToast(`Updated editor draft with replacement: "${replacement}"`, 'info');
    }
  }

  // =========================================================================
  // Edit & Override Modals
  // =========================================================================
  window.openEditModal = function(flagId) {
    const card = (state.currentAuditResponse?.inspector_cards || []).find(c => c.flag_id === flagId);
    if (!card) return;
    state.modalTargetFlag = card;
    el.editModalSnippetDesc.innerHTML = `Original snippet: <code class="flagged-snippet-text">${escapeHtml(card.original_snippet)}</code>`;
    el.editSnippetInput.value = card.suggested_rewrite;
    el.editFlagModal.classList.remove('hidden');
    el.editSnippetInput.focus();
  };

  function closeEditModal() {
    el.editFlagModal.classList.add('hidden');
    state.modalTargetFlag = null;
  }
  el.btnCancelEditModal.addEventListener('click', closeEditModal);
  el.btnCloseEditModal.addEventListener('click', closeEditModal);

  el.btnSaveEditModal.addEventListener('click', () => {
    if (!state.modalTargetFlag) return;
    const newText = el.editSnippetInput.value.trim();
    if (!newText) {
      showToast('Please provide a replacement rewrite.', 'error');
      return;
    }
    const flagId = state.modalTargetFlag.flag_id;
    closeEditModal();
    window.handleCardAction(flagId, 'EDIT', { edited_text: newText });
  });

  window.openOverrideModal = function(flagId) {
    const card = (state.currentAuditResponse?.inspector_cards || []).find(c => c.flag_id === flagId);
    if (!card) return;
    state.modalTargetFlag = card;
    el.overrideModalSnippetDesc.innerHTML = `Flagged violation: <code class="flagged-snippet-text">${escapeHtml(card.original_snippet)}</code> (${card.dimension})`;
    el.overrideJustificationInput.value = '';
    el.overrideFlagModal.classList.remove('hidden');
    el.overrideJustificationInput.focus();
  };

  function closeOverrideModal() {
    el.overrideFlagModal.classList.add('hidden');
    state.modalTargetFlag = null;
  }
  el.btnCancelOverrideModal.addEventListener('click', closeOverrideModal);
  el.btnCloseOverrideModal.addEventListener('click', closeOverrideModal);

  el.btnSaveOverrideModal.addEventListener('click', () => {
    if (!state.modalTargetFlag) return;
    const justification = el.overrideJustificationInput.value.trim();
    if (!justification) {
      showToast('Justification is required to override governance rules.', 'error');
      return;
    }
    const flagId = state.modalTargetFlag.flag_id;
    closeOverrideModal();
    window.handleCardAction(flagId, 'OVERRIDE', { override_justification: justification });
  });

  // =========================================================================
  // Diff Views Rendering
  // =========================================================================
  function renderDiffViews(data) {
    // 1. Annotated markup view
    if (data.flagged_draft_markup) {
      el.annotatedMarkupView.innerHTML = data.flagged_draft_markup;
    } else if (data.original_text) {
      // Build highlighted markup manually from inspector cards if not supplied
      let markup = escapeHtml(data.original_text);
      (data.inspector_cards || []).forEach(card => {
        const cls = card.severity === 'CRITICAL' ? 'severity-critical' : 'severity-warning';
        const escaped = escapeHtml(card.original_snippet);
        markup = markup.replace(new RegExp(escaped, 'g'), `<span class="flag-hl ${cls}">${escaped}</span>`);
      });
      el.annotatedMarkupView.innerHTML = markup;
    } else {
      el.annotatedMarkupView.innerHTML = '<span class="placeholder-text">No text available</span>';
    }

    // 2. Synthesized compliant rewrite
    if (data.suggested_full_rewrite) {
      el.suggestedRewriteView.textContent = data.suggested_full_rewrite;
    } else {
      el.suggestedRewriteView.innerHTML = '<span class="placeholder-text">All checks passed — original text is fully compliant.</span>';
    }
  }

  el.btnCopyRewrite.addEventListener('click', () => {
    const rewriteText = el.suggestedRewriteView.textContent.trim();
    if (!rewriteText || rewriteText.includes('Synthesized compliant rewrite will appear')) {
      showToast('No rewrite available to copy.', 'error');
      return;
    }
    navigator.clipboard.writeText(rewriteText).then(() => {
      showToast('Synthesized rewrite copied to clipboard!', 'success');
    }).catch(err => {
      showToast('Failed to copy to clipboard', 'error');
    });
  });

  el.btnApplyRewriteToEditor.addEventListener('click', () => {
    const rewriteText = el.suggestedRewriteView.textContent.trim();
    if (!rewriteText || rewriteText.includes('Synthesized compliant rewrite will appear')) {
      showToast('No rewrite available to use.', 'error');
      return;
    }
    el.draftContentInput.value = rewriteText;
    updateWordCount();
    showToast('Applied synthesized rewrite to draft editor.', 'success');
    logActivity('REPLACE', 'Applied synthesized rewrite to editor', `Document: ${el.documentTitleInput.value}`);
  });

  // =========================================================================
  // Brand Vault Tab Operations
  // =========================================================================
  async function loadVaultData() {
    try {
      el.factsTableBody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-4">Fetching Brand Vault data...</td></tr>';
      el.termsTableBody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-4">Fetching terminology rules...</td></tr>';

      const res = await fetch(`${API_BASE}/vault?project_id=${encodeURIComponent(state.currentProject)}`);
      if (!res.ok) throw new Error(`Vault request failed (${res.status})`);
      const vault = await res.json();

      // Stats
      const summary = vault.summary || {};
      el.vStatFacts.textContent = summary.total_approved_facts ?? (vault.approved_facts?.length || 0);
      el.vStatTerms.textContent = summary.total_terminology_rules ?? (vault.terminology_rules?.length || 0);
      el.vStatColors.textContent = summary.total_colors ?? Object.keys(vault.color_palette || {}).length;
      el.vStatChunks.textContent = summary.rag_chunk_count ?? '--';

      // Facts Table
      const facts = vault.approved_facts || [];
      el.factsCountBadge.textContent = `${facts.length} Facts`;
      if (facts.length === 0) {
        el.factsTableBody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-4">No approved facts registered for this workspace.</td></tr>';
      } else {
        el.factsTableBody.innerHTML = facts.map(f => `
          <tr>
            <td><code class="flag-id-badge">${escapeHtml(f.fact_id || f.id || 'FACT')}</code></td>
            <td><strong>${escapeHtml(f.statement || f.fact || f.claim || '')}</strong></td>
            <td><span class="badge badge-neutral">${escapeHtml(f.category || 'General')}</span></td>
            <td><span class="text-muted">${escapeHtml(f.source_document || f.citation || 'Guideline doc')}</span></td>
          </tr>
        `).join('');
      }

      // Terminology Table
      const terms = vault.terminology_rules || [];
      el.termsCountBadge.textContent = `${terms.length} Rules`;
      if (terms.length === 0) {
        el.termsTableBody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-4">No terminology rules defined.</td></tr>';
      } else {
        el.termsTableBody.innerHTML = terms.map(t => {
          const sev = (t.severity || 'WARNING').toUpperCase();
          const bClass = sev === 'CRITICAL' ? 'badge-danger' : 'badge-warning';
          return `
            <tr>
              <td><span class="flagged-snippet-text">${escapeHtml(t.prohibited_term || t.term || '')}</span></td>
              <td><span class="suggested-snippet-text">${escapeHtml(t.approved_alternative || t.alternative || '')}</span></td>
              <td><span class="badge ${bClass}">${escapeHtml(sev)}</span></td>
              <td><span class="text-muted">${escapeHtml(t.rule_reason || t.citation || '')}</span></td>
            </tr>
          `;
        }).join('');
      }

      // Color Palette Swatches
      const colors = vault.color_palette || {};
      const colorKeys = Object.keys(colors);
      if (colorKeys.length === 0) {
        el.paletteSwatchesContainer.innerHTML = '<p class="text-muted">No color tokens ingested.</p>';
      } else {
        el.paletteSwatchesContainer.innerHTML = colorKeys.map(key => {
          const val = colors[key];
          const hex = typeof val === 'string' ? val : (val.hex || '#3b82f6');
          return `
            <div class="color-swatch-card">
              <div class="swatch-color-box" style="background-color: ${escapeHtml(hex)};"></div>
              <div class="swatch-meta">
                <div class="swatch-name">${escapeHtml(key)}</div>
                <div class="swatch-hex">${escapeHtml(hex)}</div>
              </div>
            </div>
          `;
        }).join('');
      }

    } catch (err) {
      console.error('Error loading vault:', err);
      showToast(`Failed to load vault data: ${err.message}`, 'error');
    }
  }

  el.btnRefreshVault.addEventListener('click', loadVaultData);

  // Drag and Drop Guideline Upload
  el.guidelineDropzone.addEventListener('click', () => el.guidelineFileInput.click());
  el.guidelineDropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    el.guidelineDropzone.classList.add('dragover');
  });
  el.guidelineDropzone.addEventListener('dragleave', () => el.guidelineDropzone.classList.remove('dragover'));
  el.guidelineDropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    el.guidelineDropzone.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
      uploadGuidelineFile(e.dataTransfer.files[0]);
    }
  });
  el.guidelineFileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      uploadGuidelineFile(e.target.files[0]);
    }
  });

  async function uploadGuidelineFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('project_id', state.currentProject);

    showToast(`Ingesting ${file.name} into ${state.currentProject}...`, 'info');

    try {
      const res = await fetch(`${API_BASE}/upload-guidelines`, {
        method: 'POST',
        body: formData
      });

      if (!res.ok) throw new Error(`Upload failed (${res.status})`);
      const data = await res.json();

      showToast(`Guidelines ingested successfully! Extracted facts and rules.`, 'success');
      logActivity('INGEST', `Uploaded guideline: ${file.name}`, `Extracted into project ${state.currentProject}`);
      loadVaultData();
    } catch (err) {
      console.error('Upload guideline error:', err);
      showToast(`Upload failed: ${err.message}`, 'error');
    }
  }

  // =========================================================================
  // Projects Tab Operations
  // =========================================================================
  async function loadProjects() {
    try {
      const res = await fetch(`${API_BASE}/projects`);
      if (!res.ok) throw new Error(`Failed to fetch projects (${res.status})`);
      const projects = await res.json();

      if (!projects || projects.length === 0) {
        el.projectsGridContainer.innerHTML = '<p class="text-muted">No workspaces found.</p>';
        return;
      }

      el.projectsGridContainer.innerHTML = projects.map(p => {
        const stats = p.stats || {};
        return `
          <div class="project-card">
            <div>
              <div class="project-card-header">
                <div>
                  <h4 class="project-card-name">${escapeHtml(p.name)}</h4>
                  <div class="project-card-id">${escapeHtml(p.project_id)}</div>
                </div>
                <button type="button" class="btn btn-secondary small" onclick="selectWorkspace('${p.project_id}')">
                  ${p.project_id === state.currentProject ? 'Active' : 'Select'}
                </button>
              </div>
              <p class="project-card-desc">${escapeHtml(p.description || 'No description.')}</p>
              <div style="font-size: 0.75rem; color: var(--accent-blue); margin-bottom: 0.75rem;">
                <strong>Persona:</strong> ${escapeHtml(p.persona || 'Standard Corporate')}
              </div>
            </div>
            <div class="project-card-stats">
              <span>Facts: <b>${stats.facts_count ?? '--'}</b></span>
              <span>Terms: <b>${stats.terms_count ?? '--'}</b></span>
              <span>Colors: <b>${stats.colors_count ?? '--'}</b></span>
            </div>
          </div>
        `;
      }).join('');
    } catch (err) {
      console.error('Failed to load projects:', err);
      showToast(`Error loading projects: ${err.message}`, 'error');
    }
  }

  window.selectWorkspace = function(projectId) {
    state.currentProject = projectId;
    el.projectSelector.value = projectId;
    showToast(`Switched active workspace to: ${projectId}`, 'success');
    loadProjects();
    loadVaultData();
  };

  el.createProjectForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const pid = el.newProjectId.value.trim().toLowerCase().replace(/[^a-z0-9_-]/g, '-');
    const name = el.newProjectName.value.trim();
    const persona = el.newProjectPersona.value.trim();
    const desc = el.newProjectDesc.value.trim();
    const file = el.newProjectGuidelinesFile.files[0];

    if (!pid || !name) {
      showToast('Workspace ID and Name are required.', 'error');
      return;
    }

    const formData = new FormData();
    formData.append('project_id', pid);
    formData.append('name', name);
    formData.append('description', desc);
    formData.append('persona', persona);
    if (file) {
      formData.append('guidelines_file', file);
    }

    try {
      const res = await fetch(`${API_BASE}/projects`, {
        method: 'POST',
        body: formData
      });

      if (!res.ok) throw new Error(`Project creation failed (${res.status})`);
      const data = await res.json();

      showToast(`Workspace "${name}" created!`, 'success');
      logActivity('PROJECT', `Created workspace: ${name} (${pid})`, `Persona: ${persona}`);

      el.createProjectForm.reset();
      await loadProjectsDropdown();
      await loadProjects();
      selectWorkspace(pid);
    } catch (err) {
      console.error('Create project error:', err);
      showToast(`Create workspace error: ${err.message}`, 'error');
    }
  });

  // =========================================================================
  // Analytics Tab Operations
  // =========================================================================
  async function loadAnalytics() {
    try {
      const res = await fetch(`${API_BASE}/analytics`);
      if (!res.ok) throw new Error(`Analytics error (${res.status})`);
      const data = await res.json();

      // KPIs
      el.kpiTotalAudits.textContent = data.total_audits_recorded ?? 0;
      el.kpiAvgCompliance.textContent = data.average_compliance_score != null ? `${data.average_compliance_score.toFixed(0)}%` : '--';
      el.kpiAvgLatency.textContent = data.average_latency_ms != null ? `${data.average_latency_ms.toFixed(1)} ms` : '-- ms';
      el.kpiTotalViolations.textContent = data.total_violations_detected ?? 0;

      // Dimension breakdown
      const dimStats = data.violations_by_dimension || {};
      const dimKeys = Object.keys(dimStats);
      if (dimKeys.length === 0) {
        el.analyticsDimensionStats.innerHTML = '<p class="text-muted">No audit violation data yet.</p>';
      } else {
        el.analyticsDimensionStats.innerHTML = dimKeys.map(k => `
          <div class="analytics-row-item">
            <span style="text-transform: capitalize; font-weight: 500;">${escapeHtml(k)}</span>
            <span class="badge badge-danger">${dimStats[k]} flags</span>
          </div>
        `).join('');
      }

      // Actions breakdown
      const actionStats = data.actions_recorded || {};
      const actionKeys = Object.keys(actionStats);
      if (actionKeys.length === 0) {
        el.analyticsActionsStats.innerHTML = '<p class="text-muted">No review actions recorded yet.</p>';
      } else {
        el.analyticsActionsStats.innerHTML = actionKeys.map(k => `
          <div class="analytics-row-item">
            <span style="font-weight: 500;">Action: ${escapeHtml(k)}</span>
            <span class="badge badge-accent">${actionStats[k]} recorded</span>
          </div>
        `).join('');
      }

    } catch (err) {
      console.error('Analytics load error:', err);
      showToast(`Failed to load analytics: ${err.message}`, 'error');
    }
  }

  el.btnRefreshAnalytics.addEventListener('click', loadAnalytics);

  // =========================================================================
  // Activity Tab Operations
  // =========================================================================
  el.btnClearActivity.addEventListener('click', () => {
    state.activityLog = [];
    renderActivityStream();
    showToast('Activity stream cleared', 'info');
  });


  // =========================================================================
  // Two-Sided Role Mode Management (Creator vs Central Reviewer)
  // =========================================================================
  function setRoleMode(role) {
    state.currentRole = role;
    state.reviewerRole = role === 'Creator' ? 'Creator' : 'Central Reviewer';
    localStorage.setItem('zuard_role_mode', role);

    document.body.classList.remove('mode-creator', 'mode-reviewer');
    document.body.classList.add(role === 'Creator' ? 'mode-creator' : 'mode-reviewer');

    if (el.btnRoleCreator && el.btnRoleReviewer) {
      el.btnRoleCreator.classList.toggle('active', role === 'Creator');
      el.btnRoleReviewer.classList.toggle('active', role === 'Reviewer');
    }

    const activeModeText = document.getElementById('activeModeText');
    if (role === 'Creator') {
      if (el.brandSubtitle) el.brandSubtitle.textContent = 'Creator Studio • Real-Time Pre-Screen & Copywriting';
      if (el.tabReviewLabel) el.tabReviewLabel.textContent = 'Studio & Pre-Screen';
      if (el.tabQueueLabel) el.tabQueueLabel.textContent = 'My Submissions';
      if (el.queuePanelHeading) el.queuePanelHeading.textContent = 'My Submissions & Campaign Tracker';
      if (el.queuePanelSubheading) el.queuePanelSubheading.textContent = 'Track governance review statuses and reviewer notes for your campaign drafts.';
      if (el.btnRunAuditText) el.btnRunAuditText.textContent = 'Pre-Screen Draft';
      if (el.btnOpenSubmitModal) el.btnOpenSubmitModal.classList.remove('hidden');
      if (activeModeText) activeModeText.textContent = 'Creator Studio Active';
    } else {
      if (el.brandSubtitle) el.brandSubtitle.textContent = 'Central Governance Console • Policy & Approvals';
      if (el.tabReviewLabel) el.tabReviewLabel.textContent = 'Studio & Inspector';
      if (el.tabQueueLabel) el.tabQueueLabel.textContent = 'Governance Queue';
      if (el.queuePanelHeading) el.queuePanelHeading.textContent = 'Governance Review Queue';
      if (el.queuePanelSubheading) el.queuePanelSubheading.textContent = 'Review marketing copy submitted by creators. Inspect violations, approve, request changes, or record legal overrides.';
      if (el.btnRunAuditText) el.btnRunAuditText.textContent = 'Audit Draft';
      if (activeModeText) activeModeText.textContent = 'Central Reviewer Active';
    }

    loadSubmissionStats();
    loadSubmissions();
    showToast(`Switched to ${role === 'Creator' ? '🎨 Creator (Client)' : '🛡️ Central Reviewer (Admin)'} Mode`, 'info');
    logActivity('ROLE', `Role switched to ${role}`, `Workspace: ${state.currentProject}`);
  }

  if (el.btnRoleCreator) {
    el.btnRoleCreator.addEventListener('click', () => setRoleMode('Creator'));
  }
  if (el.btnRoleReviewer) {
    el.btnRoleReviewer.addEventListener('click', () => setRoleMode('Reviewer'));
  }

  // =========================================================================
  // Submissions & Governance Workflow
  // =========================================================================
  async function loadSubmissionStats() {
    try {
      const res = await fetch(`${API_BASE}/submissions-stats?project_id=${state.currentProject}`);
      if (!res.ok) return;
      const stats = await res.json();

      if (el.qKpiPending) el.qKpiPending.textContent = stats.pending || 0;
      if (el.qKpiApproved) el.qKpiApproved.textContent = stats.approved || 0;
      if (el.qKpiChanges) el.qKpiChanges.textContent = stats.changes_requested || 0;
      if (el.qKpiTotal) el.qKpiTotal.textContent = stats.total || 0;

      const pendingCount = stats.pending || 0;
      if (el.headerQueueBadge) {
        if (pendingCount > 0) {
          el.headerQueueBadge.textContent = pendingCount;
          el.headerQueueBadge.classList.remove('hidden');
        } else {
          el.headerQueueBadge.classList.add('hidden');
        }
      }
      if (el.tabQueueBadge) {
        if (pendingCount > 0) {
          el.tabQueueBadge.textContent = pendingCount;
          el.tabQueueBadge.style.display = 'inline-block';
        } else {
          el.tabQueueBadge.style.display = 'none';
        }
      }
    } catch (err) {
      console.warn('Failed to load submission stats:', err);
    }
  }

  async function loadSubmissions() {
    if (!el.submissionsTableContainer) return;
    try {
      const filter = state.submissionStatusFilter;
      const url = `${API_BASE}/submissions?project_id=${state.currentProject}` + (filter !== 'all' ? `&status=${filter}` : '');
      const res = await fetch(url);
      if (!res.ok) throw new Error(`Submissions fetch failed (${res.status})`);
      const subs = await res.json();
      state.submissions = subs;
      renderSubmissionsTable(subs);
    } catch (err) {
      console.error('Failed to load submissions:', err);
      el.submissionsTableContainer.innerHTML = `<div class="empty-state-card"><p class="text-red">Error loading submissions: ${escapeHtml(err.message)}</p></div>`;
    }
  }

  function renderSubmissionsTable(subs) {
    if (!subs || subs.length === 0) {
      const isCreator = state.currentRole === 'Creator';
      el.submissionsTableContainer.innerHTML = `
        <div class="empty-state-card" style="padding: 3rem 1rem;">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="text-muted" style="margin-bottom: 0.75rem;">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
          </svg>
          <p class="empty-state-title">${isCreator ? 'No submissions yet' : 'No submissions in queue'}</p>
          <p class="empty-state-desc">${isCreator ? 'Pre-screen your copy in the Studio tab and click "Submit for Review" to submit your work.' : 'All incoming creator submissions will appear here for governance review.'}</p>
        </div>`;
      return;
    }

    const isCreator = state.currentRole === 'Creator';

    el.submissionsTableContainer.innerHTML = `
      <table class="submissions-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Title &amp; Creator</th>
            <th>Workspace</th>
            <th>Score</th>
            <th>Flags</th>
            <th>Status</th>
            <th>Date</th>
            <th style="text-align: right;">Actions</th>
          </tr>
        </thead>
        <tbody>
          ${subs.map(s => {
            const dateStr = s.created_at ? new Date(s.created_at).toLocaleDateString() : '--';
            const score = Math.round(s.compliance_score || 0);
            const scoreColor = score >= 85 ? 'text-green' : score >= 60 ? 'text-amber' : 'text-red';
            const statusLabel = (s.status || 'PENDING_REVIEW').replace(/_/g, ' ');
            
            return `
              <tr>
                <td><span class="font-mono text-accent" style="font-size: 0.8125rem;">${escapeHtml(s.id)}</span></td>
                <td>
                  <div style="font-weight: 600; color: var(--text-main);">${escapeHtml(s.title)}</div>
                  <div class="text-muted" style="font-size: 0.75rem;">By ${escapeHtml(s.creator_name || 'Creator')}</div>
                  ${s.notes ? `<div class="text-subtle" style="font-size: 0.75rem; font-style: italic;">"${escapeHtml(s.notes)}"</div>` : ''}
                </td>
                <td><span class="badge badge-neutral">${escapeHtml(s.project_id)}</span></td>
                <td><strong class="${scoreColor}">${score}%</strong></td>
                <td><span class="badge ${s.violations_count > 0 ? 'badge-danger' : 'badge-success'}">${s.violations_count}</span></td>
                <td>
                  <span class="status-pill status-${s.status}">
                    ${statusLabel}
                  </span>
                  ${s.reviewer_decision ? `<div style="font-size: 0.7rem; color: var(--text-muted); margin-top: 2px;">Decision by ${escapeHtml(s.reviewer_decision.reviewer_name || 'Admin')}</div>` : ''}
                </td>
                <td class="text-muted" style="font-size: 0.75rem;">${dateStr}</td>
                <td style="text-align: right;">
                  <div class="btn-actions-group" style="justify-content: flex-end;">
                    ${!isCreator ? `
                      <button type="button" class="btn btn-primary small" onclick="window.openReviewModal('${s.id}')" title="Review & Make Governance Decision">
                        Review &amp; Decide
                      </button>
                    ` : ''}
                    <button type="button" class="btn btn-secondary small" onclick="window.loadSubmissionToStudio('${s.id}')" title="Load into Studio Editor">
                      ${isCreator ? 'Revise in Studio' : 'Inspect'}
                    </button>
                    ${!isCreator ? `
                      <button type="button" class="btn btn-ghost small" onclick="window.deleteSubmission('${s.id}')" title="Delete submission" style="color: var(--color-red);">
                        &times;
                      </button>
                    ` : ''}
                  </div>
                </td>
              </tr>
            `;
          }).join('')}
        </tbody>
      </table>
    `;
  }

  // Filter buttons handler
  if (el.queueStatusFilterGroup) {
    el.queueStatusFilterGroup.querySelectorAll('.btn-filter').forEach(btn => {
      btn.addEventListener('click', (e) => {
        el.queueStatusFilterGroup.querySelectorAll('.btn-filter').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.submissionStatusFilter = btn.dataset.status;
        loadSubmissions();
      });
    });
  }

  if (el.btnRefreshSubmissions) {
    el.btnRefreshSubmissions.addEventListener('click', () => {
      loadSubmissions();
      loadSubmissionStats();
      showToast('Submissions queue refreshed', 'info');
    });
  }

  // =========================================================================
  // Creator Submit Modal Logic
  // =========================================================================
  function openSubmitModal() {
    const text = el.draftContentInput.value.trim();
    if (!text) {
      showToast('Please type or load marketing copy into the editor before submitting.', 'error');
      el.draftContentInput.focus();
      return;
    }

    if (el.subTitleInput) {
      el.subTitleInput.value = el.documentTitleInput.value.trim() || 'Marketing Campaign Draft';
    }
    if (el.modalPreWorkspace) {
      el.modalPreWorkspace.textContent = state.currentProject;
    }
    const score = state.currentAuditResponse?.compliance_score ?? '--';
    const violations = state.currentAuditResponse?.total_violations_count ?? '--';
    if (el.modalPreScore) el.modalPreScore.textContent = `${score}/100`;
    if (el.modalPreViolations) el.modalPreViolations.textContent = violations;

    const savedCreator = localStorage.getItem('zuard_creator_name') || 'Content Team Alpha';
    if (el.subCreatorNameInput) el.subCreatorNameInput.value = savedCreator;

    el.submitDraftModal.classList.remove('hidden');
  }

  function closeSubmitModal() {
    if (el.submitDraftModal) el.submitDraftModal.classList.add('hidden');
  }

  if (el.btnOpenSubmitModal) {
    el.btnOpenSubmitModal.addEventListener('click', openSubmitModal);
  }
  if (el.btnCloseSubmitModal) {
    el.btnCloseSubmitModal.addEventListener('click', closeSubmitModal);
  }
  if (el.btnCancelSubmitModal) {
    el.btnCancelSubmitModal.addEventListener('click', closeSubmitModal);
  }

  async function confirmSubmitDraft() {
    const title = el.subTitleInput.value.trim() || 'Untitled Campaign';
    const creatorName = el.subCreatorNameInput.value.trim() || 'Content Creator';
    const notes = el.subNotesInput.value.trim();
    const contentText = el.draftContentInput.value.trim();

    localStorage.setItem('zuard_creator_name', creatorName);

    const payload = {
      project_id: state.currentProject,
      title: title,
      content_text: contentText,
      creator_name: creatorName,
      notes: notes,
      compliance_score: state.currentAuditResponse?.compliance_score || 0,
      violations_count: state.currentAuditResponse?.total_violations_count || 0,
      audit_data: state.currentAuditResponse || null
    };

    try {
      el.btnConfirmSubmitDraft.disabled = true;
      const res = await fetch(`${API_BASE}/submissions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) throw new Error(`Submission failed (${res.status})`);
      const created = await res.json();

      closeSubmitModal();
      showToast(`Submission ${created.id} sent to Central Reviewer!`, 'success');
      logActivity('SUBMIT', `Submitted "${title}" to Governance Queue`, `ID: ${created.id} • Creator: ${creatorName}`);

      loadSubmissionStats();
      loadSubmissions();

      // Switch to queue tab to see status
      switchTab('queue');
    } catch (err) {
      console.error('Submit draft error:', err);
      showToast(`Submission error: ${err.message}`, 'error');
    } finally {
      el.btnConfirmSubmitDraft.disabled = false;
    }
  }

  if (el.btnConfirmSubmitDraft) {
    el.btnConfirmSubmitDraft.addEventListener('click', confirmSubmitDraft);
  }

  // =========================================================================
  // Reviewer Decision Modal Logic
  // =========================================================================
  window.openReviewModal = async function(subId) {
    try {
      const res = await fetch(`${API_BASE}/submissions/${subId}`);
      if (!res.ok) throw new Error(`Could not fetch submission (${res.status})`);
      const sub = await res.json();
      state.activeDecisionSubId = subId;

      el.decSubId.textContent = sub.id;
      el.decCreator.textContent = sub.creator_name || 'Creator';
      el.decWorkspace.textContent = sub.project_id;
      el.decStatusBadge.textContent = (sub.status || 'PENDING_REVIEW').replace(/_/g, ' ');
      el.decStatusBadge.className = `badge ${sub.status === 'APPROVED' ? 'badge-success' : sub.status === 'CHANGES_REQUESTED' ? 'badge-warning' : 'badge-danger'}`;
      el.decCreatorNotes.textContent = sub.notes || 'No extra notes provided by creator.';
      el.decContentPreview.textContent = sub.content_text || '';

      // Reset tabs to APPROVE
      state.selectedDecisionAction = 'APPROVE';
      updateDecisionActionTabs('APPROVE');
      el.decFeedbackInput.value = '';

      el.reviewDecisionModal.classList.remove('hidden');
    } catch (err) {
      console.error('Open review modal error:', err);
      showToast(`Failed to open submission: ${err.message}`, 'error');
    }
  };

  function updateDecisionActionTabs(action) {
    state.selectedDecisionAction = action;
    [el.btnDecApproveTab, el.btnDecChangesTab, el.btnDecOverrideTab].forEach(btn => {
      if (btn) btn.classList.toggle('active', btn.dataset.action === action);
    });

    if (action === 'APPROVE') {
      el.decFeedbackLabel.textContent = 'Approval Remarks (Optional)';
      el.decFeedbackInput.placeholder = 'e.g. Perfect alignment with Q4 brand tone and verified metrics. Approved.';
    } else if (action === 'REQUEST_CHANGES') {
      el.decFeedbackLabel.textContent = 'Policy Feedback & Required Revisions';
      el.decFeedbackInput.placeholder = 'e.g. Please replace unverified claim with approved Fact #F-104.';
    } else {
      el.decFeedbackLabel.textContent = 'Legal / Governance Exemption Justification (Required)';
      el.decFeedbackInput.placeholder = 'e.g. Approved under Executive Marketing Exception #MEMO-2026-04.';
    }
  }

  [el.btnDecApproveTab, el.btnDecChangesTab, el.btnDecOverrideTab].forEach(btn => {
    if (btn) {
      btn.addEventListener('click', () => updateDecisionActionTabs(btn.dataset.action));
    }
  });

  function closeDecisionModal() {
    if (el.reviewDecisionModal) el.reviewDecisionModal.classList.add('hidden');
  }

  if (el.btnCloseDecisionModal) {
    el.btnCloseDecisionModal.addEventListener('click', closeDecisionModal);
  }

  async function submitDecision() {
    const subId = state.activeDecisionSubId;
    if (!subId) return;

    const action = state.selectedDecisionAction;
    const reviewerName = el.decReviewerNameInput.value.trim() || 'Central Governance Lead';
    const feedback = el.decFeedbackInput.value.trim();

    if (action === 'OVERRIDE' && !feedback) {
      showToast('Please provide a legal or governance justification for overriding.', 'error');
      el.decFeedbackInput.focus();
      return;
    }

    try {
      el.btnSubmitDecision.disabled = true;
      const payload = {
        action: action,
        reviewer_name: reviewerName,
        feedback_notes: feedback,
        justification: action === 'OVERRIDE' ? feedback : ''
      };

      const res = await fetch(`${API_BASE}/submissions/${subId}/decision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) throw new Error(`Decision submission failed (${res.status})`);
      const result = await res.json();

      closeDecisionModal();
      showToast(`Decision recorded: ${action} for ${subId}`, 'success');
      logActivity(action, `Governance Decision on ${subId}`, `Status: ${result.submission.status} • Reviewer: ${reviewerName}`);

      loadSubmissionStats();
      loadSubmissions();
    } catch (err) {
      console.error('Submit decision error:', err);
      showToast(`Decision failed: ${err.message}`, 'error');
    } finally {
      el.btnSubmitDecision.disabled = false;
    }
  }

  if (el.btnSubmitDecision) {
    el.btnSubmitDecision.addEventListener('click', submitDecision);
  }

  window.loadSubmissionToStudio = async function(subId) {
    try {
      const res = await fetch(`${API_BASE}/submissions/${subId}`);
      if (!res.ok) throw new Error(`Failed to load submission (${res.status})`);
      const sub = await res.json();

      el.documentTitleInput.value = sub.title || 'Submission Draft';
      el.draftContentInput.value = sub.content_text || '';
      updateWordCount();

      closeDecisionModal();
      switchTab('review');

      // If submission already has audit data, render it; otherwise run audit
      if (sub.audit_data && sub.audit_data.compliance_score !== undefined) {
        state.currentAuditResponse = sub.audit_data;
        renderAuditResults(sub.audit_data);
      } else {
        runAudit();
      }

      showToast(`Loaded "${sub.title}" into Studio Editor`, 'info');
    } catch (err) {
      console.error('Load submission error:', err);
      showToast(`Could not load submission: ${err.message}`, 'error');
    }
  };

  if (el.btnInspectInStudio) {
    el.btnInspectInStudio.addEventListener('click', () => {
      if (state.activeDecisionSubId) {
        window.loadSubmissionToStudio(state.activeDecisionSubId);
      }
    });
  }

  window.deleteSubmission = async function(subId) {
    if (!confirm(`Are you sure you want to delete submission ${subId}?`)) return;
    try {
      const res = await fetch(`${API_BASE}/submissions/${subId}`, { method: 'DELETE' });
      if (!res.ok) throw new Error(`Delete failed (${res.status})`);
      showToast(`Submission ${subId} deleted`, 'info');
      logActivity('DELETE', `Deleted submission ${subId}`, `Workspace: ${state.currentProject}`);
      loadSubmissionStats();
      loadSubmissions();
    } catch (err) {
      console.error('Delete submission error:', err);
      showToast(`Failed to delete: ${err.message}`, 'error');
    }
  };

  // =========================================================================
  // Initialization Sequence
  // =========================================================================
  async function init() {
    await checkServerHealth();
    await loadProjectsDropdown();
    updateWordCount();
    setRoleMode(state.currentRole);
    loadSubmissionStats();
    logActivity('SYS', 'Zuard Governance Studio Initialized', `API Endpoint: ${API_BASE}`);
  }

  init();
});
