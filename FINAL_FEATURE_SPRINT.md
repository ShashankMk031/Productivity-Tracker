# Final Feature Sprint: Flexible Reminders & Sticky Notes Board

Documentation of the implementation and architecture of the final planned sprint features: the Flexible Reminder System and the scrollable Sticky Notes Whiteboard Canvas.

---

## 1. Flexible Reminder System

### Overview
The reminder system has been updated to remove the strict restriction requiring a time for every reminder. The schema, service layer, and UI now support fully optional date and time inputs.

### Supported Combinations
- **Title only**: E.g., *"Complete DBMS Revision"*. Sits at the bottom of the list. No specific date or time alert trigger.
- **Title + Date**: E.g., *"Finish Resume" (Date: 2026-07-20)*. Overdue warning triggers on the day after the target date (logical IST day transition).
- **Title + Time**: E.g., *"Call Recruiter" (Time: 16:00)*. Triggers a push notification or toast alert at that exact time on today's logical date.
- **Title + Date + Time**: E.g., *"Submit Assignment" (Date: 2026-07-20, Time: 23:00)*. Triggers exactly at that datetime, and is marked overdue if missed.

### Backend Details
- **Schema**: Recreated `reminders` table with nullable `due_date`, `due_time`, and `datetime` columns (migration `0008`). Backward-compatibility migration automatically separates legacy ISO datetimes.
- **Sorting**: SQLite sorts NULL first. To keep undated reminders grouped at the bottom, sorting orders by `(CASE WHEN due_date IS NULL THEN 1 ELSE 0 END), due_date ASC, due_time ASC`.
- **Overdue Evaluation**: The backend service computes the timezone-aware (`Asia/Kolkata` IST) overdue status dynamically on all requests:
  - If date and time are provided: overdue if current IST datetime > target datetime.
  - If only date is provided: overdue if today's logical IST date > target date.
  - If only time is provided: overdue if today's logical IST date + target time is in the past.

### Frontend Integration
- Quick Reminder widget form expanded with an optional HTML5 date picker.
- Dynamic list formats output text according to active components:
  - Date & Time: `Jul 20 @ 4:00 PM`
  - Date only: `Due: Jul 20`
  - Time only: `At: 4:00 PM`
- Notification daemon checks `is_overdue` and fires system push notifications or warning indicators when appropriate.

---

## 2. Sticky Notes Board

### Overview
A freeform whiteboard canvas space that allows brain-dumping, sorting, and organizing ideas. Features drag-and-drop position persistence, layer ordering, and autosaving.

### Features & Implementation
- **Whiteboard Viewport**: A scrollable viewport containing a large canvas (3500x3500px) styled with a premium dot-grid matrix background.
- **Solid Pastel Color Themes**: Note containers feature opaque, solid pastel backgrounds with high-contrast, matching text colors (Yellow, Pink, Blue, Green, Purple) to maintain full readability.
- **Manual Sizing Power**: Cards support custom resize styling. Users can manually resize any sticky note using the browser's native drag handle on the bottom-right corner. The custom dimensions (`width` and `height`) save automatically to the database on pointer release.
- **Background & Text Color Pickers**: In addition to preset dots, each note footer includes a background color picker (🎨) and writing text color picker (✍️) letting users select any custom colors they prefer. Changes save to the server on color dialog completion.
- **Staggered Non-Overlapping Drafts**: Instead of spawning on top of each other, draft notes stagger horizontally (to the right of the latest pinned card, wrapping to a new line when canvas limits are reached) to ensure they do not overlay.
- **Auto-Save & Direct Editing**: Direct typing inside a card's textarea or tag input triggers a debounced autosave PUT API request (600ms content debounce, 800ms tag debounce). Shows a subtle `"Saving..."` / `"Saved"` feedback badge in the note footer.
- **Layer Ordering (z_index)**: Clicking anywhere on a note increments the global stack ordering (`maxZIndex + 1`) and persists the `z_index` in the database immediately, bringing it to the front of the viewport stack.
- **Position Persistence**: Smooth pointer event drag-and-drop listeners attached to note headers update local coordinates. The final coordinate values (`position_x`, `position_y`) save on pointer release.
- **Draft Note Constraints**: Enforces **exactly one active draft note** at all times.
  - Draft note has a default color, empty content, and displays a `"Draft"` badge.
  - Click the **📌 Pin** button to convert the draft into a persistent note (`is_draft = 0`), which immediately auto-spawns a new active draft note on the canvas.
  - Deleting the active draft note automatically auto-spawns a replacement empty draft note.
- **Search Filtering**: Live search input filters active notes dynamically by content substring or `#tag`.
- **Bulk Actions**:
  - **Archive Completed**: Sets `is_archived = 1` for all completed notes.
  - **Delete Completed**: Deletes all completed notes from the database.
