import sys
from pathlib import Path
import sqlite3

# Ensure backend directory is in python path
sys.path.append(str(Path(__file__).parent / "backend"))

from backend.database.db import DB_PATH, init_db
from backend.ai.context_builder import build_ai_context
from backend.ai.prompt_builder import build_ai_prompt
from backend.ai.ai_service import AIService

def test_pipeline():
    print("=== Starting AI Infrastructure Layer Dry-Run Verification ===")
    
    # 1. Ensure database is initialized
    print(f"Connecting to database at: {DB_PATH}")
    if not DB_PATH.exists():
        print("Database not found. Initializing empty database with schema...")
        init_db()
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # 2. Run Context Builder
    print("\n[Step 1] Executing Context Builder...")
    try:
        context = build_ai_context(conn, period_type="weekly")
        print("✓ Context Package successfully created!")
        print(f"  - Generated Timestamp: {context.generated_at}")
        print(f"  - Active Tasks Evaluated: {context.behavioral_patterns.active_tasks_count}")
        print(f"  - Notes Evaluated: {context.notes.total_notes_analyzed}")
        print(f"  - Goals Loaded: {len(context.goals)}")
        print(f"  - Projects Loaded: {len(context.projects)}")
    except Exception as e:
        print(f"❌ Context Builder failed: {e}")
        conn.close()
        return
        
    # 3. Run Prompt Builder
    print("\n[Step 2] Executing Prompt Builder...")
    try:
        prompt = build_ai_prompt(context)
        print("✓ Prompt successfully rendered!")
        print(f"  - Prompt length: {len(prompt)} characters")
        print("--- PROMPT PREVIEW (First 300 characters) ---")
        print(prompt[:300] + "\n...")
        print("---------------------------------------------")
    except Exception as e:
        print(f"❌ Prompt Builder failed: {e}")
        conn.close()
        return
        
    # 4. Run AI Service Mock Reflection
    print("\n[Step 3] Executing AIService Reflection...")
    try:
        ai_service = AIService()
        reflection, provider, model = ai_service.generate_reflection(prompt)
        print("✓ Mock AI Reflection successfully rendered!")
        print(f"  - Active Provider: {provider} ({model})")
        print("--- REFLECTION PREVIEW (First 300 characters) ---")
        print(reflection[:300] + "\n...")
        print("---------------------------------------------")
    except Exception as e:
        print(f"❌ AI Service failed: {e}")
        conn.close()
        return
        
    conn.close()
    print("\n🎉 PHASE 4A AI INFRASTRUCTURE LAYER SUCCESSFULLY VERIFIED! 🎉")

if __name__ == "__main__":
    test_pipeline()
