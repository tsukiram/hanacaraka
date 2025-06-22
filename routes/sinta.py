# C:\Users\rama\Desktop\hanacaraka\HANACARAKA\routes\sinta.py
from flask import Blueprint, render_template, jsonify, request, current_app
from flask_login import login_required, current_user
from models import ChatSession, ChatMessage
from extensions import db
from groq import Groq
import os
import logging
import json
from datetime import datetime
from io import BytesIO

logger = logging.getLogger(__name__)

sinta = Blueprint('sinta', __name__)

# Initialize Groq client
def get_groq_client():
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        logger.error("GROQ_API_KEY not found in environment variables")
        raise ValueError("GROQ_API_KEY is missing")
    return Groq(api_key=api_key)

# Load initial prompt
def load_initial_prompt():
    prompt_path = os.path.join(current_app.root_path, 'initial_prompt.txt')
    try:
        with open(prompt_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        logger.warning("initial_prompt.txt not found, using default prompt")
        return "You are Sinta, an AI English learning assistant. Help users practice English conversation, correct grammar, pronunciation, and structure, and suggest casual/formal variants."

@sinta.route('/')
@login_required
def sinta_page():
    try:
        sessions = ChatSession.query.filter_by(user_id=current_user.id).order_by(ChatSession.created_at.desc()).all()
        return render_template('sinta.html', sessions=sessions)
    except Exception as e:
        logger.error(f"Error loading Sinta page: {str(e)}", exc_info=True)
        return render_template('sinta.html', sessions=[], error=str(e))

@sinta.route('/new', methods=['POST'])
@login_required
def new_chat():
    try:
        data = request.get_json()
        topic = data.get('topic')
        if not topic or len(topic.strip()) < 3:
            return jsonify({'error': 'Topic must be at least 3 characters long'}), 400

        # Create new chat session
        title = f"Chat about {topic[:50]}"  # Auto-generate title
        session = ChatSession(
            user_id=current_user.id,
            title=title,
            topic=topic.strip()
        )
        db.session.add(session)
        db.session.commit()

        # Generate initial assistant message
        client = get_groq_client()
        initial_prompt = load_initial_prompt()
        system_prompt = f"""You are Sinta, an AI English learning assistant designed to help users practice English through engaging conversations.

USER PROFILE:
- User's name: {current_user.username}
- Conversation topic: {topic}

PERSONALIZED INTERACTION:
- Focus the conversation specifically on: {topic}
- Maintain enthusiasm and genuine interest in this topic
- For the first message, only provide the conversation starter without corrections or scores
- For subsequent messages, correct grammar, pronunciation, and structure errors in user input
- Provide scores for structure, diction, and context (1-5)
- Suggest casual and formal variants for user input
- Return responses in JSON format with fields: input_raw, error_tags, correction_tags, scores, variants, output

{initial_prompt}

CONVERSATION STARTER:
Begin by greeting the user appropriately and introducing the chosen topic of {topic}. Ask an engaging question to start the discussion while maintaining the JSON response format."""
        
        groq_messages = [{'role': 'system', 'content': system_prompt}]
        try:
            chat_completion = client.chat.completions.create(
                messages=groq_messages,
                model='llama3-70b-8192',
                response_format={"type": "json_object"}
            )
            response = json.loads(chat_completion.choices[0].message.content)
            
            # Save initial assistant message
            assistant_message = ChatMessage(
                chat_session_id=session.id,
                role='assistant',
                content=response['output']
            )
            db.session.add(assistant_message)
            db.session.commit()

            logger.debug(f"New chat session created: {session.id} for user {current_user.id} with initial message")
            return jsonify({
                'session_id': session.id,
                'title': session.title,
                'initial_message': {
                    'role': 'assistant',
                    'content': response['output'],
                    'timestamp': assistant_message.timestamp.isoformat()
                }
            })
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error generating initial message: {str(e)}", exc_info=True)
            return jsonify({'error': f'Failed to generate initial message: {str(e)}'}), 500

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating new chat: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@sinta.route('/chat/<int:session_id>', methods=['GET', 'POST'])
@login_required
def chat(session_id):
    try:
        session = ChatSession.query.get_or_404(session_id)
        if session.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized access'}), 403

        if request.method == 'GET':
            messages = ChatMessage.query.filter_by(chat_session_id=session_id).order_by(ChatMessage.timestamp.asc()).all()
            return jsonify({
                'session': {'id': session.id, 'title': session.title, 'topic': session.topic},
                'messages': [{
                    'id': m.id,
                    'role': m.role,
                    'content': m.content,
                    'input_raw': m.input_raw,
                    'error_tags': m.error_tags,
                    'correction_tags': m.correction_tags,
                    'scores': m.scores,
                    'variants': m.variants,
                    'timestamp': m.timestamp.isoformat()
                } for m in messages]
            })

        # POST: Handle new message
        client = get_groq_client()
        initial_prompt = load_initial_prompt()
        system_prompt = f"""You are Sinta, an AI English learning assistant designed to help users practice English through engaging conversations.

USER PROFILE:
- User's name: {current_user.username}
- Conversation topic: {session.topic}

PERSONALIZED INTERACTION:
- Focus the conversation specifically on: {session.topic}
- Maintain enthusiasm and genuine interest in this topic
- Correct grammar, pronunciation, and structure errors in user input
- Provide scores for structure, diction, and context (1-5)
- Suggest casual and formal variants for user input
- Return responses in JSON format with fields: input_raw, error_tags, correction_tags, scores, variants, output

{initial_prompt}"""

        data = request.form if request.form else request.get_json()
        user_input = data.get('message')
        audio = request.files.get('audio')

        if not user_input and not audio:
            return jsonify({'error': 'Message or audio required'}), 400

        input_raw = user_input
        if audio:
            try:
                # Process audio in memory
                audio_data = BytesIO(audio.read())
                audio_data.name = 'recording.wav'  # Required for Groq API
                transcription = client.audio.transcriptions.create(
                    file=audio_data,
                    model='whisper-large-v3-turbo',
                    response_format='verbose_json',
                    language='en',
                    temperature=0.0
                )
                input_raw = transcription.text
                logger.debug(f"Transcribed audio: {input_raw}")
            except Exception as e:
                logger.error(f"Error transcribing audio: {str(e)}", exc_info=True)
                return jsonify({'error': f'Failed to transcribe audio: {str(e)}'}), 500

        if not input_raw:
            return jsonify({'error': 'Empty input'}), 400

        # Save user message
        user_message = ChatMessage(
            chat_session_id=session_id,
            role='user',
            content=input_raw,
            input_raw=input_raw
        )
        db.session.add(user_message)

        # Get assistant response
        messages = ChatMessage.query.filter_by(chat_session_id=session_id).order_by(ChatMessage.timestamp.asc()).all()
        groq_messages = [
            {'role': 'system', 'content': system_prompt}
        ] + [
            {'role': m.role, 'content': m.content} for m in messages
        ]

        try:
            chat_completion = client.chat.completions.create(
                messages=groq_messages,
                model='llama3-70b-8192',
                response_format={"type": "json_object"}
            )
            response = json.loads(chat_completion.choices[0].message.content)

            # Save assistant message
            assistant_message = ChatMessage(
                chat_session_id=session_id,
                role='assistant',
                content=response['output'],
                input_raw=response.get('input_raw'),
                error_tags=response.get('error_tags'),
                correction_tags=response.get('correction_tags'),
                scores=response.get('scores'),
                variants=response.get('variants')
            )
            db.session.add(assistant_message)
            db.session.commit()

            logger.debug(f"Assistant response for session {session_id}: {response['output']}")
            return jsonify(response)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error getting assistant response: {str(e)}", exc_info=True)
            return jsonify({'error': f'Failed to get response: {str(e)}'}), 500

    except Exception as e:
        logger.error(f"Error in chat session {session_id}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500