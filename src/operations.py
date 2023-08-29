from src.constants.http_status_codes import HTTP_400_BAD_REQUEST
from src.constants.http_status_codes import HTTP_401_UNAUTHORIZED
from src.constants.http_status_codes import HTTP_404_NOT_FOUND
from src.constants.http_status_codes import HTTP_409_CONFLICT
from src.constants.http_status_codes import HTTP_200_OK
from src.constants.http_status_codes import HTTP_201_CREATED
from src.constants.http_status_codes import HTTP_202_ACCEPTED
from src.constants.http_status_codes import HTTP_204_NO_CONTENT
from flask import Blueprint, request
from src.database import Company, Branch, Review, File, db
from flask import Blueprint, request, jsonify
import validators
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
import time

operations = Blueprint("operation", __name__, url_prefix="/api/v1/operations")

@operations.route('/search/companies/<item>', methods=['GET'])
# @jwt_required()
def search_companies(item):

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    companies=Company.query.filter(Company.name.like(f'%{item}%')).paginate(page=page, per_page=per_page)

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

@operations.route('/search/branches/<item>', methods=['GET'])
# @jwt_required()
def search_branches(item):

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    branches=Branch.query.filter(Branch.name.like(f'%{item}%')).paginate(page=page, per_page=per_page)

    data = []

    for branch in branches.items:
        data.append({
            'id': branch.id,
            'name': branch.name,
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