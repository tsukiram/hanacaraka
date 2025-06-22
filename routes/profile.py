# C:\Users\rama\Desktop\hanacaraka\HANACARAKA\routes\profile.py
from flask import Blueprint, render_template, jsonify, request, send_file
from flask_login import login_required, current_user
from models import User, TestResult, Friendship, FriendRequest, UserStatus
from extensions import db, csrf
import logging
from PIL import Image
import io
import re
from datetime import datetime

logger = logging.getLogger(__name__)

profile = Blueprint('profile', __name__)

@profile.route('/')
@login_required
def profile_page():
    try:
        results = TestResult.query.filter_by(user_id=current_user.id).order_by(TestResult.timestamp.desc()).all()
        friends = Friendship.query.filter_by(user_id=current_user.id).all()
        friend_requests = FriendRequest.query.filter_by(receiver_id=current_user.id, status='pending').all()
        
        stats = {
            'total_tests': len(results),
            'reading_tests': sum(1 for r in results if r.test_type == 'reading'),
            'listening_tests': sum(1 for r in results if r.test_type == 'listening'),
            'writing_tests': sum(1 for r in results if r.test_type == 'writing'),
            'speaking_tests': sum(1 for r in results if r.test_type == 'speaking'),
            'avg_reading': 0,
            'avg_listening': 0,
            'avg_writing': 0,
            'avg_speaking': 0
        }
        
        reading_scores = [r.score.get('percentage', 0) for r in results if r.test_type == 'reading' and 'percentage' in r.score]
        listening_scores = [r.score.get('percentage', 0) for r in results if r.test_type == 'listening' and 'percentage' in r.score]
        writing_scores = [r.score.get('overall', 0) for r in results if r.test_type == 'writing' and 'overall' in r.score]
        speaking_scores = [r.score.get('overall', 0) for r in results if r.test_type == 'speaking' and 'overall' in r.score]
        
        stats['avg_reading'] = sum(reading_scores) / len(reading_scores) if reading_scores else 0
        stats['avg_listening'] = sum(listening_scores) / len(listening_scores) if listening_scores else 0
        stats['avg_writing'] = sum(writing_scores) / len(writing_scores) if writing_scores else 0
        stats['avg_speaking'] = sum(speaking_scores) / len(speaking_scores) if speaking_scores else 0
        
        return render_template('profile.html', results=results, stats=stats, user=current_user, friends=friends, friend_requests=friend_requests)
    except Exception as e:
        logger.error(f"Error loading profile for user {current_user.id}: {str(e)}", exc_info=True)
        return render_template('profile.html', results=[], stats={}, user=current_user, friends=[], friend_requests=[], error=str(e))
    
@profile.route('/update', methods=['GET', 'POST'])
@login_required
def update_profile():
    if request.method == 'POST':
        try:
            # Validate username
            new_username = request.form.get('username')
            if new_username:
                if not re.match(r'^[a-zA-Z0-9_]{3,80}$', new_username):
                    logger.error(f"Invalid username format: {new_username}")
                    return jsonify({'error': 'Username must be 3-80 characters long and contain only letters, numbers, or underscores'}), 400
                if new_username != current_user.username and User.query.filter_by(username=new_username).first():
                    logger.error(f"Username already taken: {new_username}")
                    return jsonify({'error': 'Username is already taken'}), 400
                current_user.username = new_username

            # Validate status
            status_text = request.form.get('status')
            if status_text:
                if len(status_text) > 200:
                    logger.error(f"Status too long: {len(status_text)} characters")
                    return jsonify({'error': 'Status must be 200 characters or less'}), 400
                status = UserStatus.query.filter_by(user_id=current_user.id).first()
                if not status:
                    status = UserStatus(user_id=current_user.id)
                    db.session.add(status)
                status.status = status_text
                status.updated_at = datetime.utcnow()

            # Validate profile image
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

            # Check for changes
            if not any([new_username, status_text, file]):
                return jsonify({'error': 'No changes provided'}), 400

            db.session.commit()
            logger.debug(f"Profile updated for user {current_user.id}, username: {current_user.username}")
            return jsonify({'message': 'Profile updated successfully'})
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating profile for user {current_user.id}: {str(e)}", exc_info=True)
            return jsonify({'error': f'Failed to update profile: {str(e)}'}), 500
    
    # For GET requests, pass user and status to the template
    status = UserStatus.query.filter_by(user_id=current_user.id).first()
    return render_template('update_profile.html', user=current_user, status=status)
    

@profile.route('/image')
@login_required
def get_profile_image():
    try:
        if current_user.profile_image:
            img_format = 'JPEG' if current_user.profile_image.startswith(b'\xff\d8') else 'PNG'
            return send_file(
                io.BytesIO(current_user.profile_image),
                mimetype=f'image/{img_format.lower()}',
                as_attachment=False,
                download_name=f'profile_{current_user.id}.{img_format.lower()}'
            )
        logger.warning(f"No profile image found for user {current_user.id}")
        return jsonify({'error': 'No profile image found'}), 404
    except Exception as e:
        logger.error(f"Error serving profile image for user {current_user.id}: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to retrieve image: {str(e)}'}), 500

@profile.route('/delete_result/<int:result_id>', methods=['POST'])
@login_required
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
        logger.error(f"Error deleting result {result_id} for user {current_user.id}: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to delete result: {str(e)}'}), 500

@profile.route('/toggle_public/<int:result_id>', methods=['POST'])
@login_required
def toggle_public(result_id):
    try:
        result = TestResult.query.get_or_404(result_id)
        if result.user_id != current_user.id:
            logger.error(f"User {current_user.id} attempted to toggle public status for result {result_id} not owned")
            return jsonify({'error': 'Unauthorized action'}), 403
        result.is_public = not result.is_public
        db.session.commit()
        logger.debug(f"Result {result_id} toggled to {'public' if result.is_public else 'private'} by user {current_user.id}")
        return jsonify({'is_public': result.is_public})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling public status for result {result_id}: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to toggle public status: {str(e)}'}), 500

@profile.route('/friends', methods=['GET'])
@login_required
def get_friends():
    try:
        friends = Friendship.query.filter_by(user_id=current_user.id).all()
        friend_ids = [f.friend_id for f in friends]
        friends_data = User.query.filter(User.id.in_(friend_ids)).all()
        return jsonify([{'id': f.id, 'username': f.username} for f in friends_data])
    except Exception as e:
        logger.error(f"Error fetching friends for user {current_user.id}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@profile.route('/friend_request', methods=['POST'])
@login_required
def send_friend_request():
    try:
        data = request.get_json()
        receiver_id = data.get('receiver_id')
        if not receiver_id or receiver_id == current_user.id:
            return jsonify({'error': 'Invalid or self request'}), 400
        if Friendship.query.filter_by(user_id=current_user.id, friend_id=receiver_id).first():
            return jsonify({'error': 'Already friends'}), 400
        if FriendRequest.query.filter_by(sender_id=current_user.id, receiver_id=receiver_id, status='pending').first():
            return jsonify({'error': 'Request already sent'}), 400
        friend_request = FriendRequest(sender_id=current_user.id, receiver_id=receiver_id)
        db.session.add(friend_request)
        db.session.commit()
        logger.debug(f"Friend request sent from user {current_user.id} to {receiver_id}")
        return jsonify({'message': 'Friend request sent'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error sending friend request from user {current_user.id}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@profile.route('/friend_request/<int:request_id>/<action>', methods=['POST'])
@login_required
def handle_friend_request(request_id, action):
    try:
        friend_request = FriendRequest.query.get_or_404(request_id)
        if friend_request.receiver_id != current_user.id:
            logger.error(f"User {current_user.id} attempted to handle request {request_id} not addressed to them")
            return jsonify({'error': 'Unauthorized access'}), 403
        if action not in ['accept', 'reject']:
            return jsonify({'error': 'Invalid action'}), 400
        if action == 'accept':
            friendship1 = Friendship(user_id=friend_request.sender_id, friend_id=friend_request.receiver_id)
            friendship2 = Friendship(user_id=friend_request.receiver_id, friend_id=friend_request.sender_id)
            db.session.add(friendship1)
            db.session.add(friendship2)
            friend_request.status = 'accepted'
        else:
            friend_request.status = 'rejected'
        db.session.commit()
        logger.debug(f"Friend request {request_id} {action}ed by user {current_user.id}")
        return jsonify({'message': f'Friend request {action}ed'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error handling friend request {request_id} for user {current_user.id}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@profile.route('/search_users', methods=['GET'])
@login_required
def search_users():
    try:
        query = request.args.get('q', '')
        users = User.query.filter(User.username.ilike(f'%{query}%'), User.id != current_user.id).limit(10).all()
        return jsonify([{'id': u.id, 'username': u.username} for u in users])
    except Exception as e:
        logger.error(f"Error searching users for user {current_user.id}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@profile.route('/status', methods=['GET', 'POST'])
@login_required
def user_status():
    try:
        if request.method == 'POST':
            data = request.get_json()
            status_text = data.get('status')
            if len(status_text) > 200:
                logger.error(f"Status too long: {len(status_text)} characters for user {current_user.id}")
                return jsonify({'error': 'Status must be 200 characters or less'}), 400
            status = UserStatus.query.filter_by(user_id=current_user.id).first()
            if not status:
                status = UserStatus(user_id=current_user.id)
                db.session.add(status)
            status.status = status_text
            status.updated_at = datetime.utcnow()
            db.session.commit()
            logger.debug(f"Status updated for user {current_user.id}")
            return jsonify({'message': 'Status updated'})
        else:
            status = UserStatus.query.filter_by(user_id=current_user.id).first()
            return jsonify({'status': status.status if status else ''})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating status for user {current_user.id}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@profile.route('/view/<int:user_id>', methods=['GET'])
@login_required
def view_profile(user_id):
    try:
        user = User.query.get_or_404(user_id)
        is_friend = Friendship.query.filter_by(user_id=current_user.id, friend_id=user_id).first() is not None
        results = TestResult.query.filter_by(user_id=user_id, is_public=True).order_by(TestResult.timestamp.desc()).all()
        status = UserStatus.query.filter_by(user_id=user_id).first()
        
        stats = {
            'total_tests': len(results),
            'reading_tests': sum(1 for r in results if r.test_type == 'reading'),
            'listening_tests': sum(1 for r in results if r.test_type == 'listening'),
            'writing_tests': sum(1 for r in results if r.test_type == 'writing'),
            'speaking_tests': sum(1 for r in results if r.test_type == 'speaking'),
            'avg_reading': 0,
            'avg_listening': 0,
            'avg_writing': 0,
            'avg_speaking': 0
        }
        
        reading_scores = [r.score.get('percentage', 0) for r in results if r.test_type == 'reading' and 'percentage' in r.score]
        listening_scores = [r.score.get('percentage', 0) for r in results if r.test_type == 'listening' and 'percentage' in r.score]
        writing_scores = [r.score.get('overall', 0) for r in results if r.test_type == 'writing' and 'overall' in r.score]
        speaking_scores = [r.score.get('overall', 0) for r in results if r.test_type == 'speaking' and 'overall' in r.score]
        
        stats['avg_reading'] = sum(reading_scores) / len(reading_scores) if reading_scores else 0
        stats['avg_listening'] = sum(listening_scores) / len(listening_scores) if listening_scores else 0
        stats['avg_writing'] = sum(writing_scores) / len(writing_scores) if writing_scores else 0
        stats['avg_speaking'] = sum(speaking_scores) / len(speaking_scores) if speaking_scores else 0
        
        return render_template('user_profile.html', user=user, results=results, stats=stats, is_friend=is_friend, status=status)
    except Exception as e:
        logger.error(f"Error loading profile for user {user_id} by user {current_user.id}: {str(e)}", exc_info=True)
        return render_template('user_profile.html', user=None, results=[], stats={}, is_friend=False, status=None, error=f"Failed to load profile: {str(e)}")