from src.constants.http_status_codes import HTTP_400_BAD_REQUEST
from src.constants.http_status_codes import HTTP_401_UNAUTHORIZED
from src.constants.http_status_codes import HTTP_404_NOT_FOUND
from src.constants.http_status_codes import HTTP_409_CONFLICT
from src.constants.http_status_codes import HTTP_200_OK
from src.constants.http_status_codes import HTTP_201_CREATED
from src.constants.http_status_codes import HTTP_202_ACCEPTED
from src.constants.http_status_codes import HTTP_204_NO_CONTENT
from flask import Blueprint, request
from src.database import Message, Mfile, User, Company, db
from flask import Blueprint, request, jsonify
import validators
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
import time
from datetime import datetime

messages = Blueprint("message", __name__, url_prefix="/api/v1/messages")

@messages.post('/<int:id>')
@jwt_required()
def create_message(id):
    current_user = get_jwt_identity()

    if not Company.query.filter_by(id = id).first():
        return jsonify({'error': "Company not found"}), HTTP_404_NOT_FOUND

    body = request.form['body']

    if not body:
        return jsonify({'error': "Message body must not be empty"}), HTTP_400_BAD_REQUEST 

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
            
    message = Message(company_id=id, user_id=current_user, body=body, created_at=datetime.now(), updated_at=datetime.now())
    db.session.add(message)
    db.session.commit()
        
    attachments = []

    for file in files:

        file_size = len(file.read())
        file.seek(0)
        # Append a unique micro timestamp to the filename
        timestamp = int(time.time() * 1000000)

        # Get the absolute path of the current working directory
        app_root = os.path.dirname(os.path.abspath(__file__))

        user_directory = os.path.join(app_root, 'static', 'files', str(current_user),'messages')
        os.makedirs(user_directory, exist_ok=True)
        
        file_path = os.path.join(user_directory, f'{timestamp}_{secure_filename(file.filename)}')

        # Save the file to disk
        file.save(file_path)

        mfile = Mfile(message_id= message.id, name=file_path, type=str(file.content_type), size=str(file_size), created_at=datetime.now(), updated_at=datetime.now())
        db.session.add(mfile)
        db.session.commit()

        attachments.append({
            'id': mfile.id,
            'name': mfile.name,
            'type' : mfile.type,
            'size' : mfile.size,
            'created_at' : mfile.created_at,
            'updated_at' : mfile.updated_at,
        })

    return jsonify({
        'id': message.id,
        'company_id': message.company_id,
        'user_id': message.user_id,
        'body': message.body,
        'created_at': message.created_at,
        'updated_at': message.updated_at,
        'attachments' : attachments
    }), HTTP_201_CREATED

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'heif', 'png', 'jpg', 'jpeg', 'pdf', 'xls', 'xlsx', 'mp4', 'mp3'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_file_size(file):
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    return len(file.read()) <= MAX_CONTENT_LENGTH


@messages.get("/<int:id>")
@jwt_required()
def get_message(id):
    current_user = get_jwt_identity()

    message = Message.query.filter_by(id=id).first()

    if not message:
        return jsonify({'message': "Message not found"}),HTTP_404_NOT_FOUND
    
    company = Company.query.filter_by(id=message.company_id).first()

    if current_user == message.user_id or current_user == company.user_id:
        pass
    else:
        return jsonify({'error': "Unauthorized User"}),HTTP_401_UNAUTHORIZED
    
    mfiles = Mfile.query.filter_by(message_id=id)
    attachments = []
    for mfile in mfiles:

        attachments.append({
                'id': mfile.id,
                'name': mfile.name,
                'type' : mfile.type,
                'size' : mfile.size,
                'created_at' : mfile.created_at,
                'updated_at' : mfile.updated_at,
            })
    
    return jsonify({
            'id': message.id,
            'company_id': message.company_id,
            'user_id': message.user_id,
            'body': message.body,
            'created_at': message.created_at,
            'updated_at': message.updated_at,
            'attachments': attachments
        }), HTTP_200_OK


@messages.route('/companies/<int:id>', methods=['GET'])
@jwt_required()
def get_company_messages(id):
    current_user = get_jwt_identity()

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    company=Company.query.filter_by(id=id, user_id=current_user).first()

    if not company:
        return jsonify({'error': "Unauthorized User"}),HTTP_401_UNAUTHORIZED

    messages = Message.query.filter_by(company_id=company.id).paginate(page=page, per_page=per_page)

    data = []

    for message in messages.items:
        mfiles = Mfile.query.filter_by(message_id=message.id)
        attachments = []
        for mfile in mfiles:

            attachments.append({
                    'id': mfile.id,
                    'name': mfile.name,
                    'type' : mfile.type,
                    'size' : mfile.size,
                    'created_at' : mfile.created_at,
                    'updated_at' : mfile.updated_at,
                })
        data.append({
            'id': message.id,
            'company_id': message.company_id,
            'user_id': message.user_id,
            'body': message.body,
            'created_at': message.created_at,
            'updated_at': message.updated_at,
            'attachments': attachments
        })

    meta={
        "page": messages.page,
        "pages": messages.pages,
        "total_count": messages.total,
        "prev_page": messages.prev_num,
        "next_page": messages.next_num,
        "has_next": messages.has_next,
        "has_prev": messages.has_prev
    }

    return jsonify({'data': data, 'meta':meta}), HTTP_200_OK


@messages.route('/', methods=['GET'])
@jwt_required()
def get_user_messages():
    current_user = get_jwt_identity()

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    messages = Message.query.filter_by(user_id=current_user).paginate(page=page, per_page=per_page)

    if not messages:
        return jsonify({'error': "Error getting reviews"}), HTTP_400_BAD_REQUEST

    data = []

    for message in messages.items:
        mfiles = Mfile.query.filter_by(message_id=message.id)
        attachments = []
        for mfile in mfiles:

            attachments.append({
                    'id': mfile.id,
                    'name': mfile.name,
                    'type' : mfile.type,
                    'size' : mfile.size,
                    'created_at' : mfile.created_at,
                    'updated_at' : mfile.updated_at,
                })
        
        data.append({
            'id': message.id,
            'company_id': message.company_id,
            'user_id': message.user_id,
            'body': message.body,
            'created_at': message.created_at,
            'updated_at': message.updated_at,
            'attachments': attachments
        })

    meta={
        "page": messages.page,
        "pages": messages.pages,
        "total_count": messages.total,
        "prev_page": messages.prev_num,
        "next_page": messages.next_num,
        "has_next": messages.has_next,
        "has_prev": messages.has_prev
    }

    return jsonify({'data': data, 'meta':meta}), HTTP_200_OK


@messages.delete('/<int:id>')
@jwt_required()
def delete_message(id):
    current_user = get_jwt_identity()

    message = Message.query.filter_by(id =id).first()

    if not message:
        return jsonify({'msg': "Message not found"}), HTTP_404_NOT_FOUND
    
    if not message.user_id == current_user:
        return jsonify({'error': "Unauthorized User"}), HTTP_401_UNAUTHORIZED
    
    mfiles = Mfile.query.filter_by(message_id =id)

    for mfile in mfiles:
        if os.path.exists(mfile.name):
            os.remove(mfile.name)

    db.session.delete(message)
    db.session.commit()

    return jsonify({}), HTTP_204_NO_CONTENT