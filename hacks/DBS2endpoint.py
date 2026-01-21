from flask import Blueprint, jsonify, request
from flask_restful import Api, Resource
import requests
import random

from hacks.DBS2data import *

DBS2_api = Blueprint('DBS2_api', __name__,
                   url_prefix='/api/DBS2')

api = Api(DBS2_api)

# Banned words for password filtering
BANNED_WORDS = [
    'fuck', 'shit', 'damn', 'bitch', 'ass', 'dick', 'cock', 'pussy', 'cunt',
    'fag', 'nigger', 'nigga', 'retard', 'slut', 'whore', 'porn', 'sex',
    'nazi', 'hitler', 'rape', 'kill', 'murder', 'die', 'kys'
]

def contains_banned_word(text):
    """Check if text contains any banned words"""
    lower = text.lower()
    return any(banned in lower for banned in BANNED_WORDS)


class _Read(Resource):
    """GET /api/DBS2 - Get all items"""
    def get(self):
        return jsonify(getDBS2Items())


class _ReadID(Resource):
    """GET /api/DBS2/{id} - Get item by ID, PUT to update"""
    def get(self, id):
        item = getDBS2Item(id)
        if item:
            return jsonify(item)
        return {'error': 'Item not found'}, 404
    
    def put(self, id):
        data = request.get_json()
        if not data:
            return {'error': 'No data provided'}, 400
        
        item = updateDBS2Item(id, data)
        if item:
            return jsonify(item)
        return {'error': 'Item not found'}, 404


class _ReadRandom(Resource):
    """GET /api/DBS2/random - Get random item"""
    def get(self):
        item = getRandomDBS2Item()
        if item:
            return jsonify(item)
        return {'error': 'No items'}, 404


class _ReadCount(Resource):
    """GET /api/DBS2/count - Get item count"""
    def get(self):
        count = countDBS2Items()
        return jsonify({'count': count})


class _Passwords(Resource):
    """
    GET /api/DBS2/passwords - Get global passwords
    PUT /api/DBS2/passwords - Update global passwords
    """
    def get(self):
        passwords = getPasswords()
        return jsonify({
            'name': 'passwords',
            'data': passwords,
            'count': len(passwords)
        })
    
    def put(self):
        data = request.get_json()
        if not data:
            return {'error': 'No data provided'}, 400
        
        passwords = data.get('data') or data.get('passwords')
        if not passwords or not isinstance(passwords, list):
            return {'error': 'passwords array required'}, 400
        
        # Filter out invalid passwords
        valid_passwords = []
        for pw in passwords:
            if isinstance(pw, str) and len(pw) >= 4 and not contains_banned_word(pw):
                # Only lowercase letters
                clean = ''.join(c for c in pw.lower() if c.isalpha())
                if len(clean) >= 4:
                    valid_passwords.append(clean)
        
        if not valid_passwords:
            return {'error': 'No valid passwords provided'}, 400
        
        # Limit to 5
        valid_passwords = valid_passwords[:5]
        
        updated = updatePasswords(valid_passwords)
        return jsonify({
            'name': 'passwords',
            'data': updated,
            'count': len(updated),
            'message': 'Passwords updated successfully'
        })


class _PasswordRotate(Resource):
    """
    POST /api/DBS2/passwords/rotate
    Remove old password and add new one (used by minigame)
    Body: { "old": "oldpassword", "new": "newpassword" }
    """
    def post(self):
        data = request.get_json()
        if not data:
            return {'error': 'No data provided'}, 400
        
        old_pw = data.get('old', '').lower().strip()
        new_pw = data.get('new', '').lower().strip()
        
        # Validate new password
        if not new_pw or len(new_pw) < 4:
            return {'error': 'New password must be at least 4 characters'}, 400
        
        if contains_banned_word(new_pw):
            return {'error': 'Password contains inappropriate content'}, 400
        
        # Clean to only letters
        new_pw = ''.join(c for c in new_pw if c.isalpha())
        if len(new_pw) < 4:
            return {'error': 'Password must contain at least 4 letters'}, 400
        
        # Get current passwords
        passwords = getPasswords()
        
        # Remove old password if it exists
        if old_pw and old_pw in passwords:
            passwords.remove(old_pw)
        
        # Add new password if not duplicate
        if new_pw not in passwords:
            passwords.append(new_pw)
        
        # Keep only last 5
        if len(passwords) > 5:
            passwords = passwords[-5:]
        
        # Save
        updated = updatePasswords(passwords)
        
        return jsonify({
            'name': 'passwords',
            'data': updated,
            'count': len(updated),
            'message': f'Password rotated: removed "{old_pw}", added "{new_pw}"'
        })


# Register routes
api.add_resource(_Read, '', '/')
api.add_resource(_ReadID, '/<int:id>', '/<int:id>/')
api.add_resource(_ReadRandom, '/random', '/random/')
api.add_resource(_ReadCount, '/count', '/count/')
api.add_resource(_Passwords, '/passwords', '/passwords/')
api.add_resource(_PasswordRotate, '/passwords/rotate', '/passwords/rotate/')


if __name__ == "__main__": 
    server = 'https://dbs2.opencodingsociety.com'
    url = server + "/api/DBS2"
    
    # Test get passwords
    response = requests.get(url + "/passwords")
    print("Passwords:", response.json())