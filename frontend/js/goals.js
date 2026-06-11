import { fetchAPI } from './api.js';
import { toast } from './ui.js';

let goals = [];

// DOM Elements
let goalModal;
let goalModalOverlay;
let goalModalClose;
let goalModalCancel;
let goalModalSave;
let btnAddGoal;

let inputTitle;
let inputCategory;
let inputDate;
let inputDescription;
let inputProgress;
let inputPriority;

let listLong;
let listShort;
let listStepup;

// State
let editingGoalId = null;

// Initialize
export async function initGoals() {
  goalModal = document.getElementById('goal-modal');
  goalModalOverlay = document.getElementById('goal-modal-overlay');
  goalModalClose = document.getElementById('goal-modal-close-btn');
  goalModalCancel = document.getElementById('goal-modal-cancel-btn');
  goalModalSave = document.getElementById('goal-modal-save-btn');
  btnAddGoal = document.getElementById('btn-add-goal');
  inputTitle = document.getElementById('goal-modal-input');
  inputCategory = document.getElementById('goal-modal-category');
  inputDate = document.getElementById('goal-modal-date');
  inputDescription = document.getElementById('goal-modal-description');
  inputProgress = document.getElementById('goal-modal-progress');
  inputPriority = document.getElementById('goal-modal-priority');
  listLong = document.getElementById('goals-list-long');
  listShort = document.getElementById('goals-list-short');
  listStepup = document.getElementById('goals-list-stepup');
  setupEventListeners();
  await loadGoals();
}

function setupEventListeners() {
  btnAddGoal.addEventListener('click', () => {
    console.log("Add Goal clicked");
    openGoalModal();
  });
  goalModalClose.addEventListener('click', closeGoalModal);
  goalModalCancel.addEventListener('click', closeGoalModal);
  goalModalOverlay.addEventListener('click', closeGoalModal);
  goalModalSave.addEventListener('click', saveGoal);
}

async function loadGoals() {
  try {
    goals = await fetchAPI('/goals');
    renderGoals();
  } catch (err) {
    console.error("Failed to load goals", err);
  }
}

function openGoalModal(goal = null) {
  editingGoalId = goal ? goal.id : null;
  document.getElementById('goal-modal-title').textContent = goal ? 'Edit Goal' : 'New Goal';
  
  inputTitle.value = goal ? goal.title : '';
  inputCategory.value = goal ? goal.category : 'Long-Term Goals';
  inputDate.value = goal && goal.target_date ? goal.target_date : '';
  inputDescription.value = goal && goal.description ? goal.description : '';
  inputProgress.value = goal && goal.progress ? goal.progress : 0;
  inputPriority.value = goal && goal.priority ? goal.priority : 0;
  
  goalModal.classList.add('modal--open');
  inputTitle.focus();
}

function closeGoalModal() {
  goalModal.classList.remove('modal--open');
  editingGoalId = null;
}

async function saveGoal() {
  const title = inputTitle.value.trim();
  if (!title) {
    toast('Goal title is required');
    return;
  }

  const payload = {
    title,
    category: inputCategory.value,
    target_date: inputDate.value || null,
    description: inputDescription.value.trim(),
    progress: parseInt(inputProgress.value) || 0,
    priority: parseInt(inputPriority.value) || 0
  };

  try {
    if (editingGoalId) {
      await fetchAPI(`/goals/${editingGoalId}`, {
        method: 'PUT',
        body: JSON.stringify(payload)
      });
      toast('Goal updated');
    } else {
      await fetchAPI('/goals', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      toast('Goal created');
    }
    closeGoalModal();
    await loadGoals();
  } catch (err) {
    console.error('Failed to save goal:', err);
    toast('Failed to create goal');
  }
}

async function deleteGoal(id, e) {
  e.stopPropagation();
  if (!confirm('Delete this goal?')) return;
  try {
    await fetchAPI(`/goals/${id}`, { method: 'DELETE' });
    toast('Goal deleted');
    await loadGoals();
  } catch (err) {
    console.error(err);
  }
}

async function toggleGoal(id, completed, e) {
  e.stopPropagation();
  try {
    await fetchAPI(`/goals/${id}`, {
      method: 'PUT',
      body: JSON.stringify({ completed: completed ? 0 : 1 })
    });
    await loadGoals();
  } catch (err) {
    console.error(err);
  }
}

function renderGoals() {
  listLong.innerHTML = '';
  listShort.innerHTML = '';
  listStepup.innerHTML = '';

  goals.forEach(goal => {
    const el = document.createElement('div');
    el.className = 'goal-card';
    el.onclick = () => openGoalModal(goal);

    const isDone = goal.completed === 1;
    el.style.opacity = isDone ? '0.6' : '1';

    el.innerHTML = `
      <div class="goal-card__meta">
        <span>${goal.target_date || 'No Date'}</span>
        <div style="display:flex; gap: 8px; align-items:center;">
          <input type="checkbox" ${isDone ? 'checked' : ''} style="cursor:pointer;" class="goal-check">
          <button class="icon-btn goal-del" style="font-size:14px; padding:0;">✕</button>
        </div>
      </div>
      <div class="goal-card__title" style="text-decoration: ${isDone ? 'line-through' : 'none'}">${goal.title}</div>
      <div class="progress-bar-container">
        <div class="progress-bar-fill" style="width: ${goal.progress}%"></div>
      </div>
    `;

    el.querySelector('.goal-check').addEventListener('click', (e) => toggleGoal(goal.id, isDone, e));
    el.querySelector('.goal-del').addEventListener('click', (e) => deleteGoal(goal.id, e));

    if (goal.category === 'Long-Term Goals') listLong.appendChild(el);
    else if (goal.category === 'Short-Term Goals') listShort.appendChild(el);
    else if (goal.category === 'Step-Up Goals') listStepup.appendChild(el);
  });
}

// Auto-init
try {
  console.log("Goals module loaded, initializing...");
  initGoals().catch(err => console.error("Goals init async error:", err));
} catch (e) {
  console.error("Goals init sync error:", e);
}
