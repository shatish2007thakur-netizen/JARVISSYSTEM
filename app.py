import streamlit as strl
from google import genai
import json
import os

# ================= STREAMLIT PAGE CONFIG =================
strl.set_page_config(page_title="JARVIS AI ONLINE SYSTEM", page_icon="🤖", layout="centered")

# Custom CSS for Jarvis Terminal View
strl.markdown("""
    <style>
    .stApp {
        background-color: #1a1a1a;
    }
    .terminal-title {
        font-family: 'Courier New', Courier, monospace;
        color: #4af626;
        font-weight: bold;
        text-align: center;
        font-size: 32px;
        margin-bottom: 5px;
    }
    .terminal-status {
        color: #ffffff;
        font-style: italic;
        text-align: center;
        font-size: 14px;
        margin-bottom: 20px;
    }
    .chat-box {
        background-color: #000000;
        border: 2px solid #2d2d2d;
        border-radius: 5px;
        padding: 15px;
        font-family: 'Courier New', Courier, monospace;
        color: #4af626;
        height: 300px;
        overflow-y: auto;
        margin-bottom: 20px;
        white-space: pre-wrap;
    }
    </style>
""", unsafe_allow_html=True)

# Title & Status Headers
strl.markdown('<div class="terminal-title">JARVIS AI ONLINE SYSTEM</div>', unsafe_allow_html=True)

# ================= GEMINI CONFIGURATION =================
# Try to get API key from Streamlit Secrets or Environment Variables
api_key = strl.secrets.get("GEMINI_API_KEY")

try:
    ai_client = genai.Client(api_key=api_key)
except Exception as e:
    ai_client = None

# Initialize Session States for Logs and Responses
if "chat_history" not in strl.session_state:
    strl.session_state.chat_history = "Jarvis: Systems online. Jarvis AI initialized.\nJarvis: Ready for your command, Sir."
if "tts_text" not in strl.session_state:
    strl.session_state.tts_text = "Systems initialized with Gemini AI. I am online, Sir."

# ================= JAVASCRIPT FOR SPEECH & TTS =================
# This handles Microphone Input and Voice Output directly in the browser!
js_code = f"""
<script>
    // --- TEXT TO SPEECH (Jarvis Voice) ---
    function speak(text) {{
        if ('speechSynthesis' in window && text !== "") {{
            window.speechSynthesis.cancel(); // Stop any ongoing speech
            var msg = new SpeechSynthesisUtterance(text);
            // Try to find a nice male or clean voice
            var voices = window.speechSynthesis.getVoices();
            if(voices.length > 0) {{
                msg.voice = voices[0]; 
            }}
            msg.rate = 1.0;
            window.speechSynthesis.speak(msg);
        }}
    }}

    // Trigger initial welcome speech if any
    var current_tts = `{strl.session_state.tts_text}`;
    if (current_tts !== "") {{
        speak(current_tts);
        // Clear it so it doesn't repeat on reload
        window.parent.postMessage({{type: 'streamlit:setComponentValue', value: 'clear_tts'}}, '*');
    }}

    // --- SPEECH RECOGNITION (Mic Input) ---
    function startListening() {{
        var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {{
            alert("Your browser does not support Speech Recognition. Please use Chrome.");
            return;
        }}
        
        var recognition = new SpeechRecognition();
        recognition.lang = 'en-IN';
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;

        window.parent.postMessage({{type: 'status_update', status: 'Listening... (Speak Now)'}}, '*');

        recognition.start();

        recognition.onresult = function(event) {{
            var speechToText = event.results[0][0].transcript;
            // Send the recognized query back to Streamlit
            const doc = window.parent.document;
            const textFields = doc.querySelectorAll('textarea[aria-label="voice_input_receiver"]');
            if(textFields.length > 0) {{
                textFields[0].value = speechToText;
                textFields[0].dispatchEvent(new Event('input', {{ bubbles: true }}));
                // Find and click submit if needed, or let Streamlit handle the rerun
            }}
            window.parent.postMessage({{type: 'speech_result', text: speechToText}}, '*');
        }};

        recognition.onspeechend = function() {{
            recognition.stop();
        }};

        recognition.onerror = function(event) {{
            window.parent.postMessage({{type: 'speech_error', error: event.error}}, '*');
        }};
    }}
</script>
"""

# Inject JavaScript helper hiddenly
strl.components.v1.html(js_code, height=0, width=0)

# JS Voice Handler trigger interface via safe HTML button hack for Mic trigger
st_status = strl.empty()
st_status.markdown('<div class="terminal-status">Status: Standby. Click "INITIALIZE MIC" to Speak</div>', unsafe_allow_html=True)

# Hidden Text Area to receive voice data from JS browser side
voice_query = strl.text_area("voice_input_receiver", label_visibility="collapsed", key="hidden_voice_input")

# Display Terminal logs
strl.markdown(f'<div class="chat-box">{strl.session_state.chat_history}</div>', unsafe_allow_html=True)

# ================= CORE PROCESSOR =================
def process_command(command):
    cmd = command.lower().strip()
    if not cmd:
        return
        
    strl.session_state.chat_history += f"\n\nYou: {command}"
    
    # 1. EXIT COMMANDS
    if "stop" in cmd or "exit" in cmd or "bye jarvis" in cmd:
        reply = "Going offline. Goodbye, Sir."
        strl.session_state.chat_history += f"\n\nJarvis: {reply}"
        strl.session_state.tts_text = reply
        
    # 2. OS/BROWSER CAPABILITIES
    elif "open google" in cmd or "open d google" in cmd:
        reply = "Opening Google, Sir."
        strl.session_state.chat_history += f"\n\nJarvis: {reply}"
        strl.session_state.tts_text = reply
        strl.markdown('<meta http-equiv="refresh" content="0;URL=\'https://www.google.com\'" />', unsafe_allow_html=True)
        
    elif "open youtube" in cmd:
        reply = "Opening YouTube, Sir."
        strl.session_state.chat_history += f"\n\nJarvis: {reply}"
        strl.session_state.tts_text = reply
        strl.markdown('<meta http-equiv="refresh" content="0;URL=\'https://www.youtube.com\'" />', unsafe_allow_html=True)

    # 3. GEMINI CORE RESPONSE
    else:
        if not ai_client:
            reply = "Sir, Gemini API Key core component missing configuration."
            strl.session_state.chat_history += f"\n\nJarvis: {reply}"
            strl.session_state.tts_text = reply
        else:
            try:
                response = ai_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=command,
                    config={
                        'system_instruction': "You are JARVIS, a helpful, ultra-smart AI assistant. Keep responses sweet, clean, smart, and under 2 sentences. Speak like a loyal assistant."
                    }
                )
                reply = response.text.strip()
                strl.session_state.chat_history += f"\n\nJarvis: {reply}"
                strl.session_state.tts_text = reply
            except Exception as e:
                reply = "Sir, I faced an error connecting to the AI core."
                strl.session_state.chat_history += f"\n\nJarvis: {reply}"
                strl.session_state.tts_text = "Apologies Sir, server error."

# Handle incoming Voice or Text Queries
if voice_query and voice_query != strl.session_state.get("last_processed_query", ""):
    st_status.markdown('<div class="terminal-status">Status: Processing Command...</div>', unsafe_allow_html=True)
    process_command(voice_query)
    strl.session_state.last_processed_query = voice_query
    strl.session_state.tts_text = strl.session_state.tts_text # force trigger voice update
    strl.rerun()

# --- Fallback Input Box & Control Action Buttons ---
col1, col2 = strl.columns([3, 1])
with col1:
    text_input = strl.text_input("Type command manually here:", key="manual_text_input", label_visibility="collapsed", placeholder="Type a command or use mic...")
with col2:
    if strl.button("SEND ↵", use_container_width=True) and text_input:
        process_command(text_input)
        strl.rerun()

# Main Interactive Custom Mic Activation Button 
strl.markdown("""
    <div style="text-align: center; margin-top: 10px;">
        <button onclick="startListening()" style="background-color: #2d2d2d; color: #4af626; border: 2px solid #4af626; font-weight: bold; padding: 12px 24px; font-size: 16px; border-radius: 5px; cursor: pointer; width: 100%;">
            🎙️ INITIALIZE MIC SYSTEMS
        </button>
    </div>
""", unsafe_allow_html=True)

