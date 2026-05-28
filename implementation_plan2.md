# Sidebar Chat History Implementation Plan 📝

This plan outlines adding a ChatGPT/Gemini-style sidebar to store past chats and a "New Chat" option.

## User Review Required

> [!IMPORTANT]
> **Storage Decision:** I am proposing to use **Local Storage (Browser Memory)** to save the chat history. Iska fayda ye hai ki backend me koi database setup nahi karna padega aur turant fast chalega. Jab tak tum browser data clear nahi karoge, chats yahan save rahengi. 
> 
> Is this okay? Or do you want me to build a permanent backend SQLite database for it? (Local Storage is recommended for now).

## Open Questions

> [!WARNING]
> Side bar hamesha open rakhna hai ya mobile screen jaisa "Hamburger (☰)" menu banana hai jo click karne par slide ho kar aaye? (I propose keeping it always visible on desktop, and collapsible on mobile).

## Proposed Changes

---

### Frontend Updates (index.html)

#### [MODIFY] [index.html](file:///c:/Users/VAIBHAVI/ai/index.html)
- **UI Structure**: Restructure the `#chat` div to use a flex layout with two columns: a left sidebar (`#sidebar`) and the main chat area (`#main-chat`).
- **Sidebar CSS**: Add premium dark styling for the sidebar to match the overall Manthan AI aesthetic.
- **New Chat Button**: Add a prominent `➕ New Chat` button at the top of the sidebar.
- **Chat History List**: Add a scrollable list inside the sidebar showing titles of past chats.
- **JavaScript Logic**:
  - Generate a unique `chatId` when starting a new chat.
  - Save messages to `localStorage` under an array `manthan_chats`.
  - When a user types the first message of a "New Chat", automatically generate a short title for it (e.g., taking the first 20 characters of the prompt) and save it.
  - Clicking a chat from the sidebar will clear the current screen and load the history of that specific `chatId` from `localStorage`.

## Verification Plan

### Manual Verification
1. Start the app. 
2. Enter the chat area. Note the new Sidebar on the left.
3. Click "New Chat". 
4. Type a message. Check if a new chat entry appears in the sidebar.
5. Refresh the page, log back in, and verify the chat history is still present in the sidebar.
6. Click an old chat to see if the messages load correctly.
