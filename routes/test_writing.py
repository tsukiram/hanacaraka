# C:\Users\rama\Desktop\hanacaraka\HANACARAKA\routes\test_writing.py
from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import TestResult, UserStatus
from utils import load_json_data
from config import Config
import logging
import json
import random
from datetime import datetime

logger = logging.getLogger(__name__)

test_writing = Blueprint('test_writing', __name__)

@test_writing.route('/')
@login_required
def writing():
    logger.debug(f"User {current_user.id} accessed writing route")
    try:
        data = load_json_data('static/datasets/writing.json')
        sets = data.get('writing_comprehension', [])
        if not sets:
            raise ValueError("No writing comprehension sets found")
        logger.debug(f"Loaded writing.json: {len(sets)} sets")
        selected_set = random.choice(sets)
        logger.debug(f"Selected writing set: {selected_set['set_name']}, tasks: {len(selected_set['tasks'])}")
        word_ranges = {str(task['task_number']): {'min': task['word_range']['min'], 'max': task['word_range']['max']} for task in selected_set['tasks']}
        logger.debug(f"Word ranges: {word_ranges}")
        
        # Set active test in UserStatus
        status = UserStatus.query.filter_by(user_id=current_user.id).first()
        if not status:
            status = UserStatus(user_id=current_user.id)
            db.session.add(status)
        status.active_test_id = None  # Temporary, will set after result creation
        status.updated_at = datetime.utcnow()
        db.session.commit()
        
        return render_template('writing_test.html', set=selected_set, word_ranges=word_ranges)
    except Exception as e:
        logger.error(f"Error loading writing test: {str(e)}", exc_info=True)
        flash(f'Error loading writing test: {str(e)}', 'error')
        return redirect(url_for('home.home_page'))

@test_writing.route('/submit', methods=['POST'])
@login_required
def submit_writing():
    logger.debug(f"User {current_user.id} submitted writing test")
    try:
        set_name = request.form.get('set_name')
        form_data = request.form.to_dict()
        logger.debug(f"Writing submission: set_name={set_name}, form_data={form_data}")
        if not set_name:
            logger.error("Missing set_name")
            return jsonify({'error': 'Missing set name.'}), 400

        data = load_json_data('static/datasets/writing.json')
        set_data = next((s for s in data['writing_comprehension'] if s['set_name'] == set_name), None)
        if not set_data:
            logger.error(f"No test set found for set_name: {set_name}")
            return jsonify({'error': f'No test set found for set_name: {set_name}'}), 400
        logger.debug(f"Found set: {set_data['set_name']}, tasks: {len(set_data['tasks'])}")

        scores = []
        for task in set_data['tasks']:
            task_number = str(task['task_number'])
            answer = request.form.get(f'answer_{task_number}')
            logger.debug(f"Processing task {task_number}, answer length: {len(answer) if answer else 0}")
            if not answer:
                logger.error(f"Missing answer for task_number: {task_number}")
                return jsonify({'error': f'Missing answer for task {task_number}.'}), 400

            logger.debug(f"Received answer for task {task_number}: {answer[:100]}...")

            with open('prompt/writing.txt', 'r') as f:
                system_prompt = f.read()
            logger.debug(f"System prompt: {system_prompt[:100]}...")

            prompt = f"""
            Task type: {task['task_type']}
            Question (Reading Passage): {task.get('reading_passage', '')}
            Instructions: {task['prompt']}
            Answer to Evaluate: {answer}
            """
            logger.debug(f"Prompt for task {task_number}: {prompt[:200]}...")

            logger.debug(f"Sending prompt to Groq API for task {task_number}")
            try:
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
                score = json.loads(completion.choices[0].message.content)
                logger.debug(f"Raw score from API for task {task_number}: {score}")
                if not all(key in score for key in ['task_achievement', 'coherence', 'vocabulary', 'grammar']):
                    logger.error(f"Invalid score format for task {task_number}: {score}")
                    return jsonify({'error': f'Invalid score format for task {task_number}'}), 500
                score['overall'] = sum([score['task_achievement'], score['coherence'], score['vocabulary'], score['grammar']]) / 4.0
                scores.append(score)
                logger.debug(f"Processed score for task {task_number}: {score}")
            except Exception as api_error:
                logger.error(f"Groq API error for task {task_number}: {str(api_error)}", exc_info=True)
                return jsonify({'error': f'Failed to evaluate task {task_number}: {str(api_error)}'}), 500

        overall_score = sum(score['overall'] for score in scores) / len(scores)
        logger.debug(f"Overall test score: {overall_score}")

        result = TestResult(
            user_id=current_user.id,
            test_type='writing',
            set_name=set_name,
            score={
                'tasks': scores,
                'overall': overall_score
            },
            is_public=False  # Default to private
        )
        db.session.add(result)
        
        # Update UserStatus with active test
        status = UserStatus.query.filter_by(user_id=current_user.id).first()
        if not status:
            status = UserStatus(user_id=current_user.id)
            db.session.add(status)
        status.active_test_id = result.id
        status.updated_at = datetime.utcnow()
        
        try:
            db.session.commit()
            logger.debug(f"Writing result saved for user {current_user.id}, set_name: {set_name}")
            
            # Reset active test after submission
            status.active_test_id = None
            status.updated_at = datetime.utcnow()
            db.session.commit()
        except Exception as db_error:
            db.session.rollback()
            logger.error(f"Database error: {str(db_error)}", exc_info=True)
            return jsonify({'error': 'Failed to save result due to database error.'}), 500

        return jsonify({
            'scores': scores,
            'overall_score': overall_score,
            'message': 'Writing test submitted successfully'
        })
    except Exception as e:
        logger.error(f"Error in submit_writing: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to process writing test: {str(e)}'}), 500