# AI Integration Tasks

- [x] Choose AI Provider
  - OpenAI
  - Gemini
- [x] Create API Key (from OpenAI Developer Platform or Google AI Studio)
- [x] Create local `.env` configuration file under `backend/.env`
- [x] Add the API Key to `backend/.env`
  - For OpenAI: `OPENAI_API_KEY=your_api_key_here`
  - For Gemini: `GEMINI_API_KEY=your_api_key_here`
- [x] Set `AI_PROVIDER` to `openai` or `gemini` in `backend/.env`
- [x] Verify first AI report generation triggers the active API integration successfully
- [x] Review generated reflection quality and adjust prompts in `backend/ai/prompt_builder.py` if needed
