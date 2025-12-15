"""
DBS2 Game API - Complete Backend with Admin Panel Support
Place this in: api/dbs2_api.py

Works with the DBS2Player model structure that has:
- user_id (not _uid)
- Individual _completed_* fields (not _minigames_completed dict)
- read(), get_all_players(), get_leaderboard() methods
"""

from flask import Blueprint, request, g
from flask_restful import Api, Resource
from datetime import datetime
import requests

# Import your models and decorators
from model.dbs2_player import DBS2Player
from model.user import User
from __init__ import db
from api.jwt_authorize import token_required

# Create Blueprint
dbs2_api = Blueprint('dbs2_api', __name__, url_prefix='/api/dbs2')
api = Api(dbs2_api)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_current_player():
    """Get DBS2Player for current authenticated user, create if doesn't exist"""
    if not g.current_user:
        return None
    return DBS2Player.get_or_create(g.current_user.id)


def format_minigames(player):
    """Convert individual completion fields to dict format for API response"""
    return {
        'crypto_miner': player._completed_crypto_miner,
        'infinite_user': player._completed_infinite_user,
        'laundry': player._completed_laundry,
        'ash_trail': player._completed_ash_trail,
        'whackarat': player._completed_whackarat
    }


# ============================================================================
# PLAYER ENDPOINTS (Authenticated)
# ============================================================================

class _PlayerResource(Resource):
    """Get/Update current player's data"""
    
    @token_required()
    def get(self):
        """GET /api/dbs2/player - Get current player's full data"""
        player = get_current_player()
        if not player:
            return {'error': 'Not authenticated'}, 401
        return player.read(), 200
    
    @token_required()
    def put(self):
        """PUT /api/dbs2/player - Update player data"""
        player = get_current_player()
        if not player:
            return {'error': 'Not authenticated'}, 401
        
        data = request.get_json()
        player.update(data)
        return player.read(), 200


class _CryptoResource(Resource):
    """Manage player's crypto currency"""
    
    @token_required()
    def get(self):
        """GET /api/dbs2/crypto - Get current crypto balance"""
        player = get_current_player()
        if not player:
            return {'error': 'Not authenticated'}, 401
        return {'crypto': player._crypto}, 200
    
    @token_required()
    def put(self):
        """PUT /api/dbs2/crypto - Update crypto"""
        player = get_current_player()
        if not player:
            return {'error': 'Not authenticated'}, 401
        
        data = request.get_json()
        
        if 'crypto' in data:
            player._crypto = max(0, int(data['crypto']))
        elif 'add' in data:
            player._crypto = max(0, player._crypto + int(data['add']))
        
        db.session.commit()
        return {'crypto': player._crypto}, 200


class _InventoryResource(Resource):
    """Manage player's inventory"""
    
    @token_required()
    def get(self):
        """GET /api/dbs2/inventory"""
        player = get_current_player()
        if not player:
            return {'error': 'Not authenticated'}, 401
        return {'inventory': player.inventory}, 200
    
    @token_required()
    def post(self):
        """POST /api/dbs2/inventory - Add item"""
        player = get_current_player()
        if not player:
            return {'error': 'Not authenticated'}, 401
        
        data = request.get_json()
        item = {
            'name': data.get('name', 'Unknown Item'),
            'found_at': data.get('found_at', 'unknown'),
            'timestamp': datetime.now().isoformat()
        }
        
        player.add_inventory_item(item)
        return {'inventory': player.inventory}, 200
    
    @token_required()
    def delete(self):
        """DELETE /api/dbs2/inventory - Remove item by index"""
        player = get_current_player()
        if not player:
            return {'error': 'Not authenticated'}, 401
        
        data = request.get_json()
        index = data.get('index', -1)
        player.remove_inventory_item(index)
        return {'inventory': player.inventory}, 200


class _ScoresResource(Resource):
    """Manage player's game scores"""
    
    @token_required()
    def get(self):
        """GET /api/dbs2/scores"""
        player = get_current_player()
        if not player:
            return {'error': 'Not authenticated'}, 401
        return {'scores': player.scores}, 200
    
    @token_required()
    def put(self):
        """PUT /api/dbs2/scores - Update score for a game"""
        player = get_current_player()
        if not player:
            return {'error': 'Not authenticated'}, 401
        
        data = request.get_json()
        game = data.get('game')
        score = data.get('score', 0)
        
        if game:
            player.update_score(game, score)
        
        return {'scores': player.scores}, 200


class _MinigamesResource(Resource):
    """Track minigame completion"""
    
    @token_required()
    def get(self):
        """GET /api/dbs2/minigames"""
        player = get_current_player()
        if not player:
            return {'error': 'Not authenticated'}, 401
        return {'minigames_completed': format_minigames(player)}, 200
    
    @token_required()
    def put(self):
        """PUT /api/dbs2/minigames - Mark minigame complete"""
        player = get_current_player()
        if not player:
            return {'error': 'Not authenticated'}, 401
        
        data = request.get_json()
        
        # Map API names to model field names
        field_map = {
            'crypto_miner': 'completed_crypto_miner',
            'infinite_user': 'completed_infinite_user',
            'laundry': 'completed_laundry',
            'ash_trail': 'completed_ash_trail',
            'whackarat': 'completed_whackarat'
        }
        
        update_data = {}
        for game, completed in data.items():
            if game in field_map and completed:
                update_data[field_map[game]] = True
        
        if update_data:
            player.update(update_data)
        
        return {'minigames_completed': format_minigames(player)}, 200


# ============================================================================
# PUBLIC ENDPOINTS (No Auth Required)
# ============================================================================

class _LeaderboardResource(Resource):
    """Public leaderboard"""
    
    def get(self):
        """GET /api/dbs2/leaderboard?limit=10"""
        limit = min(int(request.args.get('limit', 10)), 100)
        leaderboard = DBS2Player.get_leaderboard(limit)
        
        # Add minigames_completed format for frontend compatibility
        for entry in leaderboard:
            entry['minigames_completed'] = {
                'crypto_miner': entry.get('completed_crypto_miner', False),
                'infinite_user': entry.get('completed_infinite_user', False),
                'laundry': entry.get('completed_laundry', False),
                'ash_trail': entry.get('completed_ash_trail', False),
                'whackarat': entry.get('completed_whackarat', False)
            }
        
        return {'leaderboard': leaderboard}, 200


class _BitcoinBoostResource(Resource):
    """Get Bitcoin price data for crypto miner minigame"""
    
    def get(self):
        """GET /api/dbs2/bitcoin-boost"""
        try:
            response = requests.get(
                'https://api.coingecko.com/api/v3/simple/price',
                params={
                    'ids': 'bitcoin',
                    'vs_currencies': 'usd',
                    'include_24hr_change': 'true'
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                btc_price = data['bitcoin']['usd']
                btc_change = data['bitcoin'].get('usd_24h_change', 0)
                
                boost = max(0.5, min(2.0, 1.0 + (btc_change / 20)))
                
                return {
                    'btc_price_usd': btc_price,
                    'btc_change_24h': round(btc_change, 2),
                    'boost_multiplier': round(boost, 2),
                    'message': f"BTC {'📈' if btc_change >= 0 else '📉'} {btc_change:+.2f}%"
                }, 200
        except Exception as e:
            print(f"Bitcoin API error: {e}")
        
        return {
            'btc_price_usd': 0,
            'btc_change_24h': 0,
            'boost_multiplier': 1.0,
            'message': 'Bitcoin data unavailable'
        }, 200


# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

class _AdminAllPlayers(Resource):
    """Get all DBS2 players - for admin panel"""
    
    def get(self):
        """GET /api/dbs2/admin/players"""
        try:
            sort_by = request.args.get('sort', 'crypto')
            
            # Use the model's built-in method
            players = DBS2Player.get_all_players()
            
            # Add minigames_completed format for each player
            for player in players:
                player['minigames_completed'] = {
                    'crypto_miner': player.get('completed_crypto_miner', False),
                    'infinite_user': player.get('completed_infinite_user', False),
                    'laundry': player.get('completed_laundry', False),
                    'ash_trail': player.get('completed_ash_trail', False),
                    'whackarat': player.get('completed_whackarat', False)
                }
            
            # Sort
            if sort_by == 'crypto':
                players.sort(key=lambda x: x.get('crypto', 0), reverse=True)
            elif sort_by == 'name':
                players.sort(key=lambda x: (x.get('user_info', {}).get('name') or '').lower())
            elif sort_by == 'updated':
                players.sort(key=lambda x: x.get('updated_at') or '', reverse=True)
            
            # Add rank
            for i, player in enumerate(players):
                player['rank'] = i + 1
            
            return {'players': players, 'total': len(players), 'sort': sort_by}, 200
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'error': str(e)}, 500


class _AdminPlayerDetail(Resource):
    """Get/Update specific player by UID"""
    
    def get(self, user_id):
        """GET /api/dbs2/admin/player/<user_id>"""
        try:
            # Find user by uid string
            user = User.query.filter_by(_uid=user_id).first()
            if not user:
                return {'error': f'User {user_id} not found'}, 404
            
            player = DBS2Player.get_by_user_id(user.id)
            if not player:
                return {'error': f'No DBS2 data for user {user_id}'}, 404
            
            result = player.read()
            result['minigames_completed'] = format_minigames(player)
            return result, 200
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'error': str(e)}, 500
    
    def put(self, user_id):
        """PUT /api/dbs2/admin/player/<user_id>"""
        try:
            user = User.query.filter_by(_uid=user_id).first()
            if not user:
                return {'error': f'User {user_id} not found'}, 404
            
            player = DBS2Player.get_by_user_id(user.id)
            if not player:
                return {'error': f'No DBS2 data for user {user_id}'}, 404
            
            data = request.get_json()
            
            # Handle reset
            if data.get('reset'):
                player._crypto = 0
                player._inventory = '[]'
                player._scores = '{}'
                player._completed_ash_trail = False
                player._completed_crypto_miner = False
                player._completed_whackarat = False
                player._completed_laundry = False
                player._completed_infinite_user = False
                player._completed_all = False
                db.session.commit()
                return {'message': f'Player {user_id} reset', 'crypto': 0}, 200
            
            # Handle crypto updates
            if 'crypto' in data:
                player._crypto = max(0, int(data['crypto']))
            elif 'add_crypto' in data:
                player._crypto = max(0, player._crypto + int(data['add_crypto']))
            
            # Handle inventory
            if 'inventory' in data:
                player.inventory = data['inventory']
            
            # Handle scores
            if 'scores' in data:
                player.scores = data['scores']
            
            # Handle minigame completions
            if 'completed_crypto_miner' in data:
                player._completed_crypto_miner = data['completed_crypto_miner']
            if 'completed_infinite_user' in data:
                player._completed_infinite_user = data['completed_infinite_user']
            if 'completed_laundry' in data:
                player._completed_laundry = data['completed_laundry']
            if 'completed_ash_trail' in data:
                player._completed_ash_trail = data['completed_ash_trail']
            if 'completed_whackarat' in data:
                player._completed_whackarat = data['completed_whackarat']
            
            # Update completed_all
            player._completed_all = (
                player._completed_ash_trail and
                player._completed_crypto_miner and
                player._completed_whackarat and
                player._completed_laundry and
                player._completed_infinite_user
            )
            
            db.session.commit()
            
            return {
                'message': f'Player {user_id} updated',
                'crypto': player._crypto
            }, 200
            
        except Exception as e:
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return {'error': str(e)}, 500


class _AdminStats(Resource):
    """Get overall game statistics"""
    
    def get(self):
        """GET /api/dbs2/admin/stats"""
        try:
            players = DBS2Player.query.all()
            
            total_players = len(players)
            total_crypto = sum(p._crypto for p in players)
            avg_crypto = total_crypto / total_players if total_players > 0 else 0
            
            # Count minigame completions
            minigame_counts = {
                'crypto_miner': sum(1 for p in players if p._completed_crypto_miner),
                'infinite_user': sum(1 for p in players if p._completed_infinite_user),
                'laundry': sum(1 for p in players if p._completed_laundry),
                'ash_trail': sum(1 for p in players if p._completed_ash_trail),
                'whackarat': sum(1 for p in players if p._completed_whackarat)
            }
            
            # Top players
            sorted_players = sorted(players, key=lambda p: p._crypto, reverse=True)[:5]
            top_players = []
            for p in sorted_players:
                if p.user:
                    top_players.append({
                        'uid': getattr(p.user, '_uid', 'unknown'),
                        'name': getattr(p.user, '_name', 'Unknown'),
                        'crypto': p._crypto
                    })
            
            return {
                'total_players': total_players,
                'total_crypto_in_circulation': total_crypto,
                'average_crypto': round(avg_crypto, 2),
                'minigame_completions': minigame_counts,
                'top_players': top_players
            }, 200
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'error': str(e)}, 500


class _AdminBulkUpdate(Resource):
    """Bulk operations on all players"""
    
    def post(self):
        """POST /api/dbs2/admin/bulk"""
        try:
            data = request.get_json()
            action = data.get('action')
            amount = data.get('amount', 0)
            
            if not action:
                return {'error': 'Action required'}, 400
            
            players = DBS2Player.query.all()
            affected = 0
            
            if action == 'add_crypto':
                for player in players:
                    player._crypto = max(0, player._crypto + int(amount))
                    affected += 1
            
            elif action == 'set_crypto':
                for player in players:
                    player._crypto = max(0, int(amount))
                    affected += 1
            
            elif action == 'reset_all':
                for player in players:
                    player._crypto = 0
                    player._inventory = '[]'
                    player._scores = '{}'
                    player._completed_ash_trail = False
                    player._completed_crypto_miner = False
                    player._completed_whackarat = False
                    player._completed_laundry = False
                    player._completed_infinite_user = False
                    player._completed_all = False
                    affected += 1
            
            else:
                return {'error': f'Unknown action: {action}'}, 400
            
            db.session.commit()
            
            return {'message': f'{action} completed', 'affected_players': affected}, 200
            
        except Exception as e:
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return {'error': str(e)}, 500


# ============================================================================
# SIMPLE ADMIN ENDPOINTS (Alternative - uses existing model methods)
# ============================================================================

class _AdminPlayersSimple(Resource):
    """Simpler admin endpoint using model's built-in methods"""
    
    def get(self):
        """GET /api/dbs2/players - Get all players"""
        try:
            players = DBS2Player.get_all_players()
            return {'players': players}, 200
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'error': str(e)}, 500


class _AdminPlayerSimple(Resource):
    """Get/update single player"""
    
    def get(self, uid):
        """GET /api/dbs2/player/<uid>"""
        try:
            user = User.query.filter_by(_uid=uid).first()
            if not user:
                return {'error': 'User not found'}, 404
            
            player = DBS2Player.get_by_user_id(user.id)
            if not player:
                return {'error': 'Player not found'}, 404
            
            return player.read(), 200
        except Exception as e:
            return {'error': str(e)}, 500
    
    def put(self, uid):
        """PUT /api/dbs2/player/<uid>"""
        try:
            user = User.query.filter_by(_uid=uid).first()
            if not user:
                return {'error': 'User not found'}, 404
            
            player = DBS2Player.get_by_user_id(user.id)
            if not player:
                return {'error': 'Player not found'}, 404
            
            data = request.get_json()
            player.update(data)
            return player.read(), 200
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500


# ============================================================================
# REGISTER ALL ROUTES
# ============================================================================

# Player endpoints (authenticated)
api.add_resource(_PlayerResource, '/player')
api.add_resource(_CryptoResource, '/crypto')
api.add_resource(_InventoryResource, '/inventory')
api.add_resource(_ScoresResource, '/scores')
api.add_resource(_MinigamesResource, '/minigames')

# Public endpoints
api.add_resource(_LeaderboardResource, '/leaderboard')
api.add_resource(_BitcoinBoostResource, '/bitcoin-boost')

# Admin endpoints (full featured)
api.add_resource(_AdminAllPlayers, '/admin/players')
api.add_resource(_AdminPlayerDetail, '/admin/player/<string:user_id>')
api.add_resource(_AdminStats, '/admin/stats')
api.add_resource(_AdminBulkUpdate, '/admin/bulk')

# Simple admin endpoints (uses model methods directly)
api.add_resource(_AdminPlayersSimple, '/players')
api.add_resource(_AdminPlayerSimple, '/player/<string:uid>')