from functools import wraps
from typing import Callable, Iterable

from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from .models import User


def require_roles(roles: Iterable[str]):
    role_set = set(roles)

    def decorator(fn: Callable):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = User.query.get(int(user_id))
            if not user or not user.is_active or user.role not in role_set:
                return jsonify({"message": "无权限"}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator

