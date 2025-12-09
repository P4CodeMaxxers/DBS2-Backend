from flask import Blueprint, request, jsonify, g
from flask_restful import Api, Resource
from api.jwt_authorize import token_required
from model.dbs2_player import DBS2Player

dbs2_api = Blueprint('dbs2_api', __name__, url_prefix='/api/dbs2')
api = Api(dbs2_api)


class PlayerData(Resource):
    @token_required()
    def get(self):
        current_user = g.current_user
        player = DBS2Player.get_or_create(current_user.id)
        return jsonify(player.read())
    
    @token_required()
    def post(self):
        current_user = g.current_user
        player = DBS2Player.get_by_user_id(current_user.id)
        if player:
            return jsonify({'error': 'Player already exists'}), 400
        
        player = DBS2Player(user_id=current_user.id)
        player.create()
        return jsonify(player.read()), 201
    
    @token_required()
    def put(self):
        current_user = g.current_user
        player = DBS2Player.get_or_create(current_user.id)
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        player.update(data)
        return jsonify(player.read())
    
    @token_required()
    def delete(self):
        current_user = g.current_user
        player = DBS2Player.get_by_user_id(current_user.id)
        if not player:
            return jsonify({'error': 'Player not found'}), 404
        
        player.delete()
        return jsonify({'message': 'Player deleted'})


class Crypto(Resource):
    @token_required()
    def get(self):
        current_user = g.current_user
        player = DBS2Player.get_or_create(current_user.id)
        return jsonify({'crypto': player.crypto})
    
    @token_required()
    def put(self):
        current_user = g.current_user
        player = DBS2Player.get_or_create(current_user.id)
        data = request.get_json()
        
        if 'crypto' in data:
            player.update({'crypto': data['crypto']})
        elif 'add' in data:
            player.update({'add_crypto': data['add']})
        
        return jsonify({'crypto': player.crypto})


class Inventory(Resource):
    @token_required()
    def get(self):
        current_user = g.current_user
        player = DBS2Player.get_or_create(current_user.id)
        return jsonify({'inventory': player.inventory})
    
    @token_required()
    def post(self):
        current_user = g.current_user
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
    
    @token_required()
    def delete(self):
        current_user = g.current_user
        player = DBS2Player.get_or_create(current_user.id)
        data = request.get_json()
        
        if not data or 'index' not in data:
            return jsonify({'error': 'Index required'}), 400
        
        removed = player.remove_inventory_item(data['index'])
        if removed:
            return jsonify({'removed': removed, 'inventory': player.inventory})
        return jsonify({'error': 'Invalid index'}), 400


class Scores(Resource):
    @token_required()
    def get(self):
        current_user = g.current_user
        player = DBS2Player.get_or_create(current_user.id)
        return jsonify({'scores': player.scores})
    
    @token_required()
    def put(self):
        current_user = g.current_user
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
    @token_required()
    def get(self):
        current_user = g.current_user
        player = DBS2Player.get_or_create(current_user.id)
        return jsonify({
            'ash_trail': player._completed_ash_trail,
            'crypto_miner': player._completed_crypto_miner,
            'whackarat': player._completed_whackarat,
            'laundry': player._completed_laundry,
            'infinite_user': player._completed_infinite_user,
            'completed_all': player._completed_all
        })
    
    @token_required()
    def put(self):
        current_user = g.current_user
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
    # No auth required - public endpoint
    def get(self):
        limit = request.args.get('limit', 10, type=int)
        leaderboard = DBS2Player.get_leaderboard(limit)
        return jsonify({'leaderboard': leaderboard})


class AllPlayers(Resource):
    @token_required()
    def get(self):
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
    
    @token_required()
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


class BitcoinBoost(Resource):
    """
    Get Bitcoin price data for crypto miner boost.
    Uses CoinGecko API (free, no key required).
    Returns a multiplier based on Bitcoin's 24h price change.
    """
    def get(self):
        import requests
        
        try:
            # CoinGecko API - free, no API key needed
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                "ids": "bitcoin",
                "vs_currencies": "usd",
                "include_24hr_change": "true"
            }
            
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code != 200:
                return jsonify({
                    'boost_multiplier': 1.0,
                    'btc_change_24h': 0,
                    'error': 'Failed to fetch Bitcoin data'
                })
            
            data = response.json()
            btc_data = data.get('bitcoin', {})
            price = btc_data.get('usd', 0)
            change_24h = btc_data.get('usd_24h_change', 0)
            
            # Calculate boost multiplier based on 24h change
            # Positive change = bonus, negative change = penalty
            # Example: +10% change = 1.5x multiplier, -10% = 0.5x
            # Clamped between 0.5x and 2.0x
            boost = 1.0 + (change_24h / 20)  # Divide by 20 to scale nicely
            boost = max(0.5, min(2.0, boost))  # Clamp between 0.5 and 2.0
            
            return jsonify({
                'boost_multiplier': round(boost, 2),
                'btc_price_usd': round(price, 2),
                'btc_change_24h': round(change_24h, 2),
                'message': 'Bitcoin is up! Bonus crypto!' if change_24h > 0 else 'Bitcoin is down... reduced earnings'
            })
            
        except Exception as e:
            # If API fails, return neutral multiplier (no boost, no penalty)
            return jsonify({
                'boost_multiplier': 1.0,
                'btc_change_24h': 0,
                'error': str(e)
            })


api.add_resource(PlayerData, '/player')
api.add_resource(Crypto, '/crypto')
api.add_resource(Inventory, '/inventory')
api.add_resource(Scores, '/scores')
api.add_resource(Minigames, '/minigames')
api.add_resource(Leaderboard, '/leaderboard')
api.add_resource(AllPlayers, '/players')
api.add_resource(PlayerByUID, '/player/<string:uid>')
api.add_resource(BitcoinBoost, '/bitcoin-boost')