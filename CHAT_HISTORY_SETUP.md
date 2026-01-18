# Chat History Setup Guide

## Backend Setup

### 1. Configure Environment Variables

Copy the `.env.example` file to `.env`:
```bash
cd backend
cp .env.example .env
```

Edit `.env` and add your Supabase credentials:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key_here
```

### 2. Set Up Supabase Database

1. Go to your Supabase project dashboard
2. Navigate to the SQL Editor
3. Run the schema from `backend/supabase_schema.sql`

This will create:
- `conversation_turns` table - stores chat messages
- `agent_logs` table - stores AI agent activity
- `sessions` table - stores session metadata

### 3. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Start the Backend Server

```bash
python main.py
```

The server will run on `http://127.0.0.1:8000`

## Frontend Setup

The frontend is already configured! Just make sure:

1. Backend server is running
2. Navigate to the chat interface
3. Click the menu button (☰) on the left to see chat history

## Features

### Chat History Panel
- **View all sessions**: Click the menu button to see your chat history
- **Load previous chats**: Click any session to load its full conversation
- **Start new chat**: Click "Start New Chat" to begin a fresh conversation
- **Auto-save**: All conversations are automatically saved to Supabase

### How It Works

1. **Saving**: Every message you send is stored in Supabase with:
   - Session ID (unique per chat)
   - User message and AI response
   - Timestamp
   - Agent metadata

2. **Loading**: When you click a session:
   - Frontend fetches the full conversation history
   - All messages are restored in order
   - You can continue the conversation

3. **Sessions List**: Shows:
   - Preview of the first message
   - Relative time (Today, Yesterday, dates)
   - Active session highlighting

## API Endpoints

- `GET /api/sessions` - Get all chat sessions
- `GET /api/history/{session_id}` - Get full conversation history
- `POST /api/chat` - Send a message (auto-saves to Supabase)

## Troubleshooting

### "No chat history yet"
- Start a conversation first
- Make sure Supabase credentials are correct in `.env`
- Check backend logs for Supabase connection errors

### Sessions not loading
- Verify Supabase URL and key in `.env`
- Check that the database schema was created correctly
- Look for errors in browser console and backend logs

### Backend connection failed
- Ensure backend is running on port 8000
- Check CORS settings if accessing from different domain
