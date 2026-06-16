import { fetchAPI } from './api.js';
import { toast } from './ui.js';

let projects = [];
let liveTickInterval = null;

// DOM Elements
let projectModal;
let projectModalOverlay;
let projectModalClose;
let projectModalCancel;
let projectModalSave;
let btnAddProject;

let inputTitle;
let inputDeadline;
let inputDescription;
let inputPriority;
let inputMilestones;
let inputGoal;

let projectsGrid;

// Milestone Modal DOM
let milestoneModal;
let milestoneModalOverlay;
let milestoneModalClose;
let milestoneInput;
let milestoneAddBtn;
let milestonesList;

// Completed Projects DOM
let completedProjectsGrid;
let completedProjectsToggleBtn;
let completedProjectsExpanded = false;

// State
let editingProjectId = null;
let activeMilestoneProjectId = null;

// Initialize
export async function initProjects() {
  projectModal = document.getElementById('project-modal');
  projectModalOverlay = document.getElementById('project-modal-overlay');
  projectModalClose = document.getElementById('project-modal-close-btn');
  projectModalCancel = document.getElementById('project-modal-cancel-btn');
  projectModalSave = document.getElementById('project-modal-save-btn');
  btnAddProject = document.getElementById('btn-add-project');
  inputTitle = document.getElementById('project-modal-input');
  inputDeadline = document.getElementById('project-modal-deadline');
  inputDescription = document.getElementById('project-modal-description');
  inputPriority = document.getElementById('project-modal-priority');
  inputMilestones = document.getElementById('project-modal-milestones');
  inputGoal = document.getElementById('project-modal-goal');
  projectsGrid = document.getElementById('projects-grid');
  milestoneModal = document.getElementById('milestone-modal');
  milestoneModalOverlay = document.getElementById('milestone-modal-overlay');
  milestoneModalClose = document.getElementById('milestone-modal-close-btn');
  milestoneInput = document.getElementById('milestone-modal-input');
  milestoneAddBtn = document.getElementById('milestone-modal-add-btn');
  milestonesList = document.getElementById('milestones-modal-list');
  
  completedProjectsGrid = document.getElementById('completed-projects-grid');
  completedProjectsToggleBtn = document.getElementById('completed-projects-toggle-btn');
  
  setupEventListeners();
  await loadProjects();
}

function setupEventListeners() {
  btnAddProject.addEventListener('click', () => {
    console.log("Add Project clicked");
    openProjectModal();
  });
  projectModalClose.addEventListener('click', closeProjectModal);
  projectModalCancel.addEventListener('click', closeProjectModal);
  projectModalOverlay.addEventListener('click', closeProjectModal);
  projectModalSave.addEventListener('click', saveProject);

  milestoneModalClose.addEventListener('click', closeMilestoneModal);
  milestoneModalOverlay.addEventListener('click', closeMilestoneModal);
  milestoneAddBtn.addEventListener('click', addMilestone);
  
  if (completedProjectsToggleBtn) {
    completedProjectsToggleBtn.addEventListener('click', () => {
      completedProjectsExpanded = !completedProjectsExpanded;
      renderCompletedVisibility();
    });
  }
}

async function loadProjects() {
  try {
    projects = await fetchAPI('/projects');
    renderProjects();
    startLiveTick();
  } catch (err) {
    console.error("Failed to load projects", err);
  }
}

function renderCompletedVisibility() {
  if (!completedProjectsGrid || !completedProjectsToggleBtn) return;
  if (completedProjectsExpanded) {
    completedProjectsGrid.classList.remove('hidden');
    completedProjectsToggleBtn.textContent = '🏆 Completed Projects ▲';
  } else {
    completedProjectsGrid.classList.add('hidden');
    completedProjectsToggleBtn.textContent = '🏆 Completed Projects ▼';
  }
}

async function openProjectModal(project = null) {
  editingProjectId = project ? project.id : null;
  document.getElementById('project-modal-title').textContent = project ? 'Edit Project' : 'New Project';
  
  inputTitle.value = project ? project.title : '';
  inputDeadline.value = project ? project.deadline : '';
  inputDescription.value = project && project.description ? project.description : '';
  inputPriority.value = project && project.priority ? project.priority : 0;
  
  if (project) {
    inputMilestones.parentElement.style.display = 'none'; // Hide initial milestones when editing
  } else {
    inputMilestones.parentElement.style.display = 'block';
    inputMilestones.value = '';
  }

  // Populate goals select options
  if (inputGoal) {
    inputGoal.innerHTML = '<option value="">-- No Link --</option>';
    try {
      const goals = await fetchAPI('/goals') || [];
      goals.forEach(g => {
        if (g.completed === 0 || (project && project.goal_id === g.id)) {
          const opt = document.createElement('option');
          opt.value = g.id;
          opt.textContent = g.title;
          inputGoal.appendChild(opt);
        }
      });
      inputGoal.value = (project && project.goal_id) ? project.goal_id : '';
    } catch (err) {
      console.warn("Failed to load goals for project link:", err);
    }
  }
  
  projectModal.classList.add('modal--open');
  inputTitle.focus();
}

function closeProjectModal() {
  projectModal.classList.remove('modal--open');
  editingProjectId = null;
}

async function saveProject() {
  const title = inputTitle.value.trim();
  const deadline = inputDeadline.value;

  if (!title || !deadline) {
    toast('Title and deadline are required');
    return;
  }

  const payload = { 
    title, 
    deadline,
    description: inputDescription.value.trim(),
    priority: parseInt(inputPriority.value) || 0,
    goal_id: inputGoal && inputGoal.value ? parseInt(inputGoal.value) : null
  };

  if (!editingProjectId) {
    const msStr = inputMilestones.value.trim();
    if (msStr) {
      payload.initial_milestones = msStr.split(',').map(s => s.trim()).filter(s => s);
    }
  }

  try {
    if (editingProjectId) {
      await fetchAPI(`/projects/${editingProjectId}`, {
        method: 'PUT',
        body: JSON.stringify(payload)
      });
      toast('Project updated');
    } else {
      await fetchAPI('/projects', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      toast('Project created');
    }
    closeProjectModal();
    await loadProjects();
  } catch (err) {
    console.error('Failed to save project:', err);
    toast('Failed to create project');
  }
}

async function deleteProject(id, e) {
  e.stopPropagation();
  if (!confirm('Delete this project?')) return;
  try {
    await fetchAPI(`/projects/${id}`, { method: 'DELETE' });
    toast('Project deleted');
    await loadProjects();
  } catch (err) {
    console.error(err);
  }
}

// -- Milestones Logic --

function openMilestoneModal(project, e) {
  if (e) e.stopPropagation();
  activeMilestoneProjectId = project.id;
  milestoneInput.value = '';
  renderMilestonesModal(project);
  milestoneModal.classList.add('modal--open');
  milestoneInput.focus();
}

function closeMilestoneModal() {
  milestoneModal.classList.remove('modal--open');
  activeMilestoneProjectId = null;
}

async function addMilestone() {
  const title = milestoneInput.value.trim();
  if (!title) return;

  try {
    const updatedProj = await fetchAPI(`/projects/${activeMilestoneProjectId}/milestones`, {
      method: 'POST',
      body: JSON.stringify({ title })
    });
    
    // Update local state
    const idx = projects.findIndex(p => p.id === activeMilestoneProjectId);
    if (idx !== -1) projects[idx] = updatedProj;
    
    milestoneInput.value = '';
    renderMilestonesModal(updatedProj);
    renderProjects();
  } catch (err) {
    console.error(err);
  }
}

async function toggleMilestone(milestoneId, isCompleted) {
  try {
    const updatedProj = await fetchAPI(`/projects/milestones/${milestoneId}`, {
      method: 'PUT',
      body: JSON.stringify({ completed: isCompleted ? 0 : 1 })
    });
    
    // Update local state
    const idx = projects.findIndex(p => p.id === activeMilestoneProjectId);
    if (idx !== -1) projects[idx] = updatedProj;
    
    renderMilestonesModal(updatedProj);
    renderProjects();
  } catch (err) {
    console.error(err);
  }
}

async function deleteMilestone(milestoneId) {
  try {
    const updatedProj = await fetchAPI(`/projects/milestones/${milestoneId}`, {
      method: 'DELETE'
    });
    
    // Update local state
    const idx = projects.findIndex(p => p.id === activeMilestoneProjectId);
    if (idx !== -1) projects[idx] = updatedProj;
    
    renderMilestonesModal(updatedProj);
    renderProjects();
  } catch (err) {
    console.error(err);
  }
}

function renderMilestonesModal(project) {
  milestonesList.innerHTML = '';
  if (!project.milestones || project.milestones.length === 0) {
    milestonesList.innerHTML = '<div style="color:var(--muted); font-size:12px; margin-top:8px;">No milestones yet.</div>';
    return;
  }

  project.milestones.forEach(m => {
    const el = document.createElement('div');
    el.className = 'milestone-item';
    
    const isDone = m.completed === 1;
    el.innerHTML = `
      <input type="checkbox" ${isDone ? 'checked' : ''}>
      <span class="milestone-title-text" style="flex:1; font-size:13px; text-decoration: ${isDone ? 'line-through' : 'none'}">${m.title}</span>
      <button class="icon-btn milestone-edit-btn" title="Edit Milestone" style="font-size:12px; padding:2px; color:var(--muted); margin-right: 4px;">✎</button>
      <button class="icon-btn milestone-del-btn" title="Delete Milestone" style="font-size:12px; padding:2px; color:var(--muted)">✕</button>
    `;

    el.querySelector('input').addEventListener('click', () => toggleMilestone(m.id, isDone));
    el.querySelector('.milestone-del-btn').addEventListener('click', () => deleteMilestone(m.id));
    
    const textSpan = el.querySelector('.milestone-title-text');
    const editBtn = el.querySelector('.milestone-edit-btn');
    
    editBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      
      if (el.querySelector('.milestone-edit-input')) return;
      
      const input = document.createElement('input');
      input.type = 'text';
      input.className = 'modal-input milestone-edit-input';
      input.value = m.title;
      input.style.flex = '1';
      input.style.minHeight = '30px';
      input.style.height = '30px';
      input.style.fontSize = '13px';
      input.style.padding = '0 8px';
      input.style.marginRight = '8px';
      
      textSpan.replaceWith(input);
      input.focus();
      input.select();
      
      editBtn.innerHTML = '💾';
      editBtn.title = 'Save Title';
      
      const saveAction = async () => {
        const newTitle = input.value.trim();
        if (newTitle && newTitle !== m.title) {
          try {
            const updatedProj = await fetchAPI(`/projects/milestones/${m.id}`, {
              method: 'PUT',
              body: JSON.stringify({ title: newTitle })
            });
            const idx = projects.findIndex(p => p.id === activeMilestoneProjectId);
            if (idx !== -1) projects[idx] = updatedProj;
            renderMilestonesModal(updatedProj);
            renderProjects();
          } catch (err) {
            console.error(err);
            toast('Failed to update milestone');
          }
        } else {
          renderMilestonesModal(project);
        }
      };
      
      input.addEventListener('keydown', (evt) => {
        if (evt.key === 'Enter') {
          saveAction();
        } else if (evt.key === 'Escape') {
          renderMilestonesModal(project);
        }
      });
      
      editBtn.onclick = (evt) => {
        evt.stopPropagation();
        saveAction();
      };
    });
    
    milestonesList.appendChild(el);
  });
}

// -- Render & Live Tick --

function renderProjects() {
  projectsGrid.innerHTML = '';
  if (completedProjectsGrid) completedProjectsGrid.innerHTML = '';

  const activeProjects = projects.filter(p => p.completed === 0);
  const completedProjects = projects.filter(p => p.completed === 1);

  // Render Active Projects
  activeProjects.forEach(project => {
    const countdown = project.countdown;
    const el = document.createElement('div');
    el.className = 'project-card';
    el.setAttribute('data-urgency', countdown.urgency);
    el.setAttribute('data-deadline', project.deadline);
    
    el.onclick = (e) => openMilestoneModal(project, e);

    const total = project.milestones.length;
    const completed = project.milestones.filter(m => m.completed === 1).length;

    // FCFS top uncompleted todo
    const activeMilestones = project.milestones.filter(m => m.completed === 0);
    const topTodo = activeMilestones.length > 0 ? activeMilestones[0] : null;
    let topTodoHtml = '';
    if (project.milestones.length === 0) {
      topTodoHtml = `<div class="project-card__top-todo" style="font-size:12px; color:var(--muted); font-style:italic;">No milestones yet. Click to manage.</div>`;
    } else if (!topTodo) {
      topTodoHtml = `<div class="project-card__top-todo" style="font-size:12px; color:var(--green); font-weight:500;">All caught up! 🎉</div>`;
    } else {
      topTodoHtml = `
        <div class="project-card__top-todo" style="font-size:12px; color:var(--text); background:rgba(255,255,255,0.03); padding:4px 8px; border-radius:4px; border:1px solid rgba(255,255,255,0.05); margin:4px 0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">
          📌 <span style="font-weight:600; color:var(--green)">Next ToDo:</span> ${topTodo.title}
        </div>
      `;
    }

    const goalLinkHtml = project.goal_title 
      ? `<div class="project-card__goal-link" style="font-size:10px; color:#4a90e2; font-weight:600; margin-top:2px;">🎯 Goal: ${project.goal_title}</div>`
      : '';

    el.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:flex-start; gap: 8px;">
        <div>
          <div class="project-card__title">${project.title}</div>
          ${goalLinkHtml}
        </div>
        <div style="display:flex; gap: 8px; align-items:center;">
          <button class="icon-btn project-complete" title="Mark Completed" style="font-size:14px; padding:2px; color:var(--muted)">✓</button>
          <button class="icon-btn project-edit" title="Edit Project" style="font-size:14px; padding:2px; color:var(--muted)">✎</button>
          <button class="icon-btn project-del" title="Delete Project" style="font-size:14px; padding:2px; color:var(--muted)">✕</button>
        </div>
      </div>
      <div class="project-card__countdown" data-live="${countdown.live}">${countdown.text}</div>
      <div class="progress-bar-container" style="margin-top: 8px;">
        <div class="progress-bar-fill" style="width: ${project.progress}%"></div>
      </div>
      ${topTodoHtml}
      <div class="project-card__milestones" style="margin-top: 4px;">
        <span>${completed}/${total} Milestones</span>
        <button class="btn-manage-milestones" style="font-size:11px; color:var(--green); background:var(--green-glow); padding:2px 6px; border-radius:4px;">Manage</button>
      </div>
    `;

    el.querySelector('.project-complete').addEventListener('click', async (e) => {
      e.stopPropagation();
      if (!confirm(`Mark project "${project.title}" as completed?`)) return;
      try {
        await fetchAPI(`/projects/${project.id}`, {
          method: 'PUT',
          body: JSON.stringify({
            completed: 1,
            completed_at: new Date().toISOString()
          })
        });
        toast('Project completed! 🏆');
        await loadProjects();
      } catch (err) {
        console.error(err);
        toast('Failed to complete project');
      }
    });

    el.querySelector('.project-edit').addEventListener('click', (e) => {
      e.stopPropagation();
      openProjectModal(project);
    });

    el.querySelector('.project-del').addEventListener('click', (e) => deleteProject(project.id, e));
    el.querySelector('.btn-manage-milestones').addEventListener('click', (e) => openMilestoneModal(project, e));

    projectsGrid.appendChild(el);
  });

  // Render Completed Projects
  completedProjects.forEach(project => {
    const el = document.createElement('div');
    el.className = 'project-card';
    el.style.opacity = '0.75';
    el.setAttribute('data-urgency', 'COMPLETED');
    
    el.onclick = (e) => openMilestoneModal(project, e);

    const total = project.milestones.length;
    const completed = project.milestones.filter(m => m.completed === 1).length;
    
    const completedDateFormatted = project.completed_at ? new Date(project.completed_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }) : 'Unknown date';
    
    const goalLinkHtml = project.goal_title 
      ? `<div class="project-card__goal-link" style="font-size:10px; color:#4a90e2; font-weight:600; margin-top:2px; text-decoration:none;">🎯 Goal: ${project.goal_title}</div>`
      : '';

    el.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:flex-start; gap: 8px;">
        <div>
          <div class="project-card__title" style="text-decoration: line-through; color: var(--muted);">${project.title}</div>
          ${goalLinkHtml}
        </div>
        <div style="display:flex; gap: 8px; align-items:center;">
          <button class="icon-btn project-restore" title="Restore to Active" style="font-size:14px; padding:2px; color:var(--muted)">↺</button>
          <button class="icon-btn project-del" title="Delete Project" style="font-size:14px; padding:2px; color:var(--muted)">✕</button>
        </div>
      </div>
      <div class="project-card__countdown" style="color: var(--muted-2); font-size: 12px; margin-top: 2px;">🏆 Completed on ${completedDateFormatted}</div>
      <div class="progress-bar-container" style="margin-top: 8px;">
        <div class="progress-bar-fill" style="width: ${project.progress}%; background: var(--muted-2);"></div>
      </div>
      <div class="project-card__milestones" style="margin-top: 8px;">
        <span>${completed}/${total} Milestones</span>
        <button class="btn-manage-milestones" style="font-size:11px; color:var(--muted-2); background:rgba(255,255,255,0.03); padding:2px 6px; border-radius:4px;">View</button>
      </div>
    `;

    el.querySelector('.project-restore').addEventListener('click', async (e) => {
      e.stopPropagation();
      if (!confirm(`Restore project "${project.title}" to active?`)) return;
      try {
        await fetchAPI(`/projects/${project.id}`, {
          method: 'PUT',
          body: JSON.stringify({
            completed: 0,
            completed_at: null
          })
        });
        toast('Project restored to active');
        await loadProjects();
      } catch (err) {
        console.error(err);
        toast('Failed to restore project');
      }
    });

    el.querySelector('.project-del').addEventListener('click', (e) => deleteProject(project.id, e));
    el.querySelector('.btn-manage-milestones').addEventListener('click', (e) => openMilestoneModal(project, e));

    completedProjectsGrid.appendChild(el);
  });

  renderCompletedVisibility();
}

function startLiveTick() {
  if (liveTickInterval) clearInterval(liveTickInterval);
  
  liveTickInterval = setInterval(() => {
    const liveCards = document.querySelectorAll('.project-card__countdown[data-live="true"]');
    if (liveCards.length === 0) return;

    liveCards.forEach(el => {
      const parent = el.closest('.project-card');
      let deadlineStr = parent.getAttribute('data-deadline');
      if (deadlineStr.length === 10) {
        deadlineStr += 'T23:59:59';
      }
      const deadline = new Date(deadlineStr).getTime();
      const now = new Date().getTime();
      const diffMs = deadline - now;
      
      if (diffMs <= 0) {
        el.textContent = 'Overdue';
        el.setAttribute('data-live', 'false');
        parent.setAttribute('data-urgency', 'RED');
        return;
      }
      
      const totalSeconds = Math.floor(diffMs / 1000);
      const hours = Math.floor(totalSeconds / 3600);
      const d = Math.floor(hours / 24);
      const h = hours % 24;
      
      if (d >= 2) {
        el.textContent = `${d} days left`;
      } else if (d > 0) {
        el.textContent = `${d} day ${h} hour${h !== 1 ? 's' : ''} left`;
      } else {
        if (hours > 0) {
          el.textContent = `${h} hour${h !== 1 ? 's' : ''} left`;
        } else {
          const minutes = Math.floor((totalSeconds % 3600) / 60);
          el.textContent = `${minutes} min${minutes !== 1 ? 's' : ''} left`;
        }
      }
    });
  }, 60000); // tick every minute
}

// Auto-init
try {
  console.log("Projects module loaded, initializing...");
  initProjects().catch(err => console.error("Projects init async error:", err));
} catch (e) {
  console.error("Projects init sync error:", e);
}
