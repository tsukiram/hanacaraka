# routes/profile.py
from flask import Blueprint, render_template, jsonify, request, send_file
from flask_login import login_required, current_user
from models import User, TestResult
from extensions import db
import logging
from PIL import Image
import io

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
        
        if reading_scores:
            stats['avg_reading'] = sum(reading_scores) / len(reading_scores)
        if listening_scores:
            stats['avg_listening'] = sum(listening_scores) / len(listening_scores)
        if writing_scores:
            stats['avg_writing'] = sum(writing_scores) / len(writing_scores)
        if speaking_scores:
            stats['avg_speaking'] = sum(speaking_scores) / len(speaking_scores)
        
        return render_template('profile.html', results=results, stats=stats, user=current_user)
    except Exception as e:
        logger.error(f"Error loading profile: {str(e)}", exc_info=True)
        return render_template('profile.html', results=[], stats={}, user=current_user)

@profile.route('/picture', methods=['GET', 'POST'])
@login_required
def upload_profile_picture():
    if request.method == 'POST':
        try:
            file = request.files.get('profile_image')
            if not file:
                logger.error("No file uploaded")
                return jsonify({'error': 'No file uploaded'}), 400
            
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
            db.session.commit()
            logger.debug(f"Profile picture uploaded for user {current_user.id}, size: {len(current_user.profile_image)} bytes")
            return jsonify({'message': 'Profile picture uploaded successfully'})
        except Exception as e:
            logger.error(f"Error uploading profile picture: {str(e)}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    return render_template('profile_picture.html')

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
        return jsonify({'error': 'No profile image found'}), 404
    except Exception as e:
        logger.error(f"Error serving profile image: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500