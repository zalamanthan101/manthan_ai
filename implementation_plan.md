# 7-Feature Upgrade for Manthan AI

This plan outlines the addition of the 6 requested frontend/UX features plus the PPT Maker backend feature.

## User Review Required

> [!IMPORTANT]
> - Adding the PPT Maker requires installing a new python dependency: `python-pptx`.
> - Exporting Chat to PDF requires adding client-side libraries (e.g. `jspdf` and `html2canvas`) via CDN.
> - Voice Input will use the native Web Speech API which is supported in most modern browsers (Chrome/Edge).

## Open Questions

> [!WARNING]
> For the **PPT Maker**, what should the user flow be? Should the AI automatically detect a request for a PPT, generate the content, and return a downloadable `.pptx` file link? Or should we add a specific "Generate PPT" button/task pill? (I propose adding a specific task pill for "PPT Maker").

## Proposed Changes

---

### Backend Updates

#### [MODIFY] [requirements.txt](file:///c:/Users/VAIBHAVI/ai/requirements.txt)
- Add `python-pptx` to support PowerPoint generation.

#### [MODIFY] [main.py](file:///c:/Users/VAIBHAVI/ai/main.py)
- Create a new endpoint (or modify the existing `chat` endpoint) to handle file downloads for the generated PPTs. Serve static files from a new `temp` directory.

#### [MODIFY] [core/router.py](file:///c:/Users/VAIBHAVI/ai/core/router.py)
- Update `ask_ai` to detect if the task is `ppt`.
- If `ppt`, instruct the AI model to output slide titles and content in a structured format (like JSON).
- Parse the AI response, use `python-pptx` to create a presentation, save it, and return a download link in the chat response.

---

### Frontend Updates (index.html)

#### [MODIFY] [index.html](file:///c:/Users/VAIBHAVI/ai/index.html)
- **Voice Input**: Add a microphone button 🎤 next to the input area and integrate `webkitSpeechRecognition`.
- **Copy Code & Syntax Highlighting**: Add `marked.js` and `highlight.js` via CDN to parse markdown responses and highlight code blocks. Add a "Copy" button to each code block.
- **Export Chat (PDF/MD)**: Add an "Export" icon to the topbar. Use `html2canvas` and `jspdf` to capture the chat history and save it.
- **Quick AI Prompt Buttons**: Add a row of quick prompt buttons above the input area (e.g., "Find Bug", "Explain").
- **Drag and Drop**: Add event listeners to the body/chat area for `dragover` and `drop` to handle file uploads without opening the file picker.
- **PPT Maker Task Pill**: Add a new pill `📊 Make PPT` in the task row to trigger the PPT generation flow.

---

### PWA Updates

#### [NEW] [manifest.json](file:///c:/Users/VAIBHAVI/ai/manifest.json)
- Create a Web App Manifest to define the app icon, name, and display mode (standalone).

#### [NEW] [sw.js](file:///c:/Users/VAIBHAVI/ai/sw.js)
- Create a basic Service Worker to cache assets and allow the app to be installable.

#### [MODIFY] [index.html](file:///c:/Users/VAIBHAVI/ai/index.html)
- Link the `manifest.json` and register the Service Worker in the `<head>` and `<script>` sections.

## Verification Plan

### Automated Tests
- N/A (Project does not currently have a test suite).

### Manual Verification
1. Run `pip install -r requirements.txt`.
2. Start the server.
3. Open `index.html`. Verify PWA installation prompt appears.
4. Drag and drop an image or file into the chat.
5. Click Voice Input to dictate a message.
6. Check if code blocks have Syntax Highlighting and a working Copy button.
7. Click Quick Prompts to ensure they populate the chat box.
8. Click "Make PPT" and ask "Make a PPT on AI". Verify a `.pptx` file is generated and downloadable.
9. Click "Export" to verify the chat exports to PDF/MD.
