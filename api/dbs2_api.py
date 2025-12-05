from flask import Blueprint, request, jsonify, g
from flask_restful import Api, Resource
from flask_login import login_required, current_user
from model.dbs2_player import DBS2Player

dbs2_api = Blueprint('dbs2_api', __name__, url_prefix='/api/dbs2')
api = Api(dbs2_api)


class PlayerData(Resource):
    @login_required
    def get(self):
        player = DBS2Player.get_or_create(current_user.id)
        return jsonify(player.read())
    
    @login_required
    def post(self):
        player = DBS2Player.get_by_user_id(current_user.id)
        if player:
            return jsonify({'error': 'Player already exists'}), 400
        
        player = DBS2Player(user_id=current_user.id)
        player.create()
        return jsonify(player.read()), 201
    
    @login_required
    def put(self):
        player = DBS2Player.get_or_create(current_user.id)
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        player.update(data)
        return jsonify(player.read())
    
    @login_required
    def delete(self):
        player = DBS2Player.get_by_user_id(current_user.id)
        if not player:
            return jsonify({'error': 'Player not found'}), 404
        
        player.delete()
        return jsonify({'message': 'Player deleted'})


class Crypto(Resource):
    @login_required
    def get(self):
        player = DBS2Player.get_or_create(current_user.id)
        return jsonify({'crypto': player.crypto})
    
    @login_required
    def put(self):
        player = DBS2Player.get_or_create(current_user.id)
        data = request.get_json()
        
        if 'crypto' in data:
            player.update({'crypto': data['crypto']})
        elif 'add' in data:
            player.update({'add_crypto': data['add']})
        
        return jsonify({'crypto': player.crypto})


class Inventory(Resource):
    @login_required
    def get(self):
        player = DBS2Player.get_or_create(current_user.id)
        return jsonify({'inventory': player.inventory})
    
    @login_required
    def post(self):
        player = DBS2Player.get_or_create(current_user.id)
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({'error': 'Item name required'}), 400
        
        item = {
            'id': data.get('id', f'item_{len(player.inventory)}'),
            'name': data['name'],
            'found_at': data.get('found_at', 'unknown')
        }
        
        player.add_inventory_item(item)
        return jsonify({'inventory': player.inventory})
    
    @login_required
    def delete(self):
        player = DBS2Player.get_or_create(current_user.id)
        data = request.get_json()
        
        if 'index' not in data:
            return jsonify({'error': 'Index required'}), 400
        
        removed = player.remove_inventory_item(data['index'])
        if removed:
            return jsonify({'removed': removed, 'inventory': player.inventory})
        return jsonify({'error': 'Invalid index'}), 400


class Scores(Resource):
    @login_required
    def get(self):
        player = DBS2Player.get_or_create(current_user.id)
        return jsonify({'scores': player.scores})
    
    @login_required
    def put(self):
        player = DBS2Player.get_or_create(current_user.id)
        data = request.get_json()
        
        if 'game' not in data or 'score' not in data:
            return jsonify({'error': 'Game and score required'}), 400
        
        is_high = player.update_score(data['game'], data['score'])
        return jsonify({
            'is_high_score': is_high,
            'scores': player.scores
        })


class Minigames(Resource):
    @login_required
    def get(self):
        player = DBS2Player.get_or_create(current_user.id)
        return jsonify({
            'ash_trail': player._completed_ash_trail,
            'crypto_miner': player._completed_crypto_miner,
            'whackarat': player._completed_whackarat,
            'laundry': player._completed_laundry,
            'infinite_user': player._completed_infinite_user,
            'completed_all': player._completed_all
        })
    
    @login_required
    def put(self):
        player = DBS2Player.get_or_create(current_user.id)
        data = request.get_json()
        
        update_data = {}
        if 'ash_trail' in data:
            update_data['completed_ash_trail'] = data['ash_trail']
        if 'crypto_miner' in data:
            update_data['completed_crypto_miner'] = data['crypto_miner']
        if 'whackarat' in data:
            update_data['completed_whackarat'] = data['whackarat']
        if 'laundry' in data:
            update_data['completed_laundry'] = data['laundry']
        if 'infinite_user' in data:
            update_data['completed_infinite_user'] = data['infinite_user']
        
        player.update(update_data)
        
        return jsonify({
            'ash_trail': player._completed_ash_trail,
            'crypto_miner': player._completed_crypto_miner,
            'whackarat': player._completed_whackarat,
            'laundry': player._completed_laundry,
            'infinite_user': player._completed_infinite_user,
            'completed_all': player._completed_all
        })


class Leaderboard(Resource):
    def get(self):
        limit = request.args.get('limit', 10, type=int)
        leaderboard = DBS2Player.get_leaderboard(limit)
        return jsonify({'leaderboard': leaderboard})


class AllPlayers(Resource):
    @login_required
    def get(self):
        if not hasattr(current_user, 'role') or current_user.role != 'Admin':
            players = DBS2Player.get_all_players()
            return jsonify({'players': players})
        
        players = DBS2Player.get_all_players()
        return jsonify({'players': players})


class PlayerByUID(Resource):
    def get(self, uid):
        from model.user import User
        user = User.query.filter_by(_uid=uid).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        player = DBS2Player.get_by_user_id(user.id)
        if not player:
            return jsonify({'error': 'Player data not found'}), 404
        
        return jsonify(player.read())
    
    @login_required
    def put(self, uid):
        from model.user import User
        user = User.query.filter_by(_uid=uid).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        player = DBS2Player.get_by_user_id(user.id)
        if not player:
            return jsonify({'error': 'Player data not found'}), 404
        
        data = request.get_json()
        player.update(data)
        return jsonify(player.read())


api.add_resource(PlayerData, '/player')
api.add_resource(Crypto, '/crypto')
api.add_resource(Inventory, '/inventory')
api.add_resource(Scores, '/scores')
api.add_resource(Minigames, '/minigames')
api.add_resource(Leaderboard, '/leaderboard')
api.add_resource(AllPlayers, '/players')
api.add_resource(PlayerByUID, '/player/<string:uid>')