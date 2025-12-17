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
from model.ashtrail_run import AshTrailRun
from model.ashtrail_run import AshTrailRun
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


class _MinigameLeaderboardResource(Resource):
    """
    Public minigame leaderboard.

    GET /api/dbs2/leaderboard/minigame?game=ash_trail&limit=10

    Returns:
      {
        "game": "ash_trail",
        "leaderboard": [
          { "rank": 1, "score": 97, "user_info": { "uid": "...", "name": "..." } }
        ]
      }
    """

    def get(self):
        game = (request.args.get('game') or '').strip()
        if not game:
            return {'error': 'game query param required'}, 400

        limit = min(int(request.args.get('limit', 10)), 100)

        # Use existing model read() output which already includes user_info + scores
        players = DBS2Player.get_all_players()

        # If this is an Ash Trail per-book score key, also attach a ghost `run_id` when available.
        # game keys look like: ash_trail_defi_grimoire
        ash_book_id = None
        if game.startswith('ash_trail_'):
            candidate = game.replace('ash_trail_', '', 1)
            if candidate in {'defi_grimoire', 'lost_ledger', 'proof_of_burn'}:
                ash_book_id = candidate

        # If this is an Ash Trail per-book score key, also attach a ghost `run_id` when available.
        # game keys look like: ash_trail_defi_grimoire
        ash_book_id = None
        if game.startswith('ash_trail_'):
            candidate = game.replace('ash_trail_', '', 1)
            if candidate in {'defi_grimoire', 'lost_ledger', 'proof_of_burn'}:
                ash_book_id = candidate

        scored = []
        for p in players:
            scores = p.get('scores') or {}
            raw_score = scores.get(game, None)
            if raw_score is None:
                continue
            try:
                score = float(raw_score)
            except Exception:
                continue
            scored.append({
                'user_info': p.get('user_info', {}),
                'score': score
            })

        scored.sort(key=lambda x: x.get('score', 0), reverse=True)
        scored = scored[:limit]

        # Preload best run ids for these users (only for Ash Trail books).
        run_id_by_uid = {}
        if ash_book_id and scored:
            uids = [e.get('user_info', {}).get('uid') for e in scored if e.get('user_info', {}).get('uid')]
            if uids:
                users = User.query.filter(User._uid.in_(uids)).all()
                uid_to_userid = {u._uid: u.id for u in users if getattr(u, '_uid', None)}
                user_ids = list(uid_to_userid.values())
                if user_ids:
                    runs = (
                        AshTrailRun.query
                        .filter(AshTrailRun.book_id == ash_book_id)
                        .filter(AshTrailRun.user_id.in_(user_ids))
                        .order_by(AshTrailRun.user_id.asc(), AshTrailRun.score.desc(), AshTrailRun.created_at.desc())
                        .all()
                    )
                    best_by_user = {}
                    for r in runs:
                        if r.user_id not in best_by_user:
                            best_by_user[r.user_id] = r.id
                    # invert back to uid for frontend payload
                    for uid, user_id in uid_to_userid.items():
                        if user_id in best_by_user:
                            run_id_by_uid[uid] = best_by_user[user_id]

        # Preload best run ids for these users (only for Ash Trail books).
        run_id_by_uid = {}
        if ash_book_id and scored:
            uids = [e.get('user_info', {}).get('uid') for e in scored if e.get('user_info', {}).get('uid')]
            if uids:
                users = User.query.filter(User._uid.in_(uids)).all()
                uid_to_userid = {u._uid: u.id for u in users if getattr(u, '_uid', None)}
                user_ids = list(uid_to_userid.values())
                if user_ids:
                    runs = (
                        AshTrailRun.query
                        .filter(AshTrailRun.book_id == ash_book_id)
                        .filter(AshTrailRun.user_id.in_(user_ids))
                        .order_by(AshTrailRun.user_id.asc(), AshTrailRun.score.desc(), AshTrailRun.created_at.desc())
                        .all()
                    )
                    best_by_user = {}
                    for r in runs:
                        if r.user_id not in best_by_user:
                            best_by_user[r.user_id] = r.id
                    # invert back to uid for frontend payload
                    for uid, user_id in uid_to_userid.items():
                        if user_id in best_by_user:
                            run_id_by_uid[uid] = best_by_user[user_id]

        leaderboard = []
        for idx, entry in enumerate(scored):
            uid = (entry.get('user_info') or {}).get('uid')
            uid = (entry.get('user_info') or {}).get('uid')
            leaderboard.append({
                'rank': idx + 1,
                'score': entry.get('score', 0),
                'user_info': entry.get('user_info', {}),
                'run_id': run_id_by_uid.get(uid) if uid else None
                'user_info': entry.get('user_info', {}),
                'run_id': run_id_by_uid.get(uid) if uid else None
            })

        return {'game': game, 'leaderboard': leaderboard}, 200


class _AshTrailRunsResource(Resource):
    """
    Ash Trail ghost runs (replay traces) for a specific book.

    POST /api/dbs2/ash-trail/runs
      body: { book_id: "defi_grimoire", score: 72, trace: [{x,y}, ...] }

    GET /api/dbs2/ash-trail/runs?book_id=defi_grimoire&limit=10
      returns top runs by score for that book (no trace)
    """

    @token_required()
    def post(self):
        player = get_current_player()
        if not player:
            return {'error': 'Not authenticated'}, 401

        data = request.get_json() or {}
        book_id = (data.get('book_id') or '').strip()
        score = data.get('score', 0)
        trace = data.get('trace', [])

        allowed = {'defi_grimoire', 'lost_ledger', 'proof_of_burn'}
        if book_id not in allowed:
            return {'error': 'Invalid book_id'}, 400

        try:
            score_f = float(score)
        except Exception:
            score_f = 0.0
        score_f = max(0.0, min(100.0, score_f))

        # Minimal validation + size cap (prevent huge payloads)
        if not isinstance(trace, list):
            return {'error': 'trace must be a list'}, 400
        if len(trace) > 2500:
            trace = trace[:2500]

        # Store the run
        run = AshTrailRun(user_id=g.current_user.id, book_id=book_id, score=score_f)
        run.trace = trace
        db.session.add(run)
        db.session.commit()

        return {'run': run.read(include_trace=False)}, 201

    def get(self):
        book_id = (request.args.get('book_id') or '').strip()
        allowed = {'defi_grimoire', 'lost_ledger', 'proof_of_burn'}
        if book_id not in allowed:
            return {'error': 'book_id query param required (defi_grimoire|lost_ledger|proof_of_burn)'}, 400

        limit = min(int(request.args.get('limit', 10)), 50)

        runs = (
            AshTrailRun.query
            .filter_by(book_id=book_id)
            .order_by(AshTrailRun.score.desc(), AshTrailRun.created_at.desc())
            .limit(limit)
            .all()
        )

        return {'book_id': book_id, 'runs': [r.read(include_trace=False) for r in runs]}, 200


class _AshTrailRunDetailResource(Resource):
    """
    GET /api/dbs2/ash-trail/runs/<id>
      returns run + trace for replay
    """

    def get(self, run_id: int):
        run = AshTrailRun.query.get(run_id)
        if not run:
            return {'error': 'Run not found'}, 404
        return {'run': run.read(include_trace=True)}, 200


class _AshTrailAIResource(Resource):
    """
    Simple backend-generated (AI-like) narrative for Ash Trail.

    POST /api/dbs2/ash-trail/ai
      body: { book_id: "defi_grimoire", score: 72, trail_stats: {...} }

    Returns:
      {
        "tone": "error|warn|good|great",
        "speaker": "IShowGreen",
        "dialogue": "...",
        "page_title": "...",
        "page_text": "..."
      }
    """

    def post(self):
        data = request.get_json() or {}
        book_id = (data.get('book_id') or '').strip()
        score = data.get('score', 0)
        try:
            s = float(score)
        except Exception:
            s = 0.0
        s = max(0.0, min(100.0, s))

        books = {
            'defi_grimoire': {
                'title': 'DeFi Grimoire',
                'topic': 'decentralized finance',
                'keywords': ['liquidity', 'swap', 'pool', 'yield', 'gas', 'vault', 'oracle'],
            },
            'lost_ledger': {
                'title': 'Lost Ledger',
                'topic': 'accounting the chain',
                'keywords': ['blocks', 'entries', 'balance', 'hash', 'confirmations', 'ledger'],
            },
            'proof_of_burn': {
                'title': 'Proof-of-Burn Almanac',
                'topic': 'proof-of-burn',
                'keywords': ['burn', 'supply', 'address', 'scarcity', 'verification', 'signal'],
            },
        }
        meta = books.get(book_id) or {'title': 'Burnt Book', 'topic': 'memory', 'keywords': ['ash', 'ink', 'pages']}

        # Score bands: <40 nonsense, 40-60 partial, 60-80 mostly coherent, 80-100 clean
        if s < 40:
            tone = 'error'
            dialogue = (
                'IShowGreen squints: "This reads like a toaster arguing with a spreadsheet. '
                'You brought me ash, not information."'
            )
            page_title = f"{meta['title']} — Fragment (Corrupted)"
            page_text = (
                "…liquidity = bananas??\n"
                "swap the *stairs* into a pool\n"
                "gas fee: paid in whispers\n"
                "NOTE: DO NOT ORACLE THE SPOON\n"
                "…end of page (burnt through)"
            )
        elif s < 60:
            tone = 'warn'
            dialogue = (
                'IShowGreen mutters: "Some of this is real… and some of it is smoke. '
                'You’re close, but details are missing."'
            )
            page_title = f"{meta['title']} — Partial Recovery"
            page_text = (
                f"The page mentions {meta['topic']} and a {meta['keywords'][0]} pool,\n"
                f"but the steps jump around and the {meta['keywords'][1]} rule is incomplete.\n"
                "Several lines are smeared into black dust."
            )
        elif s < 80:
            tone = 'good'
            dialogue = (
                'IShowGreen nods: "This mostly tracks. A few gaps, but I can reconstruct the rest. '
                'Run it again if you want it perfect."'
            )
            page_title = f"{meta['title']} — Mostly Restored"
            page_text = (
                f"Key idea: {meta['topic']} works when participants provide {meta['keywords'][0]}.\n"
                f"Rule of thumb: verify inputs (watch the {meta['keywords'][5] if len(meta['keywords'])>5 else meta['keywords'][2]}),\n"
                "then execute the swap/step sequence in order.\n"
                "One margin note is still burnt."
            )
        else:
            tone = 'great'
            dialogue = (
                'IShowGreen smiles: "Perfect. Clean sequence, clean logic. '
                'I can finally read this without guessing."'
            )
            page_title = f"{meta['title']} — Fully Restored"
            page_text = (
                f"Recovered summary of {meta['topic']}:\n"
                f"- Provide {meta['keywords'][0]} to a pool\n"
                f"- Validate via {meta['keywords'][6] if len(meta['keywords'])>6 else meta['keywords'][2]}\n"
                f"- Execute swap with predictable {meta['keywords'][4] if len(meta['keywords'])>4 else 'fees'}\n"
                "- Record results and verify confirmations\n"
                "\nNo burn marks remain on this page."
            )

        return {
            'tone': tone,
            'speaker': 'IShowGreen',
            'dialogue': dialogue,
            'page_title': page_title,
            'page_text': page_text,
        }, 200

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
api.add_resource(_MinigameLeaderboardResource, '/leaderboard/minigame')
api.add_resource(_AshTrailRunsResource, '/ash-trail/runs')
api.add_resource(_AshTrailRunDetailResource, '/ash-trail/runs/<int:run_id>')
api.add_resource(_AshTrailAIResource, '/ash-trail/ai')
api.add_resource(_BitcoinBoostResource, '/bitcoin-boost')

# Admin endpoints (full featured)
api.add_resource(_AdminAllPlayers, '/admin/players')
api.add_resource(_AdminPlayerDetail, '/admin/player/<string:user_id>')
api.add_resource(_AdminStats, '/admin/stats')
api.add_resource(_AdminBulkUpdate, '/admin/bulk')

# Simple admin endpoints (uses model methods directly)
api.add_resource(_AdminPlayersSimple, '/players')
api.add_resource(_AdminPlayerSimple, '/player/<string:uid>')