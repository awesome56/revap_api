from src.constants.http_status_codes import HTTP_400_BAD_REQUEST
from src.constants.http_status_codes import HTTP_401_UNAUTHORIZED
from src.constants.http_status_codes import HTTP_404_NOT_FOUND
from src.constants.http_status_codes import HTTP_409_CONFLICT
from src.constants.http_status_codes import HTTP_200_OK
from src.constants.http_status_codes import HTTP_201_CREATED
from src.constants.http_status_codes import HTTP_202_ACCEPTED
from src.constants.http_status_codes import HTTP_204_NO_CONTENT
from flask import Blueprint, request
from src.database import User, Company, Branch, Message, Review, Verification, Mfile,File, db
from flask import Blueprint, request, jsonify
import validators
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
import time

admins = Blueprint("admin", __name__, url_prefix="/api/v1/admins")

@admins.route('/users', methods=['GET'])
# @jwt_required()
def get_users():
    # current_user = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    users=User.query.paginate(page=page, per_page=per_page)

    data = []

    for user in users.items:
        data.append({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'verified': user.verified,
            'created_at': user.created_at,
            'updated_at': user.updated_at
        })

    meta={
        "page": users.page,
        "pages": users.pages,
        "total_count": users.total,
        "prev_page": users.prev_num,
        "next_page": users.next_num,
        "has_next": users.has_next,
        "has_prev": users.has_prev
    }

    return jsonify({'data': data, 'meta':meta}), HTTP_200_OK


@admins.route('/branches', methods=['GET'])
# @jwt_required()
def get_branches():
    # current_user = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    branches=Branch.query.paginate(page=page, per_page=per_page)

    data = []

    for branch in branches.items:
        data.append({
            'id': branch.id,
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


@admins.route('/verifications', methods=['GET'])
# @jwt_required()
def get_verifications():
    # current_user = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    verifications=Verification.query.paginate(page=page, per_page=per_page)

    data = []

    for verification in verifications.items:
        data.append({
            'id': verification.id,
            'user_id': verification.user_id,
            'code': verification.code,
            'purpose': verification.purpose,
            'expiration': verification.expiration,
            'created_at': verification.created_at,
            'updated_at': verification.updated_at,
        })

    meta={
        "page": verifications.page,
        "pages": verifications.pages,
        "total_count": verifications.total,
        "prev_page": verifications.prev_num,
        "next_page": verifications.next_num,
        "has_next": verifications.has_next,
        "has_prev": verifications.has_prev
    }

    return jsonify({'data': data, 'meta':meta}), HTTP_200_OK


@admins.route('/messages', methods=['GET'])
# @jwt_required()
def get_messages():
    # current_user = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    messages=Message.query.paginate(page=page, per_page=per_page)

    data = []

    for message in messages.items:
        data.append({
            'id': message.id,
            'company_id': message.company_id,
            'user_id': message.user_id,
            'body': message.body,
            'created_at': message.created_at,
            'updated_at': message.updated_at,
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


@admins.route('/companies', methods=['GET'])
# @jwt_required()
def get_companies():
    # current_user = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    companies=Company.query.paginate(page=page, per_page=per_page)

    data = []

    for company in companies.items:
        data.append({
            'id': company.id,
            'name': company.name,
            'category': company.category,
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


@admins.route('/mfiles', methods=['GET'])
# @jwt_required()
def get_message_files():
    # current_user = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    mfiles=Mfile.query.paginate(page=page, per_page=per_page)

    data = []

    for mfile in mfiles.items:
        data.append({
            'id': mfile.id,
            'message_id':mfile.message_id,
            'name': mfile.name,
            'type': mfile.type,
            'size': mfile.size,
            'created_at': mfile.created_at,
            'updated_at': mfile.updated_at
        })

    meta={
        "page": mfiles.page,
        "pages": mfiles.pages,
        "total_count": mfiles.total,
        "prev_page": mfiles.prev_num,
        "next_page": mfiles.next_num,
        "has_next": mfiles.has_next,
        "has_prev": mfiles.has_prev
    }

    return jsonify({'data': data, 'meta':meta}), HTTP_200_OK

@admins.route('/reviews', methods=['GET'])
# @jwt_required()
def get_reviews():
    # current_user = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    reviews=Review.query.paginate(page=page, per_page=per_page)

    data = []

    for review in reviews.items:
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


@admins.route('/files', methods=['GET'])
# @jwt_required()
def get_review_files():
    # current_user = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    rfiles=File.query.paginate(page=page, per_page=per_page)

    data = []

    for rfile in rfiles.items:
        data.append({
            'id': rfile.id,
            'review_id': rfile.review_id,
            'name': rfile.name,
            'type': rfile.type,
            'size': rfile.size,
            'created_at': rfile.created_at,
            'updated_at': rfile.updated_at
        })

    meta={
        "page": rfiles.page,
        "pages": rfiles.pages,
        "total_count": rfiles.total,
        "prev_page": rfiles.prev_num,
        "next_page": rfiles.next_num,
        "has_next": rfiles.has_next,
        "has_prev": rfiles.has_prev
    }

    return jsonify({'data': data, 'meta':meta}), HTTP_200_OK