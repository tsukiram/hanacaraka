# routes/results.py
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from models import TestResult
from sqlalchemy import desc
from extensions import db
import logging

logger = logging.getLogger(__name__)

results = Blueprint('results', __name__)

@results.route('/')
@login_required
def view_results():
    try:
        results = TestResult.query.filter_by(user_id=current_user.id).order_by(desc(TestResult.timestamp)).all()
        logger.debug(f"Found {len(results)} results for user {current_user.id}")
        
        for result in results:
            if result.test_type in ['writing', 'speaking']:
                logger.debug(f"{result.test_type.capitalize()} result structure: {result.score}")
        
        return render_template('results.html', results=results)
    except Exception as e:
        logger.error(f"Error loading results: {str(e)}", exc_info=True)
        return render_template('results.html', results=[])

@results.route('/api/results')
@login_required
def api_results():
    try:
        results = TestResult.query.filter_by(user_id=current_user.id).order_by(desc(TestResult.timestamp)).all()
        
        results_data = []
        for result in results:
            results_data.append({
                'id': result.id,
                'test_type': result.test_type,
                'set_name': result.set_name,
                'score': result.score,
                'timestamp': result.timestamp.isoformat()
            })
        
        return jsonify({'results': results_data})
    except Exception as e:
        logger.error(f"Error getting API results: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@results.route('/delete/<int:result_id>', methods=['POST'])
@login_required
def delete_result(result_id):
    try:
        result = TestResult.query.filter_by(id=result_id, user_id=current_user.id).first()
        if not result:
            return jsonify({'error': 'Result not found'}), 404
        
        db.session.delete(result)
        db.session.commit()
        
        logger.debug(f"Deleted result {result_id} for user {current_user.id}")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error deleting result: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500