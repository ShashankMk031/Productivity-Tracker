import { fetchAPI } from './api.js';
import { toast } from './ui.js';

let maxZIndex = 1;
let currentSearchQuery = "";
let searchDebounceTimeout = null;

// Premium Preset pastels matching solid colors and their contrasting text colors
const PRESETS = {
  '#fef3c7': { bg: '#fef3c7', text: '#1e293b' }, // Yellow
  '#ffe4e6': { bg: '#fce7f3', text: '#831843' }, // Pink
  '#e0f2fe': { bg: '#e0f2fe', text: '#0369a1' }, // Blue
  '#ecfdf5': { bg: '#d1fae5', text: '#065f46' }, // Green
  '#ede9fe': { bg: '#f3e8ff', text: '#5b21b6' }  // Purple
};

function getBorderColor(hex) {
  if (!hex || !hex.startsWith('#')) return 'rgba(255, 255, 255, 0.15)';
  let r = parseInt(hex.slice(1, 3), 16);
  let g = parseInt(hex.slice(3, 5), 16);
  let b = parseInt(hex.slice(5, 7), 16);
  
  // Darken border by 18% for high contrast outline definition
  r = Math.max(0, Math.floor(r * 0.82));
  g = Math.max(0, Math.floor(g * 0.82));
  b = Math.max(0, Math.floor(b * 0.82));
  
  return `rgb(${r}, ${g}, ${b})`;
}

document.addEventListener("DOMContentLoaded", () => {
  initBoard();
});

async function initBoard() {
  console.log("[Board Canvas] Initializing board...");
  
  const searchInput = document.getElementById("board-search-input");
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      currentSearchQuery = e.target.value;
      clearTimeout(searchDebounceTimeout);
      searchDebounceTimeout = setTimeout(() => {
        renderBoard(currentSearchQuery);
      }, 300);
    });
  }

  const archiveBtn = document.getElementById("btn-archive-completed");
  if (archiveBtn) {
    archiveBtn.addEventListener("click", handleArchiveCompleted);
  }

  const deleteBtn = document.getElementById("btn-delete-completed");
  if (deleteBtn) {
    deleteBtn.addEventListener("click", handleDeleteCompleted);
  }

  await renderBoard();
  
  const viewport = document.getElementById("board-canvas-viewport");
  if (viewport) {
    viewport.scrollLeft = 0;
    viewport.scrollTop = 0;
  }
}

async function renderBoard(query = "") {
  const canvas = document.getElementById("board-canvas");
  if (!canvas) return;

  try {
    const url = query ? `/sticky-notes?query=${encodeURIComponent(query)}` : '/sticky-notes';
    const notes = await fetchAPI(url);
    canvas.innerHTML = "";

    if (notes.length > 0) {
      maxZIndex = Math.max(...notes.map(n => n.z_index || 1), 1);
    }

    notes.forEach(note => {
      const noteEl = createStickyNoteElement(note);
      canvas.appendChild(noteEl);
    });
  } catch (err) {
    console.error("Failed to load sticky notes", err);
    toast("Error loading sticky notes board", "error");
  }
}

function createStickyNoteElement(note) {
  const el = document.createElement("div");
  el.id = `sticky-${note.id}`;
  el.className = `sticky-note ${note.is_completed ? 'sticky-completed' : ''}`;
  el.style.left = `${note.position_x}px`;
  el.style.top = `${note.position_y}px`;
  el.style.zIndex = note.z_index;

  // Apply saved dynamic rotation angle
  const rotation = note.rotation !== undefined ? note.rotation : 0.0;
  el.style.transform = `rotate(${rotation}deg)`;

  // Apply saved dynamic size
  el.style.width = `${note.width || 240}px`;
  el.style.height = `${note.height || 135}px`;

  // Apply custom background and text color styling
  const currentBgColor = note.color || '#fef3c7';
  const currentTextColor = note.text_color || '#1e293b';
  el.style.backgroundColor = currentBgColor;
  el.style.color = currentTextColor;
  el.style.borderColor = getBorderColor(currentBgColor);

  // Set up html layout
  const colorSelectorHTML = Object.keys(PRESETS).map(hex => 
    `<div class="color-dot" style="background: ${hex};" data-color="${hex}"></div>`
  ).join('');

  el.innerHTML = `
    <div class="fridge-magnet"></div>
    <div class="sticky-header" style="background: rgba(0, 0, 0, 0.08);">
      <div class="sticky-header-left">
        <input type="checkbox" class="sticky-complete-checkbox" ${note.is_completed ? 'checked' : ''} title="Mark Completed" />
        ${note.is_draft ? '<span class="sticky-draft-badge">Draft</span>' : ''}
      </div>
      <div class="sticky-header-right">
        ${note.is_draft ? `<button class="sticky-action-btn sticky-pin-btn" title="Pin note to board">📌 Pin</button>` : ''}
        <button class="sticky-action-btn sticky-delete-btn" title="Delete Note">✕</button>
      </div>
    </div>
    <div class="sticky-body">
      <textarea class="sticky-textarea" placeholder="${note.is_draft ? 'Type a new thought to draft...' : 'Type note contents...'}" style="color: ${currentTextColor};">${note.content || ''}</textarea>
    </div>
    <div class="sticky-footer" style="background: rgba(0, 0, 0, 0.03);">
      <div class="sticky-tag-container">
        <span class="sticky-tag-icon">🏷️</span>
        <input type="text" class="sticky-tag-input" placeholder="add tag..." value="${note.tag || ''}" style="color: ${currentTextColor};" />
      </div>
      <div class="sticky-color-selector" style="display: flex; align-items: center; gap: 8px;">
        <div style="display: flex; gap: 4px; align-items: center;">
          ${colorSelectorHTML}
        </div>
        <div style="display: flex; align-items: center; gap: 6px; border-left: 1px solid rgba(0,0,0,0.12); padding-left: 6px; margin-left: 2px;">
          <label style="font-size: 11px; cursor: pointer; display: flex; align-items: center; justify-content: center; width: 16px; height: 16px; margin: 0; position: relative;" title="Custom Background Color">
            🎨
            <input type="color" class="sticky-bg-color-picker" value="${currentBgColor}" style="position: absolute; left: -9999px; opacity: 0; width: 1px; height: 1px; border: none;" />
          </label>
          <label style="font-size: 11px; cursor: pointer; display: flex; align-items: center; justify-content: center; width: 16px; height: 16px; margin: 0; position: relative;" title="Custom Text Color">
            ✍️
            <input type="color" class="sticky-text-color-picker" value="${currentTextColor}" style="position: absolute; left: -9999px; opacity: 0; width: 1px; height: 1px; border: none;" />
          </label>
          <button class="sticky-action-btn sticky-rotate-btn" title="Click and drag to rotate, or use two fingers on trackpad" style="font-size: 11px; cursor: grab; user-select: none; border: none; background: transparent; padding: 2px; margin-left: 2px;">
            🔄
          </button>
        </div>
      </div>
      <span class="save-indicator"></span>
    </div>
  `;

  const bgPickerInput = el.querySelector(".sticky-bg-color-picker");
  const textPickerInput = el.querySelector(".sticky-text-color-picker");
  const rotateBtn = el.querySelector(".sticky-rotate-btn");

  // Pointer drag-to-rotate listener (Click & hold / touch drag)
  rotateBtn.addEventListener("pointerdown", (e) => {
    if (e.button !== 0) return;
    e.preventDefault();
    e.stopPropagation();
    rotateBtn.setPointerCapture(e.pointerId);

    const rect = el.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;

    const startX = e.clientX;
    const startY = e.clientY;
    const startDx = startX - centerX;
    const startDy = startY - centerY;
    const startAngle = Math.atan2(startDy, startDx) * (180 / Math.PI);
    const initialNoteRotation = note.rotation !== undefined ? note.rotation : 0.0;

    let finalAngle = initialNoteRotation;

    const onPointerMove = (moveEv) => {
      const dx = moveEv.clientX - centerX;
      const dy = moveEv.clientY - centerY;
      const currentAngle = Math.atan2(dy, dx) * (180 / Math.PI);
      const angleDiff = currentAngle - startAngle;
      finalAngle = Math.round((initialNoteRotation + angleDiff) % 360);
      el.style.transform = `rotate(${finalAngle}deg)`;
    };

    const onPointerUp = async (upEv) => {
      rotateBtn.releasePointerCapture(upEv.pointerId);
      rotateBtn.removeEventListener("pointermove", onPointerMove);
      rotateBtn.removeEventListener("pointerup", onPointerUp);

      note.rotation = finalAngle;
      await updateStickyOnServer(note.id, { rotation: finalAngle });
    };

    rotateBtn.addEventListener("pointermove", onPointerMove);
    rotateBtn.addEventListener("pointerup", onPointerUp);
  });

  // Trackpad / Touchpad gesture rotation listener (macOS Safari & Chrome)
  let initialGestureRotation = 0;
  el.addEventListener("gesturestart", (e) => {
    e.preventDefault();
    initialGestureRotation = note.rotation !== undefined ? note.rotation : 0.0;
  });

  el.addEventListener("gesturechange", (e) => {
    e.preventDefault();
    const finalAngle = Math.round((initialGestureRotation + e.rotation) % 360);
    el.style.transform = `rotate(${finalAngle}deg)`;
  });

  el.addEventListener("gestureend", async (e) => {
    e.preventDefault();
    const finalAngle = Math.round((initialGestureRotation + e.rotation) % 360);
    note.rotation = finalAngle;
    await updateStickyOnServer(note.id, { rotation: finalAngle });
  });

  // Bind pointer down to bring to front immediately on any interaction
  el.addEventListener("pointerdown", () => {
    const currentZ = parseInt(el.style.zIndex) || 1;
    if (currentZ < maxZIndex) {
      maxZIndex += 1;
      el.style.zIndex = maxZIndex;
      updateStickyOnServer(note.id, { z_index: maxZIndex });
    }
  });

  // Drag-and-drop listener on header only
  const header = el.querySelector(".sticky-header");
  header.addEventListener("pointerdown", (e) => {
    if (e.button !== 0) return;
    if (e.target.closest("input") || e.target.closest("button") || e.target.closest("label")) {
      return;
    }

    e.preventDefault();
    header.setPointerCapture(e.pointerId);

    const startX = e.clientX;
    const startY = e.clientY;
    const initialLeft = parseFloat(el.style.left) || 100;
    const initialTop = parseFloat(el.style.top) || 100;
    let hasMoved = false;

    const onPointerMove = (moveEv) => {
      hasMoved = true;
      const dx = moveEv.clientX - startX;
      const dy = moveEv.clientY - startY;

      let newLeft = initialLeft + dx;
      let newTop = initialTop + dy;

      newLeft = Math.max(0, Math.min(3260, newLeft));
      newTop = Math.max(0, Math.min(3300, newTop));

      el.style.left = `${newLeft}px`;
      el.style.top = `${newTop}px`;
    };

    const onPointerUp = (upEv) => {
      header.releasePointerCapture(upEv.pointerId);
      header.removeEventListener("pointermove", onPointerMove);
      header.removeEventListener("pointerup", onPointerUp);

      if (hasMoved) {
        const finalLeft = parseFloat(el.style.left);
        const finalTop = parseFloat(el.style.top);
        updateStickyOnServer(note.id, { position_x: finalLeft, position_y: finalTop });
      }
    };

    header.addEventListener("pointermove", onPointerMove);
    header.addEventListener("pointerup", onPointerUp);
  });

  // Track resizing to update size on server on pointer release
  el.addEventListener("pointerup", () => {
    const curW = el.offsetWidth;
    const curH = el.offsetHeight;
    if (curW !== note.width || curH !== note.height) {
      updateStickyOnServer(note.id, { width: curW, height: curH });
      note.width = curW;
      note.height = curH;
    }
  });

  // Bind checkbox toggle complete
  const checkbox = el.querySelector(".sticky-complete-checkbox");
  checkbox.addEventListener("change", async (e) => {
    const isCompleted = e.target.checked;
    if (isCompleted) {
      el.classList.add("sticky-completed");
    } else {
      el.classList.remove("sticky-completed");
    }
    await updateStickyOnServer(note.id, { is_completed: isCompleted });
  });

  // Bind delete button
  const deleteBtn = el.querySelector(".sticky-delete-btn");
  deleteBtn.addEventListener("click", async () => {
    if (confirm("Are you sure you want to delete this sticky note?")) {
      try {
        await fetchAPI(`/sticky-notes/${note.id}`, { method: 'DELETE' });
        toast("Sticky note deleted");
        await renderBoard(currentSearchQuery);
      } catch (err) {
        toast("Failed to delete note", "error");
      }
    }
  });

  // Bind Pin button (only present on draft notes)
  const pinBtn = el.querySelector(".sticky-pin-btn");
  if (pinBtn) {
    pinBtn.addEventListener("click", async () => {
      try {
        await fetchAPI(`/sticky-notes/${note.id}`, {
          method: 'PUT',
          body: JSON.stringify({ is_draft: false })
        });
        toast("Note pinned to board! New draft created. 📝");
        await renderBoard(currentSearchQuery);
      } catch (err) {
        toast("Failed to pin note", "error");
      }
    });
  }

  // Bind direct editing of content text (Debounced Autosave)
  const textarea = el.querySelector(".sticky-textarea");
  const saveIndicator = el.querySelector(".save-indicator");
  let contentTimeout = null;

  textarea.addEventListener("input", () => {
    if (saveIndicator) saveIndicator.textContent = "Saving...";
    clearTimeout(contentTimeout);
    contentTimeout = setTimeout(async () => {
      try {
        await fetchAPI(`/sticky-notes/${note.id}`, {
          method: 'PUT',
          body: JSON.stringify({ content: textarea.value })
        });
        if (saveIndicator) saveIndicator.textContent = "Saved";
      } catch (err) {
        if (saveIndicator) saveIndicator.textContent = "Failed";
      }
    }, 600);
  });

  // Bind tag input editing (Debounced Autosave)
  const tagInput = el.querySelector(".sticky-tag-input");
  let tagTimeout = null;

  tagInput.addEventListener("input", () => {
    if (saveIndicator) saveIndicator.textContent = "Saving...";
    clearTimeout(tagTimeout);
    tagTimeout = setTimeout(async () => {
      try {
        let tagValue = tagInput.value.trim();
        if (tagValue && !tagValue.startsWith("#")) {
          tagValue = "#" + tagValue;
          tagInput.value = tagValue;
        }
        await fetchAPI(`/sticky-notes/${note.id}`, {
          method: 'PUT',
          body: JSON.stringify({ tag: tagValue || "" })
        });
        if (saveIndicator) saveIndicator.textContent = "Saved";
      } catch (err) {
        if (saveIndicator) saveIndicator.textContent = "Failed";
      }
    }, 800);
  });

  // Bind color selector dots
  const colorDots = el.querySelectorAll(".color-dot");
  colorDots.forEach(dot => {
    dot.addEventListener("click", async () => {
      const selectedColor = dot.getAttribute("data-color");
      const preset = PRESETS[selectedColor];
      if (preset) {
        el.style.backgroundColor = preset.bg;
        el.style.color = preset.text;
        el.style.borderColor = getBorderColor(preset.bg);
        textarea.style.color = preset.text;
        tagInput.style.color = preset.text;
        bgPickerInput.value = preset.bg;
        textPickerInput.value = preset.text;

        await updateStickyOnServer(note.id, { color: preset.bg, text_color: preset.text });
      }
    });
  });

  // Bind custom background color picker
  bgPickerInput.addEventListener("input", (e) => {
    const selectedBg = e.target.value;
    el.style.backgroundColor = selectedBg;
    el.style.borderColor = getBorderColor(selectedBg);
  });

  bgPickerInput.addEventListener("change", async (e) => {
    const selectedBg = e.target.value;
    await updateStickyOnServer(note.id, { color: selectedBg });
  });

  // Bind custom text color picker
  textPickerInput.addEventListener("input", (e) => {
    const selectedText = e.target.value;
    el.style.color = selectedText;
    textarea.style.color = selectedText;
    tagInput.style.color = selectedText;
  });

  textPickerInput.addEventListener("change", async (e) => {
    const selectedText = e.target.value;
    await updateStickyOnServer(note.id, { text_color: selectedText });
  });

  return el;
}

async function updateStickyOnServer(id, payload) {
  try {
    await fetchAPI(`/sticky-notes/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
  } catch (err) {
    console.warn(`Failed to update sticky note ${id} on server`, err);
  }
}

async function handleArchiveCompleted() {
  try {
    const res = await fetchAPI('/sticky-notes/archive-completed', { method: 'POST' });
    toast(res.message || "Completed stickies archived.");
    await renderBoard(currentSearchQuery);
  } catch (err) {
    toast("Failed to archive stickies", "error");
  }
}

async function handleDeleteCompleted() {
  if (confirm("Are you sure you want to permanently delete all completed sticky notes?")) {
    try {
      const res = await fetchAPI('/sticky-notes/delete-completed', { method: 'POST' });
      toast(res.message || "Completed stickies deleted.");
      await renderBoard(currentSearchQuery);
    } catch (err) {
      toast("Failed to delete stickies", "error");
    }
  }
}
