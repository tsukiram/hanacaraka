# routes/test_listening.py
from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import TestResult
import logging
import json
import random

logger = logging.getLogger(__name__)

test_listening = Blueprint('test_listening', __name__)

@test_listening.route('/')
@login_required
def listening():
    logger.debug(f"User {current_user.id} accessed listening route")
    try:
        with open('static/datasets/listening.json') as f:
            data = json.load(f)
        logger.debug(f"Loaded listening.json: {len(data['listening_comprehension'])} sets")
        set = random.choice(data['listening_comprehension'])
        logger.debug(f"Selected listening set: {set['set_name']}")
        return render_template('listening_test.html', set=set)
    except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
        logger.error(f"Error loading listening test: {str(e)}", exc_info=True)
        flash(f'Error loading listening test: {str(e)}', 'error')
        return redirect(url_for('home.home_page'))

@test_listening.route('/submit', methods=['POST'])
@login_required
def submit_listening():
    logger.debug(f"User {current_user.id} submitted listening test")
    try:
        answers = request.form.to_dict(flat=False)
        set_name = answers.pop('set_name', [None])[0]
        logger.debug(f"Listening submission: set_name={set_name}, answers={answers}")
        if not set_name:
            logger.error("Missing set_name")
            return jsonify({'error': 'Set name is missing from the form.'}), 400
        
        with open('static/datasets/listening.json') as f:
            data = json.load(f)
        set_data = next((s for s in data['listening_comprehension'] if s['set_name'] == set_name), None)
        if not set_data:
            logger.error(f"No test set found for set_name: {set_name}")
            return jsonify({'error': f'No test set found for set_name: {set_name}'}), 400
        
        score = calculate_listening_score(answers, set_data)
        logger.debug(f"Calculated listening score: {score}")
        
        result = TestResult(user_id=current_user.id, test_type='listening', set_name=set_name, score=score)
        db.session.add(result)
        try:
            db.session.commit()
            logger.debug(f"Listening result saved for user {current_user.id}, set_name: {set_name}")
        except Exception as db_error:
            db.session.rollback()
            logger.error(f"Database error: {str(db_error)}", exc_info=True)
            return jsonify({'error': f'Database error: {str(db_error)}'}), 500
        
        return jsonify({'score': score})
    except Exception as e:
        logger.error(f"Error in submit_listening: {str(e)}", exc_info=True)
        return jsonify({'error': f'Error processing listening test: {str(e)}'}), 500

def calculate_listening_score(answers, set_data):
    logger.debug("Calculating listening score")
    total_correct = 0
    total_questions = 0
    for recording in set_data['recordings']:
        for q in recording['questions']:
            total_questions += 1
            user_answer = answers.get(q['question_text'], [])
            if not isinstance(user_answer, list):
                user_answer = [user_answer]
            correct_answer = q['correct_answer']
            if not isinstance(correct_answer, list):
                correct_answer = [correct_answer]
            if q['question_type'] == 'single_choice' and len(user_answer) > 1:
                logger.debug(f"Skipping invalid single_choice answer for question: {q['question_text']}")
                continue
            if sorted(user_answer) == sorted(correct_answer):
                total_correct += 1
            logger.debug(f"Question: {q['question_text']}, User answer: {user_answer}, Correct: {correct_answer}, Match: {sorted(user_answer) == sorted(correct_answer)}")
    if total_questions == 0:
        logger.warning("No questions found in listening set")
        return {'percentage': 0, 'correct': 0, 'total': 0}
    score = {'percentage': (total_correct / total_questions) * 100, 'correct': total_correct, 'total': total_questions}
    logger.debug(f"Final listening score: {score}")
    return score