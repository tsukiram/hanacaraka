# C:\Users\rama\Desktop\hanacaraka\HANACARAKA\routes\profile.py
from flask import Blueprint, render_template, jsonify, request, send_file
from flask_login import login_required, current_user
from models import User, TestResult
from extensions import db, csrf
import logging
from PIL import Image
import io
import re

logger = logging.getLogger(__name__)

profile = Blueprint('profile', __name__)

@profile.route('/')
@login_required
def profile_page():
    try:
        results = TestResult.query.filter_by(user_id=current_user.id).order_by(TestResult.timestamp.desc()).all()
        
        stats = {
            'total_tests': len(results),
            'reading_tests': len([r for r in results if r.test_type == 'reading']),
            'listening_tests': len([r for r in results if r.test_type == 'listening']),
            'writing_tests': len([r for r in results if r.test_type == 'writing']),
            'speaking_tests': len([r for r in results if r.test_type == 'speaking']),
        }
        
        reading_scores = [r.score.get('percentage', 0) for r in results if r.test_type == 'reading' and 'percentage' in r.score]
        listening_scores = [r.score.get('percentage', 0) for r in results if r.test_type == 'listening' and 'percentage' in r.score]
        writing_scores = [r.score.get('overall', 0) for r in results if r.test_type == 'writing' and 'overall' in r.score]
        speaking_scores = [r.score.get('overall', 0) for r in results if r.test_type == 'speaking' and 'overall' in r.score]
        
        stats['avg_reading'] = sum(reading_scores) / len(reading_scores) if reading_scores else 0
        stats['avg_listening'] = sum(listening_scores) / len(listening_scores) if listening_scores else 0
        stats['avg_writing'] = sum(writing_scores) / len(writing_scores) if writing_scores else 0
        stats['avg_speaking'] = sum(speaking_scores) / len(speaking_scores) if speaking_scores else 0
        
        return render_template('profile.html', results=results, stats=stats, user=current_user)
    except Exception as e:
        logger.error(f"Error loading profile: {str(e)}", exc_info=True)
        return render_template('profile.html', results=[], stats={}, user=current_user)

@profile.route('/update', methods=['GET', 'POST'])
@login_required
@csrf.exempt
def update_profile():
    if request.method == 'POST':
        try:
            # Validasi username (jika ada)
            new_username = request.form.get('username')
            if new_username:
                if not re.match(r'^[a-zA-Z0-9_]{3,80}$', new_username):
                    logger.error(f"Invalid username format: {new_username}")
                    return jsonify({'error': 'Username must be 3-80 characters long and contain only letters, numbers, or underscores'}), 400
                if new_username != current_user.username and User.query.filter(User.username == new_username).first():
                    logger.error(f"Username already taken: {new_username}")
                    return jsonify({'error': 'Username is already taken'}), 400
                current_user.username = new_username

            # Validasi gambar profil (jika ada)
            file = request.files.get('profile_image')
            if file and file.filename:
                allowed_extensions = {'jpg', 'jpeg', 'png'}
                if not '.' in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
                    logger.error(f"Invalid file extension: {file.filename}")
                    return jsonify({'error': 'Only JPG and PNG files are allowed'}), 400
                
                img = Image.open(file)
                img.thumbnail((500, 500))
                output = io.BytesIO()
                img_format = 'JPEG' if file.filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg'} else 'PNG'
                img.save(output, format=img_format, quality=85, optimize=True)
                
                quality = 85
                while output.getvalue().__len__() > 500 * 1024 and quality > 10:
                    output.seek(0)
                    output.truncate(0)
                    quality -= 5
                    img.save(output, format=img_format, quality=quality, optimize=True)
                
                if output.getvalue().__len__() > 500 * 1024:
                    logger.error("Image size still exceeds 500KB after compression")
                    return jsonify({'error': 'Image could not be compressed below 500KB'}), 400
                
                current_user.profile_image = output.getvalue()
                logger.debug(f"Profile picture updated for user {current_user.id}, size: {len(current_user.profile_image)} bytes")

            # Jika tidak ada perubahan
            if not new_username and not file:
                return jsonify({'error': 'No changes provided'}), 400

            db.session.commit()
            logger.debug(f"Profile updated for user {current_user.id}, username: {current_user.username}")
            return jsonify({'message': 'Profile updated successfully'})
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating profile: {str(e)}", exc_info=True)
            return jsonify({'error': f'Failed to update profile: {str(e)}'}), 500
    
    return render_template('update_profile.html')

@profile.route('/image')
@login_required
def get_profile_image():
    try:
        if current_user.profile_image:
            img_format = 'JPEG' if current_user.profile_image.startswith(b'\xff\xd8') else 'PNG'
            return send_file(
                io.BytesIO(current_user.profile_image),
                mimetype=f'image/{img_format.lower()}',
                as_attachment=False,
                download_name=f'profile_{current_user.id}.{img_format.lower()}'
            )
        logger.warning(f"No profile image found for user {current_user.id}")
        return jsonify({'error': 'No profile image found'}), 404
    except Exception as e:
        logger.error(f"Error serving profile image: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to retrieve image: {str(e)}'}), 500

@profile.route('/delete_result/<int:result_id>', methods=['POST'])
@login_required
@csrf.exempt
def delete_result(result_id):
    try:
        result = TestResult.query.get_or_404(result_id)
        if result.user_id != current_user.id:
            logger.error(f"User {current_user.id} attempted to delete result {result_id} not owned")
            return jsonify({'error': 'Unauthorized action'}), 403
        db.session.delete(result)
        db.session.commit()
        logger.debug(f"Result {result_id} deleted by user {current_user.id}")
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting result {result_id}: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to delete result: {str(e)}'}), 500