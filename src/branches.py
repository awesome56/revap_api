from src.constants.http_status_codes import HTTP_400_BAD_REQUEST
from src.constants.http_status_codes import HTTP_401_UNAUTHORIZED
from src.constants.http_status_codes import HTTP_404_NOT_FOUND
from src.constants.http_status_codes import HTTP_409_CONFLICT
from src.constants.http_status_codes import HTTP_200_OK
from src.constants.http_status_codes import HTTP_201_CREATED
from src.constants.http_status_codes import HTTP_204_NO_CONTENT
from flask import Blueprint, request
from src.database import Branch, Company, Review, File, db
from flask import Blueprint, request, jsonify
import validators
from flask_jwt_extended import jwt_required, get_jwt_identity
import re
from werkzeug.utils import secure_filename
import os
import time
import qrcode
from src.constants.functions import adjust_url, generate_random_code
from datetime import datetime

# Add description
# Add company_id

branches = Blueprint("branch", __name__, url_prefix="/api/v1/branches")

@branches.post("/company/<int:id>")
@jwt_required()
def add_branch(id):
    current_user = get_jwt_identity()

    if not Company.query.filter_by(id=id).first():
        return jsonify({'error': "Item not found"}), HTTP_404_NOT_FOUND

    if not Company.query.filter_by(id=id, user_id=current_user).first():
        return jsonify({'error': "Unauthorized user"}), HTTP_401_UNAUTHORIZED

    name = request.get_json().get('name','')
    description = request.get_json().get('description','')
    email = request.get_json().get('email','')
    phone = request.get_json().get('phone','')
    website = request.get_json().get('website','')
    manager = request.get_json().get('manager','')
    location = request.get_json().get('location','')
    

    if not name or not location:
        return jsonify({'error': "Name and Location are required"}), HTTP_400_BAD_REQUEST 
    
    if len(email) > 0 and not validators.email(email):
        return jsonify({'error': "Email must be a valid email"}), HTTP_400_BAD_REQUEST
    
    # if len(phone) > 0 and not isinstance(phone, int):
    #     return jsonify({'error': "Phone number must be a valid number"}), HTTP_400_BAD_REQUEST
    
    if len(website) > 0:
        adjusted_url = adjust_url(website)
        if not adjusted_url:
            return jsonify({'error': "Website must be a valid url"}), HTTP_400_BAD_REQUEST
            
    
    if Branch.query.filter_by(company_id=id, name=name).first():
        return jsonify({'error': "Branch name already exists for company"}), HTTP_409_CONFLICT
    
    code= generate_random_code(6)
    data = f'https://asltech.com.ng/{code}'
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    # Append a unique micro timestamp to the filename
    timestamp = int(time.time() * 1000000)

    # Get the absolute path of the current working directory
    app_root = os.path.dirname(os.path.abspath(__file__))

    user_directory = os.path.join(app_root, 'static', 'files', str(current_user))

    os.makedirs(user_directory, exist_ok=True)
    
    img_path = os.path.join(user_directory, f'{timestamp}_qrcode.png')

    qr_img.save(img_path)
    
    branch = Branch(company_id=id, name=name, description=description, email=email, phone=phone, website=website, img="", manager=manager, location=location, code=code, qrcode=img_path, created_at=datetime.now(), updated_at=datetime.now())
    db.session.add(branch)
    db.session.commit()

    return jsonify({
        'id': branch.id,
        'company_id': branch.company_id,
        'name': branch.name,
        'description': branch.description,
        'email': branch.email,
        'phone': branch.phone,
        'website': branch.website,
        'img': branch.img,
        'manager': branch.manager,
        'location': branch.location,
        'code': branch.code,
        'qrcode': branch.qrcode,
        'created_at': branch.created_at,
        'updated_at': branch.updated_at,
    }), HTTP_201_CREATED
        

@branches.route('/dp/<int:id>', methods=['POST'])
@jwt_required()
def dp_branches(id):
    current_user = get_jwt_identity()

    branch = Branch.query.filter_by(id=id).first()
    if not branch:
        return jsonify({'error': "Branch not found"}),HTTP_404_NOT_FOUND

    company = Company.query.filter_by(id=branch.company_id, user_id=current_user).first()

    if not company:
        return jsonify({'error': "Unauthorized User"}),HTTP_401_UNAUTHORIZED

    oldfile = branch.img
    
    if not request.files['dp']:
        return jsonify({'error': "File empty"}),HTTP_400_BAD_REQUEST

    # Get the file data from the request
    file = request.files['dp']

    # Check the file extension
    if not allowed_file(file.filename):
        return 'Invalid file extension'

    # Check the file size
    if not allowed_file_size(file):
        return 'File size is too large'
    
    # Reset the pointer to the beginning of the file
    file.seek(0)

    # Append a unique micro timestamp to the filename
    timestamp = int(time.time() * 1000000)

    # Get the absolute path of the current working directory
    app_root = os.path.dirname(os.path.abspath(__file__))

    user_directory = os.path.join(app_root, 'static', 'files', str(current_user))
    os.makedirs(user_directory, exist_ok=True)
    
    file_path = os.path.join(user_directory, f'{timestamp}_{secure_filename(file.filename)}')

    # Save the file to disk
    file.save(file_path)

    branch.img = file_path

    db.session.commit()

    if os.path.exists(oldfile):
 
        os.remove(oldfile)

    return jsonify({'img': branch.img}),HTTP_201_CREATED

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'heif', 'png', 'jpg', 'jpeg'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_file_size(file):
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    return len(file.read()) <= MAX_CONTENT_LENGTH


@branches.get("/company/<int:id>")
def get_company_branch(id):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    branches=Branch.query.filter_by(company_id=id).paginate(page=page, per_page=per_page)

    if not branches:
        return jsonify({'error': "Item not found"}),HTTP_404_NOT_FOUND

    data = []

    for branch in branches.items:
        data.append({
            'id': branch.id,
            'company_id': branch.company_id,
            'name': branch.name,
            'description': branch.description,
            'email': branch.email,
            'phone': branch.phone,
            'website': branch.website,
            'img': branch.img,
            'manager': branch.manager,
            'location': branch.location,
            'code': branch.code,
            'qrcode': branch.qrcode,
            'created_at': branch.created_at,
            'updated_at': branch.updated_at,
        })

    meta={
        "page": branches.page,
        "pages": branches.pages,
        "total_count": branches.total,
        "prev_page": branches.prev_num,
        "next_page": branches.next_num,
        "has_next": branches.has_next,
        "has_prev": branches.has_prev
    }

    return jsonify({'data': data, 'meta':meta}), HTTP_200_OK


@branches.get("/<int:id>")
def get_branch(id):

    branch = Branch.query.filter_by(id=id).first()

    if not branch:
        return jsonify({'error': "Item not found"}),HTTP_404_NOT_FOUND

    return jsonify({
            'id': branch.id,
            'company_id': branch.company_id,
            'name': branch.name,
            'description': branch.description,
            'email': branch.email,
            'phone': branch.phone,
            'website': branch.website,
            'img': branch.img,
            'manager': branch.manager,
            'location': branch.location,
            'code': branch.code,
            'qrcode': branch.qrcode,
            'created_at': branch.created_at,
            'updated_at': branch.updated_at,
        }), HTTP_200_OK


@branches.put('/<int:id>')
@branches.patch('/<int:id>')
@jwt_required()
def edit_branch(id):

    current_user = get_jwt_identity()

    branch = Branch.query.filter_by(id=id).first()

    if not branch:
        return jsonify({'error': "Branch not found"}),HTTP_404_NOT_FOUND

    company = Company.query.filter_by(id=branch.company_id, user_id=current_user).first()

    if not company:
        return jsonify({'error': "Unauthorized User"}),HTTP_401_UNAUTHORIZED

    name = request.get_json().get('name','')
    description = request.get_json().get('description','')
    email = request.get_json().get('email','')
    phone = request.get_json().get('phone','')
    website = request.get_json().get('website','')
    manager = request.get_json().get('manager','')
    location = request.get_json().get('location','')

    if not name or not location:
        return jsonify({'error': "Name and Location are required"}), HTTP_400_BAD_REQUEST  
    
    if len(email) > 0 and not validators.email(email):
        return jsonify({'error': "Email must be a valid email"}), HTTP_400_BAD_REQUEST
    
    # if len(phone) > 0 and not isinstance(phone, int):
    #     return jsonify({'error': "Phone number must be a valid number"}), HTTP_400_BAD_REQUEST
    
    if len(website) > 0:
        adjusted_url = adjust_url(website)
        if not adjusted_url:
            return jsonify({'error': "Website must be a valid url"}), HTTP_400_BAD_REQUEST
            
    if branch.name != name:
        if Branch.query.filter_by(company_id=company.id, name=name).first():
            return jsonify({'error': "Branch name already exists for company"}), HTTP_409_CONFLICT

    branch.name = name
    branch.description = description
    branch.email = email
    branch.phone = phone
    branch.website = website
    branch.manager = manager
    branch.location = location
    branch.updated_at=datetime.now()

    db.session.commit()

    return jsonify({
        'id': branch.id,
        'company_id': branch.company_id,
        'name': branch.name,
        'description': branch.description,
        'email': branch.email,
        'phone': branch.phone,
        'website': branch.website,
        'img': branch.img,
        'manager': branch.manager,
        'location': branch.location,
        'code': branch.code,
        'qrcode': branch.qrcode,
        'created_at': branch.created_at,
        'updated_at': branch.updated_at
    }), HTTP_200_OK


@branches.delete("/<int:id>")
@jwt_required()
def delete_branch(id):
    current_user = get_jwt_identity()

    branch = Branch.query.filter_by(id=id).first()

    if not branch:
        return jsonify({'error': "Branch not found"}),HTTP_404_NOT_FOUND

    company = Company.query.filter_by(id=branch.company_id, user_id=current_user).first()

    if not company:
        return jsonify({'error': "Unauthorized User"}),HTTP_401_UNAUTHORIZED
    
    reviews = Review.query.filter_by(branch_id =id)
    for review in reviews:
        rfiles = File.query.filter_by(review_id =review.id)
        for rfile in rfiles:
            if os.path.exists(rfile.name):
                os.remove(rfile.name)
        
    if os.path.exists(branch.img):
            os.remove(branch.img)

    if os.path.exists(branch.qrcode):
            os.remove(branch.qrcode)
    
    db.session.delete(branch)
    db.session.commit()
    
    return jsonify({}), HTTP_204_NO_CONTENT