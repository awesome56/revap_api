from src.constants.http_status_codes import HTTP_400_BAD_REQUEST
from src.constants.http_status_codes import HTTP_401_UNAUTHORIZED
from src.constants.http_status_codes import HTTP_404_NOT_FOUND
from src.constants.http_status_codes import HTTP_409_CONFLICT
from src.constants.http_status_codes import HTTP_200_OK
from src.constants.http_status_codes import HTTP_201_CREATED
from src.constants.http_status_codes import HTTP_202_ACCEPTED
from src.constants.http_status_codes import HTTP_204_NO_CONTENT
from flask import Blueprint, request
from src.database import Company, Message, Branch, Review, Mfile, File, db
from flask import Blueprint, request, jsonify
from src.constants.functions import adjust_url
import validators
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
import time
from datetime import datetime


companies = Blueprint("company", __name__, url_prefix="/api/v1/companies")

@companies.post("/")
@jwt_required()
def create_company():
    current_user = get_jwt_identity()
    name = request.get_json().get('name','')
    email = request.get_json().get('email','')
    website = request.get_json().get('website','')
    ceo = request.get_json().get('ceo','')
    head_office = request.get_json().get('head_office','')

    if not name:
        return jsonify({'error': "Name must not be empty"}), HTTP_400_BAD_REQUEST 
    
    if len(email) > 0 and not validators.email(email):
        return jsonify({'error': "Email must be a valid email"}), HTTP_400_BAD_REQUEST
    
    if len(website) > 0:
            adjusted_url = adjust_url(website)
            if not adjusted_url:
                return jsonify({'error': "Website must be a valid url"}), HTTP_400_BAD_REQUEST
            
    
    if Company.query.filter_by(user_id=current_user, name=name).first():
        return jsonify({'error': "Company name already exists for user"}), HTTP_409_CONFLICT
    
    company = Company(user_id=current_user, name=name, email=email, website=website, ceo=ceo, head_office=head_office, verified=0, created_at=datetime.now(), updated_at=datetime.now())
    db.session.add(company)
    db.session.commit()

    return jsonify({
        'id': company.id,
        'name': company.name,
        'email': company.email,
        'website': company.website,
        'img': company.img,
        'ceo': company.ceo,
        'verified': company.verified,
        'head_office': company.head_office,
        'created_at': company.created_at,
        'updated_at': company.updated_at,
    }), HTTP_201_CREATED

        
@companies.route('/', methods=['GET'])
@jwt_required()
def get_companies():
    current_user = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    companies=Company.query.filter_by(user_id=current_user).paginate(page=page, per_page=per_page)

    data = []

    for company in companies.items:
        data.append({
            'id': company.id,
            'name': company.name,
            'email': company.email,
            'website': company.website,
            'img': company.img,
            'ceo': company.ceo,
            'verified': company.verified,
            'head_office': company.head_office,
            'created_at': company.created_at,
            'updated_at': company.updated_at,
        })

    meta={
        "page": companies.page,
        "pages": companies.pages,
        "total_count": companies.total,
        "prev_page": companies.prev_num,
        "next_page": companies.next_num,
        "has_next": companies.has_next,
        "has_prev": companies.has_prev
    }

    return jsonify({'data': data, 'meta':meta}), HTTP_200_OK

@companies.route('/dp/<int:id>', methods=['POST'])
@jwt_required()
def dp_companies(id):
    current_user = get_jwt_identity()

    if not Company.query.filter_by(id=id).first():
        return jsonify({'message': "Item not found"}),HTTP_404_NOT_FOUND

    company = Company.query.filter_by(id=id, user_id=current_user).first()

    oldfile = company.img

    if not company:
        return jsonify({'error': "Unauthorized User"}),HTTP_401_UNAUTHORIZED
    
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

    company.img = file_path

    db.session.commit()

    if os.path.exists(oldfile):
 
        os.remove(oldfile)

    return jsonify({'img': company.img}),HTTP_201_CREATED

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'heif', 'png', 'jpg', 'jpeg'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_file_size(file):
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    return len(file.read()) <= MAX_CONTENT_LENGTH


@companies.get("/<int:id>")
def get_company(id):

    company = Company.query.filter_by(id=id).first()

    if not company:
        return jsonify({'message': "Item not found"}),HTTP_404_NOT_FOUND
    
    return jsonify({
            'id': company.id,
            'name': company.name,
            'email': company.email,
            'website': company.website,
            'img': company.img,
            'ceo': company.ceo,
            'verified': company.verified,
            'head_office': company.head_office,
            'created_at': company.created_at,
            'updated_at': company.updated_at,
        }), HTTP_200_OK


@companies.put('/<int:id>')
@companies.patch('/<int:id>')
@jwt_required()
def edit_company(id):

    current_user = get_jwt_identity()

    if not Company.query.filter_by(id=id).first():
        return jsonify({'message': "Item not found"}), HTTP_404_NOT_FOUND

    company = Company.query.filter_by(user_id=current_user, id=id).first()

    if not company:
        return jsonify({'error': "Unauthorized User"}), HTTP_401_UNAUTHORIZED

    name = request.get_json().get('name','')
    email = request.get_json().get('email','')
    website = request.get_json().get('website','')
    img = request.get_json().get('img','')
    ceo = request.get_json().get('ceo','')
    head_office = request.get_json().get('head_office','')

    if not name:
        return jsonify({'error': "Name must not be empty"}), HTTP_400_BAD_REQUEST 
    
    if len(email) > 0 and not validators.email(email):
        return jsonify({'error': "Email must be a valid email"}), HTTP_400_BAD_REQUEST
    
    if len(website) > 0:
            adjusted_url = adjust_url(website)
            if not adjusted_url:
                return jsonify({'error': "Website must be a valid url"}), HTTP_400_BAD_REQUEST
            
    if company.name != name:
        if Company.query.filter_by(user_id=current_user, name=name).first():
            return jsonify({'error': "Company name already exists for user"}), HTTP_409_CONFLICT
    
    company.name=name
    company.email=email
    company.website=website
    company.img=img
    company.ceo=ceo
    company.head_office=head_office
    company.updated_at=datetime.now()

    db.session.commit()

    return jsonify({
        'id': company.id,
        'name': company.name,
        'email': company.email,
        'website': company.website,
        'img': company.img,
        'ceo': company.ceo,
        'verified': company.verified,
        'head_office': company.head_office,
        'created_at': company.created_at,
        'updated_at': company.updated_at,
    }), HTTP_200_OK


@companies.delete("/<int:id>")
@jwt_required()
def delete_company(id):
    current_user = get_jwt_identity()

    if not Company.query.filter_by(id=id).first():
        return jsonify({'message': "Item not found"}),HTTP_404_NOT_FOUND

    company = Company.query.filter_by(id=id, user_id=current_user).first()

    if not company:
        return jsonify({'error': "Unauthorized User"}),HTTP_401_UNAUTHORIZED
    
    messages = Message.query.filter_by(company_id =id)
    for message in messages:
        mfiles = Mfile.query.filter_by(message_id =message.id)
        for mfile in mfiles:
            if os.path.exists(mfile.name):
                os.remove(mfile.name)
        
    branches = Branch.query.filter_by(company_id=id)
    for branch in branches:
        if os.path.exists(branch.img):
                os.remove(branch.img)
        reviews = Review.query.filter_by(branch_id =id)
        for review in reviews:
            rfiles = File.query.filter_by(review_id =review.id)
            for rfile in rfiles:
                if os.path.exists(rfile.name):
                    os.remove(rfile.name)
        
    if os.path.exists(company.img):
            os.remove(company.img)
    
    db.session.delete(company)
    db.session.commit()
    
    return jsonify({}), HTTP_204_NO_CONTENT