// Zuard Frontend Application Logic
document.addEventListener('DOMContentLoaded', () => {
  // Configurable API base (relative if served by backend, fallback to http://127.0.0.1:8000/api if standalone)
  const API_BASE = (window.location.port === "8000" || window.location.pathname.startsWith("/api")) 
    ? "/api" 
    : (window.ZUARD_API_URL || "http://127.0.0.1:8000/api");

  // Elements
  const navTabs = document.querySelectorAll('.nav-tab');
  const tabContents = document.querySelectorAll('.tab-content');
  const viewPills = document.querySelectorAll('.view-pill');
  const viewPanels = document.querySelectorAll('.editor-view-panel');
  
  const draftText = document.getElementById('draft-text');
  const docTitleInput = document.getElementById('doc-title-input');
  const docStatusBadge = document.getElementById('document-status-badge');
  const privacyToggle = document.getElementById('privacy-toggle');
  const privacyStatusText = document.getElementById('privacy-status-text');

  // Multi-Project Workspace Elements
  let currentProjectId = "zuard-enterprise";
  const projectSelector = document.getElementById('project-selector');
  const btnOpenNewProjectModal = document.getElementById('btn-open-new-project-modal');
  const newProjectModal = document.getElementById('new-project-modal');
  const btnCloseProjectModal = document.getElementById('btn-close-project-modal');
  const btnCancelProjectModal = document.getElementById('btn-cancel-project-modal');
  const newProjectForm = document.getElementById('new-project-form');

  const btnRunAudit = document.getElementById('btn-run-audit');
  const btnClearText = document.getElementById('btn-clear-text');
  const cardsList = document.getElementById('cards-list');
  const inspectorCardsCount = document.getElementById('inspector-cards-count');

  const statScore = document.getElementById('stat-score');
  const statScoreSub = document.getElementById('stat-score-sub');
  const statLatency = document.getElementById('stat-latency');
  const statViolations = document.getElementById('stat-violations');

  const flaggedMarkupDisplay = document.getElementById('flagged-markup-display');
  const diffOriginalContent = document.getElementById('diff-original-content');
  const diffSuggestedContent = document.getElementById('diff-suggested-content');

  const fgColorInput = document.getElementById('fg-color-input');
  const bgColorInput = document.getElementById('bg-color-input');
  const altTextInput = document.getElementById('alt-text-input');
  const contrastPreviewChip = document.getElementById('contrast-preview-chip');

  // Presets
  const btnLoadSample1 = document.getElementById('btn-load-sample-1');
  const btnLoadSample2 = document.getElementById('btn-load-sample-2');
  const btnLoadSample3 = document.getElementById('btn-load-sample-3');

  // Vault elements
  const btnRefreshVault = document.getElementById('btn-refresh-vault');
  const factsTbody = document.getElementById('facts-tbody');
  const termsTbody = document.getElementById('terms-tbody');
  const paletteSwatchesGrid = document.getElementById('palette-swatches-grid');
  const vaultFactsCount = document.getElementById('vault-facts-count');
  const vaultTermsCount = document.getElementById('vault-terms-count');

  // Analytics elements
  const btnRefreshAnalytics = document.getElementById('btn-refresh-analytics');
  const kpiTotalDocs = document.getElementById('kpi-total-docs');
  const kpiAvgScore = document.getElementById('kpi-avg-score');
  const kpiAvgSpeed = document.getElementById('kpi-avg-speed');
  const kpiTotalOverrides = document.getElementById('kpi-total-overrides');
  const dimensionBars = document.getElementById('dimension-bars');
  const ambiguityHotspotsList = document.getElementById('ambiguity-hotspots-list');

  let currentAuditResult = null;

  // 1. Navigation Tab Switching
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
      } else if (tab.getAttribute('data-tab') === 'governance-insights') {
        loadAnalyticsData();
      }
    });
  });

  // 2. View Switcher (Draft / Flagged / Diff)
  viewPills.forEach(pill => {
    pill.addEventListener('click', () => {
      viewPills.forEach(p => p.classList.remove('active'));
      viewPanels.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      const targetView = document.getElementById(`view-${pill.getAttribute('data-view')}`);
      if (targetView) targetView.classList.add('active');
    });
  });

  // 3. Privacy Toggle
  privacyToggle.addEventListener('change', () => {
    if (privacyToggle.checked) {
      privacyStatusText.textContent = "Google Gemini 2.5 Flash Cloud";
      privacyStatusText.style.color = "#93C5FD";
    } else {
      privacyStatusText.textContent = "Confidential Local Mode";
      privacyStatusText.style.color = "var(--text-muted)";
    }
  });

  // 4. Live Contrast Preview Calculation
  function updateContrastPreview() {
    const fg = fgColorInput.value.trim();
    const bg = bgColorInput.value.trim();
    if (/^#[0-9A-Fa-f]{6}$/.test(fg) && /^#[0-9A-Fa-f]{6}$/.test(bg)) {
      contrastPreviewChip.style.color = fg;
      contrastPreviewChip.style.backgroundColor = bg;
      
      const r1 = parseInt(fg.slice(1,3), 16), g1 = parseInt(fg.slice(3,5), 16), b1 = parseInt(fg.slice(5,7), 16);
      const r2 = parseInt(bg.slice(1,3), 16), g2 = parseInt(bg.slice(3,5), 16), b2 = parseInt(bg.slice(5,7), 16);
      
      const l1 = calcLuminance(r1, g1, b1);
      const l2 = calcLuminance(r2, g2, b2);
      const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
      const ratioRound = ratio.toFixed(1);
      const pass = ratio >= 4.5 ? "PASS" : "FAIL";
      contrastPreviewChip.textContent = `Aa (${ratioRound}:1 ${pass})`;
    }
  }

  function calcLuminance(r, g, b) {
    const a = [r, g, b].map(v => {
      v /= 255;
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    return a[0] * 0.2126 + a[1] * 0.7152 + a[2] * 0.0722;
  }

  fgColorInput.addEventListener('input', updateContrastPreview);
  bgColorInput.addEventListener('input', updateContrastPreview);

  // 5. Presets
  btnLoadSample1.addEventListener('click', () => {
    switchProject('zuard-enterprise');
    docTitleInput.value = "Q4_Product_Launch_Release.pdf";
    draftText.value = `Our #1 AI platform is super cheap and cuts costs by 99.9%. With our revolutionary miracle engine, you get 100% infallible automated deployments. Don't worry about complexity—this life hack guarantees insane speedups with our legacy sync feature.`;
    fgColorInput.value = "#FFFFFF";
    bgColorInput.value = "#FF0055";
    altTextInput.value = "banner";
    updateContrastPreview();
    runAudit();
  });

  btnLoadSample2.addEventListener('click', () => {
    switchProject('zuard-enterprise');
    docTitleInput.value = "Enterprise_Compliance_Release_v1.pdf";
    draftText.value = `Zuard Enterprise Platform delivers an industry-leading pre-publication brand governance gateway. In recent benchmarks, organisations demonstrated a verified 42% average operational cost reduction, backed by our 99.95% enterprise platform uptime SLA commitment. Teams pre-screen content in an average of 2.5 seconds, saving reviewer hours across all channels.`;
    fgColorInput.value = "#FFFFFF";
    bgColorInput.value = "#0F172A";
    altTextInput.value = "Comprehensive product screenshot of the Zuard review portal dashboard";
    updateContrastPreview();
    runAudit();
  });

  btnLoadSample3.addEventListener('click', () => {
    switchProject('zuard-consumer');
    docTitleInput.value = "Mobile_Creator_Announcement.md";
    draftText.value = `The Zuard Consumer app is trusted by over 5 million creators worldwide. Create lively, inspiring video stories with guaranteed 50ms real-time audio sync. Get started with our generous starter tier giving you 10 free exports per month.`;
    fgColorInput.value = "#FFFFFF";
    bgColorInput.value = "#8B5CF6";
    altTextInput.value = "Energetic preview of mobile video timeline editor";
    updateContrastPreview();
    runAudit();
  });

  btnClearText.addEventListener('click', () => {
    draftText.value = "";
    cardsList.innerHTML = `<div class="empty-cards-state"><p>Draft cleared. Enter text or click a sample preset above.</p></div>`;
    statScore.textContent = "--";
    statLatency.textContent = "0 ms";
    statViolations.textContent = "0";
    inspectorCardsCount.textContent = "0 Issues";
    flaggedMarkupDisplay.textContent = "";
    diffOriginalContent.textContent = "";
    diffSuggestedContent.textContent = "";
  });

  // 6. Execute Audit
  async function runAudit() {
    const text = draftText.value.trim();
    if (!text) {
      alert("Please enter draft text or select a benchmark preset.");
      return;
    }

    btnRunAudit.disabled = true;
    btnRunAudit.innerHTML = `<span class="loading-spinner"></span> Screening...`;

    const payload = {
      project_id: currentProjectId,
      document_title: docTitleInput.value.trim() || "Untitled_Draft",
      content_text: text,
      privacy_mode: !privacyToggle.checked,
      color_pairs: [[fgColorInput.value.trim(), bgColorInput.value.trim()]],
      alt_texts: [{ alt: altTextInput.value.trim(), asset_name: "banner_asset" }]
    };

    try {
      const response = await fetch(`${API_BASE}/audit-content`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`);
      }

      const data = await response.json();
      currentAuditResult = data;
      renderAuditResults(data);
    } catch (err) {
      console.error(err);
      alert(`Audit failed: ${err.message}. Ensure backend is running.`);
    } finally {
      btnRunAudit.disabled = false;
      btnRunAudit.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg> Run Static Pre-Check & RAG`;
    }
  }

  btnRunAudit.addEventListener('click', runAudit);

  // 7. Render Audit Results
  function renderAuditResults(data) {
    // Stats bar
    statScore.textContent = data.compliance_score;
    if (data.compliance_score >= 85) {
      statScore.className = "metric-value text-green";
      statScoreSub.textContent = "Compliant";
      docStatusBadge.textContent = "Approved — v2";
      docStatusBadge.style.color = "#34D399";
    } else if (data.compliance_score >= 60) {
      statScore.className = "metric-value text-amber";
      statScoreSub.textContent = "Warnings Detected";
      docStatusBadge.textContent = "In Review — v2";
      docStatusBadge.style.color = "#FBBF24";
    } else {
      statScore.className = "metric-value text-red";
      statScoreSub.textContent = "Critical Violations";
      docStatusBadge.textContent = "Changes Requested";
      docStatusBadge.style.color = "#F87171";
    }

    statLatency.textContent = `${data.execution_time_ms} ms`;
    statViolations.textContent = data.total_violations_count;
    inspectorCardsCount.textContent = `${data.total_violations_count} Issues`;

    // Flagged markup view
    flaggedMarkupDisplay.innerHTML = highlightFlaggedMarkup(data.flagged_draft_markup);

    // Diff view
    diffOriginalContent.textContent = data.original_text;
    diffSuggestedContent.innerHTML = highlightDiff(data.original_text, data.suggested_full_rewrite);

    // Inspector Cards
    renderInspectorCards(data.inspector_cards);
  }

  function highlightFlaggedMarkup(rawMarkup) {
    return rawMarkup.replace(/(\[FLAG \d+:[^\]]+\])/g, '<span class="flag-tag">$1</span>');
  }

  function highlightDiff(orig, rewrite) {
    if (orig === rewrite) {
      return `<div>${orig}</div><p style="color: #34D399; margin-top: 12px; font-weight: 600;">✓ Perfect match with all brand guidelines.</p>`;
    }
    return `<div style="color: #34D399;">${rewrite}</div>`;
  }

  function renderInspectorCards(cards) {
    if (!cards || cards.length === 0) {
      cardsList.innerHTML = `
        <div class="empty-cards-state">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22 4 12 14.01 9 11.01"/>
          </svg>
          <p style="color: #34D399; font-weight: 700;">Zero Brand Violations Detected</p>
          <p class="subtle-text">All lexical, factual, visual, and WCAG rules satisfied in full.</p>
        </div>
      `;
      return;
    }

    cardsList.innerHTML = cards.map(c => `
      <div class="inspector-card-item" id="card-${c.flag_id}">
        <div class="card-top-row">
          <div class="card-tags">
            <span class="badge-flag-id">${c.flag_id}</span>
            <span class="badge-severity ${c.severity}">${c.severity}</span>
            <span class="status-badge">${c.dimension.toUpperCase()}</span>
          </div>
          <span style="font-size: 0.72rem; color: var(--text-dim);">Conf: ${Math.round(c.confidence_score * 100)}%</span>
        </div>

        ${c.original_snippet ? `<div class="card-snippet">Flagged: "${c.original_snippet}"</div>` : ''}
        
        <div class="card-issue-text">${c.issue_explanation}</div>

        <div class="card-citation-box">
          <span class="citation-label">Cited Brand Source & Section:</span>
          <span class="citation-text">${c.cited_source}</span>
        </div>

        <div class="card-suggestion-box">
          <span class="suggestion-label">Suggested Intent-Preserving Correction:</span>
          <div style="font-weight: 600;">"${c.suggested_rewrite}"</div>
        </div>

        <div class="card-ai-badge">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/></svg>
          <span>${c.ai_disclosure}</span>
        </div>

        <div class="card-actions-row">
          <button class="btn-action-accept" onclick="handleCardAction('${c.flag_id}', 'ACCEPT')">Accept Rewrite</button>
          <button class="btn-action-override" onclick="handleCardAction('${c.flag_id}', 'OVERRIDE')">Override with Reason</button>
        </div>
      </div>
    `).join('');
  }

  // Card Action Handler
  window.handleCardAction = async function(flagId, action) {
    let reason = null;
    if (action === 'OVERRIDE') {
      reason = prompt("Enter justification reason for overriding this brand rule (e.g., intentional campaign exception):");
      if (!reason) return;
    }

    try {
      const resp = await fetch(`${API_BASE}/review-action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          flag_id: flagId,
          action: action,
          override_justification: reason,
          reviewer_role: "Reviewer"
        })
      });
      const res = await resp.json();
      
      const cardEl = document.getElementById(`card-${flagId}`);
      if (cardEl) {
        if (action === 'ACCEPT') {
          cardEl.style.opacity = '0.5';
          cardEl.style.borderLeft = '4px solid var(--accent-green)';
          cardEl.querySelector('.card-actions-row').innerHTML = `<span style="color: #34D399; font-size: 0.8rem; font-weight: 700;">✓ Accepted & Integrated</span>`;
        } else {
          cardEl.style.opacity = '0.7';
          cardEl.style.borderLeft = '4px solid var(--accent-amber)';
          cardEl.querySelector('.card-actions-row').innerHTML = `<span style="color: #FBBF24; font-size: 0.8rem; font-weight: 700;">⚡ Overridden (Logged to Telemetry)</span>`;
        }
      }
    } catch (e) {
      alert("Failed to record action");
    }
  };

  async function loadVaultData() {
    try {
      const res = await fetch(`${API_BASE}/vault?project_id=${currentProjectId}`);
      const data = await res.json();
      
      vaultFactsCount.textContent = `${data.approved_facts.length} Verified Facts`;
      vaultTermsCount.textContent = `${data.terminology_rules.length} Rules`;

      // Facts table
      factsTbody.innerHTML = data.approved_facts.map(f => `
        <tr>
          <td><strong style="color: #93C5FD;">#${f.fact_id}</strong></td>
          <td><span class="status-badge">${f.category}</span></td>
          <td><strong style="color: #34D399;">${f.approved_value}</strong></td>
          <td>${f.approved_claim}</td>
          <td style="font-size: 0.75rem; color: var(--text-dim);">${f.source_doc} (p.${f.page_number})</td>
        </tr>
      `).join('');

      // Terms table
      termsTbody.innerHTML = data.terminology_rules.map(t => `
        <tr>
          <td><code style="color: #F87171; background: rgba(239, 68, 68, 0.1); padding: 2px 6px; border-radius: 4px;">${t.term}</code></td>
          <td><span class="badge-severity ${t.severity}">${t.severity}</span></td>
          <td><strong style="color: #34D399;">${t.preferred}</strong></td>
          <td>${t.rationale} <br><small style="color: var(--text-dim);">Source: ${t.cited_doc || 'Brand Book'}, p.${t.page || 1}</small></td>
        </tr>
      `).join('');

      // Palette cards
      const palette = data.color_palette;
      paletteSwatchesGrid.innerHTML = Object.keys(palette).map(k => {
        const item = palette[k];
        return `
          <div class="palette-card">
            <div class="color-swatch-box" style="background-color: ${item.hex};"></div>
            <div class="palette-meta">
              <span class="color-name">${item.name}</span>
              <span class="color-hex">${item.hex}</span>
              <p style="font-size: 0.7rem; color: var(--text-dim); margin-top: 4px;">${item.usage}</p>
            </div>
          </div>
        `;
      }).join('');

    } catch (e) {
      console.error(e);
    }
  }

  btnRefreshVault.addEventListener('click', loadVaultData);

  // 9. Governance Insights Loader
  async function loadAnalyticsData() {
    try {
      const res = await fetch(`${API_BASE}/analytics`);
      const data = await res.json();

      kpiTotalDocs.textContent = data.total_documents_screened;
      kpiAvgScore.textContent = data.average_compliance_score;
      kpiAvgSpeed.textContent = `${data.average_precheck_latency_ms} ms`;
      kpiTotalOverrides.textContent = data.total_human_overrides;

      // Dimension breakdown bars
      const dims = data.violations_by_dimension || {};
      const maxVal = Math.max(...Object.values(dims), 1);
      
      const dimKeys = ["tone", "terminology", "facts", "claims", "visual", "accessibility"];
      dimensionBars.innerHTML = dimKeys.map(d => {
        const count = dims[d] || 0;
        const pct = Math.round((count / maxVal) * 100);
        return `
          <div class="dim-bar-row">
            <div class="dim-bar-label">
              <span style="text-transform: capitalize;">${d}</span>
              <span>${count} violations</span>
            </div>
            <div class="dim-bar-track">
              <div class="dim-bar-fill" style="width: ${pct}%;"></div>
            </div>
          </div>
        `;
      }).join('');

      // Hotspots
      if (data.ambiguity_hotspots && data.ambiguity_hotspots.length > 0) {
        ambiguityHotspotsList.innerHTML = data.ambiguity_hotspots.map(h => `
          <div class="hotspot-item">
            <div>
              <strong style="color: #FBBF24;">Rule ID: ${h.rule_id}</strong>
              <div style="font-size: 0.75rem; color: var(--text-muted);">${h.alert}</div>
            </div>
            <span class="badge-count" style="color: #F87171;">${h.override_count} overrides</span>
          </div>
        `).join('');
      }

    } catch (e) {
      console.error(e);
    }
  }

  // 10. Dynamic Guidelines Ingestion Upload
  const btnSelectGuidelineFile = document.getElementById('btn-select-guideline-file');
  const guidelineFileInput = document.getElementById('guideline-file-input');
  const guidelineUploadStatus = document.getElementById('guideline-upload-status');
  const guidelinesDropzone = document.getElementById('guidelines-dropzone');

  if (btnSelectGuidelineFile && guidelineFileInput) {
    btnSelectGuidelineFile.addEventListener('click', () => {
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
      guidelineUploadStatus.innerHTML = `<span class="loading-spinner"></span> Ingesting ${file.name} into [${currentProjectId}]... Parsing sections, extracting rules & re-instructing static workers...`;

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
          // Reload vault tables live!
          loadVaultData();
        } else {
          guidelineUploadStatus.className = 'upload-status-bar error';
          guidelineUploadStatus.textContent = `Ingestion error: ${result.message}`;
        }
      } catch (err) {
        guidelineUploadStatus.className = 'upload-status-bar error';
        guidelineUploadStatus.textContent = `Upload failed: ${err.message}`;
      }
    });

    // Drag and drop events
    guidelinesDropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      guidelinesDropzone.style.borderColor = 'var(--accent-cyan)';
    });

    guidelinesDropzone.addEventListener('dragleave', () => {
      guidelinesDropzone.style.borderColor = '';
    });

    guidelinesDropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      guidelinesDropzone.style.borderColor = '';
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        guidelineFileInput.files = e.dataTransfer.files;
        const event = new Event('change');
        guidelineFileInput.dispatchEvent(event);
      }
    });
  }

  // 11. Multi-Project Workspace Functions
  async function loadProjectsList() {
    try {
      const resp = await fetch(`${API_BASE}/projects`);
      const projects = await resp.json();
      if (projectSelector) {
        projectSelector.innerHTML = projects.map(p => `
          <option value="${p.project_id}" ${p.project_id === currentProjectId ? 'selected' : ''}>
            ${p.name}
          </option>
        `).join('');
      }
    } catch (e) {
      console.error("Failed to load projects list", e);
    }
  }

  function switchProject(projectId) {
    currentProjectId = projectId;
    if (projectSelector) {
      projectSelector.value = projectId;
    }
    loadVaultData();
  }

  if (projectSelector) {
    projectSelector.addEventListener('change', (e) => {
      switchProject(e.target.value);
    });
  }

  // Modal Handlers
  if (btnOpenNewProjectModal && newProjectModal) {
    btnOpenNewProjectModal.addEventListener('click', () => {
      newProjectModal.style.display = 'flex';
    });
  }

  function closeProjectModal() {
    if (newProjectModal) newProjectModal.style.display = 'none';
  }

  if (btnCloseProjectModal) btnCloseProjectModal.addEventListener('click', closeProjectModal);
  if (btnCancelProjectModal) btnCancelProjectModal.addEventListener('click', closeProjectModal);

  if (newProjectForm) {
    newProjectForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const pId = document.getElementById('new-project-id').value.trim();
      const pName = document.getElementById('new-project-name').value.trim();
      const pPersona = document.getElementById('new-project-persona').value.trim();
      const pDesc = document.getElementById('new-project-desc').value.trim();
      const pFile = document.getElementById('new-project-file').files[0];

      if (!pId || !pName) {
        alert("Please provide both Project ID and Name");
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
      submitBtn.textContent = "Creating & Ingesting...";

      try {
        const resp = await fetch(`${API_BASE}/projects`, {
          method: 'POST',
          body: formData
        });
        const res = await resp.json();
        if (res.status === 'SUCCESS') {
          alert(`Project '${pName}' created successfully!`);
          closeProjectModal();
          await loadProjectsList();
          switchProject(pId);
        } else {
          alert("Error creating project: " + (res.message || "Unknown error"));
        }
      } catch (err) {
        alert("Network error: " + err.message);
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "Create & Wire Workspace";
      }
    });
  }

  btnRefreshAnalytics.addEventListener('click', loadAnalyticsData);

  // Initialize projects and auto-load benchmark
  loadProjectsList();
  btnLoadSample1.click();
});
