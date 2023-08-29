from src.constants.http_status_codes import HTTP_400_BAD_REQUEST
from src.constants.http_status_codes import HTTP_401_UNAUTHORIZED
from src.constants.http_status_codes import HTTP_404_NOT_FOUND
from src.constants.http_status_codes import HTTP_409_CONFLICT
from src.constants.http_status_codes import HTTP_200_OK
from src.constants.http_status_codes import HTTP_201_CREATED
from src.constants.http_status_codes import HTTP_202_ACCEPTED
from src.constants.http_status_codes import HTTP_204_NO_CONTENT
from flask import Blueprint, request
from src.database import Review, File, User, Branch, Company, db
from flask import Blueprint, request, jsonify
import validators
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
import time
from datetime import datetime

reviews = Blueprint("review", __name__, url_prefix="/api/v1/reviews")

@reviews.post('/<int:id>')
@jwt_required()
def create_review(id):
    current_user = get_jwt_identity()

    if not Branch.query.filter_by(id = id).first():
        return jsonify({'error': "Branch not found"}), HTTP_404_NOT_FOUND

    title = request.form['title']
    body = request.form['body']
    rating = request.form['rating']
    location = request.form['location']

    if not title or not location:
        return jsonify({'error': "Title and Location must not be empty"}), HTTP_400_BAD_REQUEST 
    
    if len(rating) > 0 and (rating.isalpha() or int(rating) > 5):
        return jsonify({'error': "Rating must be a valid number and not greater than 5"}), HTTP_400_BAD_REQUEST
    

    files = request.files.getlist('file')

    for file in files:
        if file:
            # Check the file extension
            if not allowed_file(file.filename):
                return 'Invalid file extension'

            # Check the file size
            if not allowed_file_size(file):
                return 'File size is too large'
            
            # Reset the pointer to the beginning of the file
            file.seek(0)

    review = Review(branch_id=id, user_id=current_user, title=title, body=body, rating=rating, location=location, created_at=datetime.now(), updated_at=datetime.now())

    db.session.add(review)
    db.session.commit()

    attachments = []

    for file in files:

        file_size = len(file.read())
        file.seek(0)
        # Append a unique micro timestamp to the filename
        timestamp = int(time.time() * 1000000)

        # Get the absolute path of the current working directory
        app_root = os.path.dirname(os.path.abspath(__file__))

        user_directory = os.path.join(app_root, 'static', 'files', str(current_user), 'reviews')
        os.makedirs(user_directory, exist_ok=True)
        
        file_path = os.path.join(user_directory, f'{timestamp}_{secure_filename(file.filename)}')

        # Save the file to disk
        file.save(file_path)

        rfile = File(review_id= review.id, name=file_path, type=str(file.content_type), size=str(file_size), created_at=datetime.now(), updated_at=datetime.now())
        db.session.add(rfile)
        db.session.commit()

        attachments.append({
            'id': rfile.id,
            'name': rfile.name,
            'type' : rfile.type,
            'size' : file_size,
            'created_at' : rfile.created_at,
            'updated_at' : rfile.updated_at,
        })

    return jsonify({
        'id': review.id,
        'branch_id': review.branch_id,
        'user_id': review.user_id,
        'title': review.title,
        'body': review.body,
        'rating': review.rating,
        'location': review.location,
        'created_at': review.created_at,
        'updated_at': review.updated_at,
        'attachments' : attachments
    }), HTTP_201_CREATED

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'heif', 'png', 'jpg', 'jpeg', 'pdf', 'xls', 'xlsx', 'mp4', 'mp3'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_file_size(file):
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    return len(file.read()) <= MAX_CONTENT_LENGTH


@reviews.get("/<int:id>")
@jwt_required()
def get_review(id):
    current_user = get_jwt_identity()

    review = Review.query.filter_by(id=id).first()

    if not review:
        return jsonify({'message': "Review not found"}),HTTP_404_NOT_FOUND
    
    branch = Branch.query.filter_by(id=review.branch_id).first()

    company = Company.query.filter_by(id=branch.company_id).first()

    if current_user == review.user_id or current_user == company.user_id:
        pass
    else:
        return jsonify({'error': "Unauthorized User"}),HTTP_401_UNAUTHORIZED
    
    rfiles = File.query.filter_by(review_id=id)

    attachments = []

    for rfile in rfiles:
        attachments.append({
            'id': rfile.id,
            'name': rfile.name,
            'type' : rfile.type,
            'size' : rfile.size,
            'created_at' : rfile.created_at,
            'updated_at' : rfile.updated_at,
        })
    
    return jsonify({
            'id': review.id,
            'branch_id': review.branch_id,
            'user_id': review.user_id,
            'title': review.title,
            'body': review.body,
            'rating': review.rating,
            'location': review.location,
            'created_at': review.created_at,
            'updated_at': review.updated_at,
            'attachments': attachments
        }), HTTP_200_OK


@reviews.route('/branches/<int:id>', methods=['GET'])
@jwt_required()
def get_branch_reviews(id):
    current_user = get_jwt_identity()

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    branch=Branch.query.filter_by(id=id).first()

    company=Company.query.filter_by(id=branch.company_id, user_id=current_user).first()

    if not company:
        return jsonify({'error': "Unauthorized User"}),HTTP_401_UNAUTHORIZED

    reviews = Review.query.filter_by(branch_id=id).paginate(page=page, per_page=per_page)

    data = []

    for review in reviews.items:

        rfiles = File.query.filter_by(review_id=review.id)

        attachments = []

        for rfile in rfiles:
            attachments.append({
                'id': rfile.id,
                'name': rfile.name,
                'type' : rfile.type,
                'size' : rfile.size,
                'created_at' : rfile.created_at,
                'updated_at' : rfile.updated_at,
            })
        data.append({
            'id': review.id,
            'branch_id': review.branch_id,
            'user_id': review.user_id,
            'title': review.title,
            'body': review.body,
            'rating': review.rating,
            'location': review.location,
            'created_at': review.created_at,
            'updated_at': review.updated_at,
            'attachments': attachments
        })

    meta={
        "page": reviews.page,
        "pages": reviews.pages,
        "total_count": reviews.total,
        "prev_page": reviews.prev_num,
        "next_page": reviews.next_num,
        "has_next": reviews.has_next,
        "has_prev": reviews.has_prev
    }

    return jsonify({'data': data, 'meta':meta}), HTTP_200_OK


@reviews.route('/', methods=['GET'])
@jwt_required()
def get_user_reviews():
    current_user = get_jwt_identity()

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    reviews = Review.query.filter_by(user_id=current_user).paginate(page=page, per_page=per_page)

    if not reviews:
        return jsonify({'error': "Error getting reviews"}), HTTP_400_BAD_REQUEST

    data = []

    for review in reviews.items:

        rfiles = File.query.filter_by(review_id=review.id)

        attachments = []

        for rfile in rfiles:
            attachments.append({
                'id': rfile.id,
                'name': rfile.name,
                'type' : rfile.type,
                'size' : rfile.size,
                'created_at' : rfile.created_at,
                'updated_at' : rfile.updated_at,
            })
            
            data.append({
                'id': review.id,
                'branch_id': review.branch_id,
                'user_id': review.user_id,
                'title': review.title,
                'body': review.body,
                'rating': review.rating,
                'location': review.location,
                'created_at': review.created_at,
                'updated_at': review.updated_at,
                'attanchments': attachments
            })

    meta={
        "page": reviews.page,
        "pages": reviews.pages,
        "total_count": reviews.total,
        "prev_page": reviews.prev_num,
        "next_page": reviews.next_num,
        "has_next": reviews.has_next,
        "has_prev": reviews.has_prev
    }

    return jsonify({'data': data, 'meta':meta}), HTTP_200_OK


@reviews.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_review(id):
    current_user = get_jwt_identity()

    review = Review.query.filter_by(id =id).first()

    if not review:
        return jsonify({'msg': "Review not found"}), HTTP_404_NOT_FOUND
    
    if not review.user_id == current_user:
        return jsonify({'error': "Unauthorized User"}), HTTP_401_UNAUTHORIZED
    
    rfiles = File.query.filter_by(review_id =id)

    for rfile in rfiles:
        if os.path.exists(rfile.name):
            os.remove(rfile.name)

    db.session.delete(review)
    db.session.commit()

    return jsonify({}), HTTP_204_NO_CONTENT