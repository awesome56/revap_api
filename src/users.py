from src.constants.http_status_codes import HTTP_400_BAD_REQUEST
from src.constants.http_status_codes import HTTP_401_UNAUTHORIZED
from src.constants.http_status_codes import HTTP_404_NOT_FOUND
from src.constants.http_status_codes import HTTP_409_CONFLICT
from src.constants.http_status_codes import HTTP_200_OK
from src.constants.http_status_codes import HTTP_201_CREATED
from src.constants.http_status_codes import HTTP_202_ACCEPTED
from src.constants.http_status_codes import HTTP_204_NO_CONTENT
from flask import Blueprint, request
from src.database import User, Company, Message, Mfile, Branch, Review, File, db
from flask import Blueprint, request, jsonify
import validators
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
import shutil
import time
from datetime import datetime
from flasgger import swag_from

users = Blueprint("user", __name__, url_prefix="/api/v1/users")

@users.put('/')
@users.patch('/')
@jwt_required()
@swag_from('./docs/user/edituser.yml')
def edit_user():

    current_user = get_jwt_identity()

    user = User.query.filter_by(id=current_user).first()

    if not user:
        return jsonify({'message': "User not found"}), HTTP_404_NOT_FOUND

    name = request.get_json().get('name','')
    # email = request.get_json().get('email','')

    if not name:
        return jsonify({'error': "Name required"}), HTTP_400_BAD_REQUEST 
    
    # if not validators.email(email):
    #     return jsonify({'error': "Email must be a valid email"}), HTTP_400_BAD_REQUEST
            
    # if user.email != email:
    #     if User.query.filter_by(email=email).first():
    #         return jsonify({'error': "Email already exists"}), HTTP_409_CONFLICT
    
    user.name=name
    # user.email=email
    user.updated_at=datetime.now()

    db.session.commit()

    return jsonify({
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'verified': user.verified,
        'created_at': user.created_at,
        'updated_at': user.updated_at,
    }), HTTP_200_OK

@users.delete("/")
@jwt_required()
@swag_from('./docs/user/deleteuser.yml')
def delete_user():
    current_user = get_jwt_identity()

    user = User.query.filter_by(id=current_user).first()

    if not user:
        return jsonify({'msg': "User not found"}), HTTP_404_NOT_FOUND
    
    app_root = os.path.dirname(os.path.abspath(__file__))

    companies= Company.query.filter_by(user_id = current_user)

    for company in companies:

        messages = Message.query.filter_by(company_id =company.id)
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

    user_directory = os.path.join(app_root, 'static', 'files', str(current_user))
    
    db.session.delete(user)
    db.session.commit()

    if os.path.exists(user_directory):
            shutil.rmtree(user_directory)
    
    return jsonify({}), HTTP_204_NO_CONTENT