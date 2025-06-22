# C:\Users\rama\Desktop\hanacaraka\HANACARAKA\routes\test_speaking.py
from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db, csrf
from models import TestResult
from config import Config
import logging
import json
import random

logger = logging.getLogger(__name__)

test_speaking = Blueprint('test_speaking', __name__)

@test_speaking.route('/')
@login_required
def speaking():
    logger.debug(f"User {current_user.id} accessed speaking route")
    try:
        with open('static/datasets/speaking.json') as f:
            data = json.load(f)
        logger.debug(f"Loaded speaking.json: {len(data['speaking_comprehension'])} sets")
        set = random.choice(data['speaking_comprehension'])
        logger.debug(f"Selected speaking set: {set['set_name']}")
        return render_template('speaking_test.html', set=set)
    except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
        logger.error(f"Error loading speaking test: {str(e)}", exc_info=True)
        flash(f'Error loading speaking test: {str(e)}', 'error')
        return redirect(url_for('home.home_page'))

@test_speaking.route('/transcribe', methods=['POST'])
@login_required
@csrf.exempt
def transcribe():
    logger.debug(f"User {current_user.id} requested audio transcription")
    try:
        audio = request.files.get('audio')
        if not audio:
            logger.error("Missing audio file")
            return jsonify({'error': 'Missing audio file.'}), 400

        audio_data = audio.read()
        audio_filename = audio.filename or 'audio.webm'
        mime_type = audio.content_type or 'audio/webm'

        logger.debug(f"Transcribing audio: {audio_filename}, size: {len(audio_data)} bytes")
        transcription = Config.client.audio.transcriptions.create(
            file=(audio_filename, audio_data, mime_type),
            model='whisper-large-v3-turbo',
            response_format='text',
            language='en',
            temperature=0.0
        )
        logger.debug(f"Transcription: {transcription[:100]}...")
        return jsonify({'transcription': transcription})
    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}", exc_info=True)
        return jsonify({'error': f'Error transcribing audio: {str(e)}'}), 500

@test_speaking.route('/submit', methods=['POST'])
@login_required
@csrf.exempt
def submit():
    logger.debug(f"User {current_user.id} submitted speaking test")
    try:
        set_name = request.form.get('set_name')
        form_data = request.form.to_dict()
        logger.debug(f"Speaking submission: set_name={set_name}, form_data={form_data}")

        if not set_name:
            logger.error("Missing set_name")
            return jsonify({'error': 'Missing set name.'}), 400

        with open('static/datasets/speaking.json') as f:
            data = json.load(f)
        set_data = next((s for s in data['speaking_comprehension'] if s['set_name'] == set_name), None)
        if not set_data:
            logger.error(f"No test set found for set_name: {set_name}")
            return jsonify({'error': f'No test set found for set_name: {set_name}'}), 400

        tasks = set_data['tasks']
        transcriptions = {}
        for task in tasks:
            task_number = str(task['task_number'])
            transcription_key = f'transcription_{task_number}'
            task_number_key = f'task_number_{task_number}'
            if transcription_key not in form_data or task_number_key not in form_data:
                logger.error(f"Missing transcription or task number for task {task_number}")
                return jsonify({'error': f'Missing transcription or task number for task {task_number}'}), 400
            transcriptions[task_number] = form_data[transcription_key]

        scores = []
        for task in tasks:
            task_number = str(task['task_number'])
            transcription = transcriptions.get(task_number)
            task_type = task['task_type']
            difficulty = {
                'Personal Preference': 1,
                'Integrated Speaking': 1.5,
                'Agree/Disagree': 1
            }
            logger.debug(f"Evaluating task {task_number}, type: {task_type}, difficulty: {difficulty.get(task_type, 1)}")
            score = evaluate_speaking(transcription, set_name, task_number, difficulty.get(task_type, 1))
            score['overall'] = sum([score.get('fluency', 0), score.get('coherence', 0), score.get('vocabulary', 0), score.get('pronunciation', 0)]) / 4.0
            scores.append({'task_number': task_number, 'transcription': transcription, 'scores': score})

        overall_score = sum(score['scores']['overall'] for score in scores) / len(scores)
        logger.debug(f"Overall speaking score: {overall_score}")

        result = TestResult(
            user_id=current_user.id,
            test_type='speaking',
            set_name=set_name,
            score={
                'tasks': scores,
                'overall': overall_score
            }
        )
        db.session.add(result)
        try:
            db.session.commit()
            logger.debug(f"Speaking result saved for user {current_user.id}, set_name: {set_name}")
        except Exception as db_error:
            db.session.rollback()
            logger.error(f"Database error: {str(db_error)}", exc_info=True)
            return jsonify({'error': f'Database error: {str(db_error)}'}), 500

        return jsonify({'scores': [score['scores'] for score in scores], 'overall_score': overall_score})
    except Exception as e:
        logger.error(f"Error in submit_speaking: {str(e)}", exc_info=True)
        return jsonify({'error': f'Error processing speaking test: {str(e)}'}), 500

def evaluate_speaking(transcription, set_name, task_number, difficulty_factor):
    logger.debug(f"Evaluating speaking for set_name: {set_name}, task_number: {task_number}")
    try:
        with open('static/datasets/speaking.json') as f:
            data = json.load(f)
        set_data = next((s for s in data['speaking_comprehension'] if s['set_name'] == set_name), None)
        if not set_data:
            logger.error(f"No test set found for set_name: {set_name}")
            raise ValueError(f'No test set found for set_name: {set_name}')
        
        question = next((t for t in set_data['tasks'] if t['task_number'] == int(task_number)), None)
        if not question:
            logger.error(f"No task found for task_number: {task_number}")
            raise ValueError(f'No task found for task_number: {task_number}')
        
        with open('prompt/speaking.txt') as f:
            system_prompt = f.read()
        logger.debug(f"Loaded speaking system prompt: {system_prompt[:100]}...")
        
        prompt = f"""
        Task type: {question['task_type']}
        Question (Reading Passage): {question.get('audio_text', '')}
        Instructions: {question['prompt']}
        Answer to Evaluate: {transcription}
        """
        logger.debug(f"Speaking prompt: {prompt[:200]}...")
        
        logger.debug(f"Sending prompt to Groq API for speaking task {task_number}")
        completion = Config.client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            response_format={'type': 'json_object'},
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ],
            temperature=0.0,
            max_tokens=200
        )
        
        scores = json.loads(completion.choices[0].message.content)
        logger.debug(f"Raw speaking scores from API: {scores}")
        for key in scores:
            scores[key] = min(9, round(scores[key] * difficulty_factor))
        logger.debug(f"Adjusted speaking scores: {scores}")
        return scores
    except Exception as e:
        logger.error(f"Error evaluating speaking: {str(e)}", exc_info=True)
        raise ValueError(f'Error evaluating speaking response: {str(e)}')