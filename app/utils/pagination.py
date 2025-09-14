# =============================
# app/utils/pagination.py
# =============================
from flask import request

def get_pagination():
    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 10))
    except ValueError:
        page, limit = 1, 10
    page = max(page, 1)
    limit = max(min(limit, 100), 1)
    offset = (page - 1) * limit
    return page, limit, offset
