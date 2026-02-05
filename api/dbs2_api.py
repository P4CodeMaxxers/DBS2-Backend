"""
DBS2 Game API - Complete Backend with Wallet Support and Scrap Ownership
Place this in: api/dbs2_api.py

Works with the DBS2Player model structure that has:
- user_id (not _uid)
- Individual _completed_* fields (not _minigames_completed dict)
- Individual _scrap_* fields for code scrap ownership (purchased from shop)
- Multi-coin wallet (_wallet_btc, _wallet_eth, _wallet_sol, _wallet_ada, _wallet_doge)
- read(), get_all_players(), get_leaderboard() methods
"""

from flask import Blueprint, request, g
from flask_restful import Api, Resource
from datetime import datetime, timedelta
import requests
import json

# Import your models and decorators
from model.dbs2_player import DBS2Player, migrate_dbs2_players_add_scrap_columns
from model.user import User
from model.ashtrail_run import AshTrailRun
from __init__ import db
from api.jwt_authorize import token_required

# Create Blueprint
dbs2_api = Blueprint('dbs2_api', __name__, url_prefix='/api/dbs2')
api = Api(dbs2_api)


# ============================================================================
# COIN CONFIGURATION
# ============================================================================

SUPPORTED_COINS = {
    'satoshis': {
        'symbol': 'SATS',
        'name': 'Satoshis',
        'coingecko_id': None,
        'decimals': 0,
        'field': '_crypto'
    },
    'bitcoin': {
        'symbol': 'BTC',
        'name': 'Bitcoin',
        'coingecko_id': 'bitcoin',
        'decimals': 8,
        'field': '_wallet_btc'
    },
    'ethereum': {
        'symbol': 'ETH',
        'name': 'Ethereum',
        'coingecko_id': 'ethereum',
        'decimals': 6,
        'field': '_wallet_eth'
    },
    'solana': {
        'symbol': 'SOL',
        'name': 'Solana',
        'coingecko_id': 'solana',
        'decimals': 4,
        'field': '_wallet_sol'
    },
    'cardano': {
        'symbol': 'ADA',
        'name': 'Cardano',
        'coingecko_id': 'cardano',
        'decimals': 2,
        'field': '_wallet_ada'
    },
    'dogecoin': {
        'symbol': 'DOGE',
        'name': 'Dogecoin',
        'coingecko_id': 'dogecoin',
        'decimals': 2,
        'field': '_wallet_doge'
    }
}

# Minigame to coin mapping
MINIGAME_COINS = {
    'crypto_miner': 'satoshis',
    'whackarat': 'dogecoin',
    'laundry': 'cardano',
    'ash_trail': 'solana',
    'infinite_user': 'ethereum'
}

# Price cache
_price_cache = {
    'prices': {},
    'last_fetch': None,
    'cache_duration': timedelta(minutes=2)
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def ensure_dbs2_tables():
    """Create dbs2_players table if missing; add scrap columns if table exists with old schema."""
    try:
        DBS2Player.query.limit(1).first()
    except Exception as e:
        err_msg = str(e).lower()
        if 'no such table' in err_msg:
            try:
                db.create_all()
            except Exception as create_err:
                print('[DBS2] ensure_dbs2_tables: create_all failed:', create_err)
        elif 'no such column' in err_msg:
            migrate_dbs2_players_add_scrap_columns()
        else:
            try:
                db.create_all()
                migrate_dbs2_players_add_scrap_columns()
            except Exception as create_err:
                print('[DBS2] ensure_dbs2_tables failed:', create_err)


def ensure_ashtrail_tables():
    """Create ashtrail_runs table if missing (needed for Ash Trail ghost replays)."""
    try:
        AshTrailRun.query.limit(1).first()
    except Exception as e:
        err_msg = str(e).lower()
        if 'no such table' in err_msg or 'ashtrail' in err_msg:
            try:
                db.create_all()
                print('[DBS2] Created ashtrail_runs table')
            except Exception as create_err:
                print('[DBS2] ensure_ashtrail_tables: create_all failed:', create_err)


def get_current_player():
    """Get DBS2Player for current authenticated user, create if doesn't exist.
    If table is missing, create_all() and retry once.
    """
    if not g.current_user:
        return None
    try:
        return DBS2Player.get_or_create(g.current_user.id)
    except Exception:
        try:
            db.create_all()
            return DBS2Player.get_or_create(g.current_user.id)
        except Exception:
            raise


def format_minigames(player):
    """Convert individual completion fields to dict format for API response (getattr for missing columns)"""
    return {
        'crypto_miner': getattr(player, '_completed_crypto_miner', False),
        'infinite_user': getattr(player, '_completed_infinite_user', False),
        'laundry': getattr(player, '_completed_laundry', False),
        'ash_trail': getattr(player, '_completed_ash_trail', False),
        'whackarat': getattr(player, '_completed_whackarat', False)
    }


def format_scraps_owned(player):
    """Convert individual scrap ownership fields to dict format for API response"""
    return {
        'crypto_miner': getattr(player, '_scrap_crypto_miner', False) or False,
        'whackarat': getattr(player, '_scrap_whackarat', False) or False,
        'laundry': getattr(player, '_scrap_laundry', False) or False,
        'ash_trail': getattr(player, '_scrap_ash_trail', False) or False,
        'infinite_user': getattr(player, '_scrap_infinite_user', False) or False
    }


def fetch_coin_prices():
    """Fetch current prices from CoinGecko with caching"""
    now = datetime.now()
    
    # Return cached if valid
    if (_price_cache['last_fetch'] and 
        now - _price_cache['last_fetch'] < _price_cache['cache_duration'] and
        _price_cache['prices']):
        return _price_cache['prices']
    
    # Build list of coingecko IDs
    coin_ids = [c['coingecko_id'] for c in SUPPORTED_COINS.values() if c['coingecko_id']]
    
    try:
        url = 'https://api.coingecko.com/api/v3/simple/price'
        params = {
            'ids': ','.join(coin_ids),
            'vs_currencies': 'usd',
            'include_24hr_change': 'true'
        }
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            prices = {}
            
            for coin_id, info in SUPPORTED_COINS.items():
                cg_id = info['coingecko_id']
                if cg_id and cg_id in data:
                    prices[coin_id] = {
                        'usd': data[cg_id].get('usd', 0),
                        'change_24h': data[cg_id].get('usd_24h_change', 0)
                    }
                elif coin_id == 'satoshis':
                    # Satoshis = 1/100,000,000 of Bitcoin
                    btc_price = data.get('bitcoin', {}).get('usd', 0)
                    prices['satoshis'] = {
                        'usd': btc_price / 100_000_000,
                        'change_24h': data.get('bitcoin', {}).get('usd_24h_change', 0)
                    }
            
            _price_cache['prices'] = prices
            _price_cache['last_fetch'] = now
            return prices
            
    except Exception as e:
        print(f'[DBS2] Price fetch error: {e}')
    
    # Return cached or empty
    return _price_cache['prices'] or {}


def calculate_sats_per_coin(coin_id, prices):
    """Calculate how many satoshis one unit of a coin is worth"""
    if coin_id == 'satoshis':
        return 1
    if coin_id == 'bitcoin':
        return 100_000_000
    
    btc_price = prices.get('bitcoin', {}).get('usd', 1)
    coin_price = prices.get(coin_id, {}).get('usd', 0)
    
    if btc_price <= 0 or coin_price <= 0:
        return 0
    
    return int((coin_price / btc_price) * 100_000_000)


# ============================================================================
# PLAYER ENDPOINTS (Authenticated)
# ============================================================================

class _PlayerResource(Resource):
    """Get/Update current player's data"""
    
    @token_required()
    def get(self):
        """GET /api/dbs2/player - Get current player's full data"""
        try:
            player = get_current_player()
            if not player:
                return {'error': 'Not authenticated'}, 401
            return player.read(), 200
        except Exception as e:
            return {'error': 'Player fetch failed', 'message': str(e)}, 500
    
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
    """Manage player's crypto currency (satoshis)"""
    
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
        return {'crypto': player._crypto, 'wallet': player.wallet}, 200


# ============================================================================
# WALLET ENDPOINTS (Authenticated)
# ============================================================================

class _WalletResource(Resource):
    """Manage player's multi-coin wallet"""
    
    @token_required()
    def get(self):
        """GET /api/dbs2/wallet - Get full wallet"""
        player = get_current_player()
        if not player:
            return {'error': 'Not authenticated'}, 401
        
        prices = fetch_coin_prices()
        wallet = player.wallet
        
        # Calculate USD values
        wallet_with_usd = {}
        total_usd = 0
        
        for coin_id, balance in wallet.items():
            price_info = prices.get(coin_id, {})
            usd_value = balance * price_info.get('usd', 0)
            total_usd += usd_value
            
            wallet_with_usd[coin_id] = {
                'balance': balance,
                'usd_value': round(usd_value, 2),
                'price_usd': price_info.get('usd', 0),
                'change_24h': price_info.get('change_24h', 0)
            }
        
        return {
            'wallet': wallet_with_usd,
            'total_usd': round(total_usd, 2),
            'raw_balances': wallet
        }, 200
    
    @token_required()
    def put(self):
        """PUT /api/dbs2/wallet - Add to wallet balances"""
        player = get_current_player()
        if not player:
            return {'error': 'Not authenticated'}, 401
        
        data = request.get_json()
        
        # Handle 'add' format: {add: {satoshis: 100, dogecoin: 5}}
        if 'add' in data:
            for coin_id, amount in data['add'].items():
                if coin_id in SUPPORTED_COINS:
                    player.add_to_wallet(coin_id, amount)
        
        # Handle direct format: {satoshis: 100, dogecoin: 5}
        else:
            for coin_id, amount in data.items():
                if coin_id in SUPPORTED_COINS:
                    player.add_to_wallet(coin_id, amount)
        
        return {'wallet': player.wallet}, 200


class _WalletAddCoinResource(Resource):
    """Add specific coin to wallet"""
    
    @token_required()
    def post(self):
        """POST /api/dbs2/wallet/add - Add coin to wallet"""
        player = get_current_player()
        if not player:
            return {'error': 'Not authenticated'}, 401
        
        data = request.get_json()
        coin_id = data.get('coin', 'satoshis')
        amount = data.get('amount', 0)
        
        if coin_id not in SUPPORTED_COINS:
            return {'error': f'Unknown coin: {coin_id}'}, 400
        
        if amount <= 0:
            return {'error': 'Amount must be positive'}, 400
        
        player.add_to_wallet(coin_id, amount)
        
        return {
            'success': True,
            'coin': coin_id,
            'added': amount,
            'wallet': player.wallet
        }, 200


class _WalletConvertResource(Resource):
    """Convert between coins (5% fee)"""
    
    @token_required()
    def post(self):
        """POST /api/dbs2/wallet/convert - Convert coin to satoshis"""
        player = get_current_player()
        if not player:
            return {'error': 'Not authenticated'}, 401
        
        data = request.get_json()
        from_coin = data.get('from_coin') or data.get('coin')
        to_coin = data.get('to_coin', 'satoshis')
        amount = float(data.get('amount', 0))
        
        if from_coin not in SUPPORTED_COINS:
            return {'error': f'Unknown source coin: {from_coin}'}, 400
        if to_coin not in SUPPORTED_COINS:
            return {'error': f'Unknown target coin: {to_coin}'}, 400
        if from_coin == to_coin:
            return {'error': 'Cannot convert to same coin'}, 400
        
        # Check balance
        wallet = player.wallet
        current_balance = wallet.get(from_coin, 0)
        
        if amount <= 0:
            return {'error': 'Amount must be positive'}, 400
        if amount > current_balance:
            return {'error': 'Insufficient balance'}, 400
        
        # Get prices and calculate conversion
        prices = fetch_coin_prices()
        from_sats = calculate_sats_per_coin(from_coin, prices)
        to_sats = calculate_sats_per_coin(to_coin, prices)
        
        if from_sats <= 0 or to_sats <= 0:
            return {'error': 'Cannot determine conversion rate'}, 400
        
        # Calculate: amount * from_rate / to_rate * (1 - fee)
        sats_value = amount * from_sats
        fee_rate = 0.05  # 5% fee
        sats_after_fee = sats_value * (1 - fee_rate)
        
        if to_coin == 'satoshis':
            received = int(sats_after_fee)
        else:
            received = sats_after_fee / to_sats
            # Round to coin's decimal places
            decimals = SUPPORTED_COINS[to_coin]['decimals']
            received = round(received, decimals)
        
        # Execute conversion
        player.add_to_wallet(from_coin, -amount)
        player.add_to_wallet(to_coin, received)
        
        return {
            'success': True,
            'from_coin': from_coin,
            'from_amount': amount,
            'to_coin': to_coin,
            'to_amount': received,
            'fee_percent': fee_rate * 100,
            'wallet': player.wallet
        }, 200


# ============================================================================
# PRICE ENDPOINTS (Public)
# ============================================================================

class _PricesResource(Resource):
    """Get current coin prices"""
    
    def get(self):
        """GET /api/dbs2/prices - Get all coin prices"""
        prices = fetch_coin_prices()
        
        result = {}
        for coin_id, info in SUPPORTED_COINS.items():
            price_data = prices.get(coin_id, {})
            result[coin_id] = {
                'symbol': info['symbol'],
                'name': info['name'],
                'price_usd': price_data.get('usd', 0),
                'change_24h': price_data.get('change_24h', 0),
                'sats_per_unit': calculate_sats_per_coin(coin_id, prices)
            }
        
        return {'prices': result}, 200


class _BitcoinBoostResource(Resource):
    """Get Bitcoin-based reward multiplier"""
    
    def get(self):
        """GET /api/dbs2/bitcoin-boost - Get boost multiplier based on BTC price"""
        prices = fetch_coin_prices()
        btc_data = prices.get('bitcoin', {})
        
        change_24h = btc_data.get('change_24h', 0)
        
        # Boost calculation: 1.0 base + 0.01 per percent change (capped)
        boost = 1.0 + (change_24h * 0.01)
        boost = max(0.5, min(2.0, boost))  # Cap between 0.5x and 2x
        
        return {
            'boost_multiplier': round(boost, 2),
            'btc_price_usd': btc_data.get('usd', 0),
            'btc_change_24h': round(change_24h, 2),
            'message': f'BTC {"up" if change_24h >= 0 else "down"} {abs(change_24h):.1f}% - {boost:.2f}x rewards'
        }, 200


# ============================================================================
# INVENTORY ENDPOINTS
# ============================================================================

class _InventoryResource(Resource):
    """Manage player's inventory"""
    
    @token_required()
    def get(self):
        """GET /api/dbs2/inventory"""
        try:
            player = get_current_player()
            if not player:
                return {'error': 'Not authenticated'}, 401
            return {'inventory': player.inventory}, 200
        except Exception as e:
            return {'error': 'Inventory fetch failed', 'message': str(e)}, 500
    
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


# ============================================================================
# SCORES ENDPOINTS
# ============================================================================

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

    @token_required()
    def post(self):
        """POST /api/dbs2/scores - Update score for a game (same as PUT; frontend uses POST)"""
        return self.put()


# ============================================================================
# MINIGAMES ENDPOINTS
# ============================================================================

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


class _MinigameCompleteResource(Resource):
    """Mark a single minigame as complete (POST body: { minigame: 'ash_trail' })"""

    @token_required()
    def post(self):
        """POST /api/dbs2/minigames/complete - Mark one minigame complete"""
        player = get_current_player()
        if not player:
            return {'error': 'Not authenticated'}, 401

        data = request.get_json() or {}
        minigame = (data.get('minigame') or '').strip()

        field_map = {
            'crypto_miner': 'completed_crypto_miner',
            'infinite_user': 'completed_infinite_user',
            'laundry': 'completed_laundry',
            'ash_trail': 'completed_ash_trail',
            'whackarat': 'completed_whackarat'
        }

        if minigame not in field_map:
            return {'error': 'Invalid or missing minigame name'}, 400

        player.update({field_map[minigame]: True})
        return {'minigames_completed': format_minigames(player), 'success': True}, 200


class _MinigameRewardResource(Resource):
    """Reward player for minigame completion with appropriate coin"""
    
    @token_required()
    def post(self):
        """POST /api/dbs2/minigame/reward - Award coin for minigame"""
        player = get_current_player()
        if not player:
            return {'error': 'Not authenticated'}, 401
        
        data = request.get_json()
        minigame = data.get('minigame')
        amount = data.get('amount', 0)
        
        if not minigame:
            return {'error': 'Minigame name required'}, 400
        
        # Get the coin for this minigame
        coin_id = MINIGAME_COINS.get(minigame, 'satoshis')
        
        if amount > 0:
            player.add_to_wallet(coin_id, amount)
        
        return {
            'success': True,
            'minigame': minigame,
            'coin': coin_id,
            'amount': amount,
            'wallet': player.wallet
        }, 200


# ============================================================================
# LEADERBOARD ENDPOINTS (Public)
# ============================================================================

def _safe_limit(default=10, max_val=100):
    """Parse limit from request args without raising."""
    try:
        raw = request.args.get('limit', default)
        n = int(raw) if raw not in (None, '') else default
        return max(1, min(n, max_val))
    except (ValueError, TypeError):
        return default


class _LeaderboardResource(Resource):
    """Public leaderboard"""
    
    def get(self):
        """GET /api/dbs2/leaderboard?limit=10"""
        try:
            ensure_dbs2_tables()
            limit = _safe_limit(10, 100)
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
        except Exception as e:
            import traceback
            traceback.print_exc()
            print('[DBS2] Leaderboard failed:', e)
            return {'leaderboard': []}, 200


class _MinigameLeaderboardResource(Resource):
    """Leaderboard for specific minigame scores"""
    
    def get(self):
        """GET /api/dbs2/leaderboard/minigame?game=ash_trail&limit=10"""
        try:
            ensure_dbs2_tables()
            game = (request.args.get('game') or '').strip()
            limit = _safe_limit(10, 100)
            if not game:
                return {'error': 'Game parameter required'}, 400
            
            players = DBS2Player.query.all()
            entries = []
            for player in players:
                try:
                    scores = player.scores
                except Exception:
                    scores = {}
                if game in scores:
                    user_info = {}
                    if player.user:
                        user_info = {
                            'uid': getattr(player.user, '_uid', None),
                            'name': getattr(player.user, '_name', None)
                        }
                    try:
                        score_val = scores[game]
                        if not isinstance(score_val, (int, float)):
                            score_val = float(score_val) if score_val is not None else 0
                    except (TypeError, ValueError):
                        score_val = 0
                    entries.append({
                        'user_info': user_info,
                        'score': score_val,
                        'game': game
                    })
            entries.sort(key=lambda x: x['score'], reverse=True)
            for i, entry in enumerate(entries[:limit]):
                entry['rank'] = i + 1
            return {'leaderboard': entries[:limit], 'game': game}, 200
        except Exception as e:
            import traceback
            traceback.print_exc()
            print('[DBS2] Minigame leaderboard failed:', e)
            return {'leaderboard': [], 'game': game or 'unknown'}, 200


# ============================================================================
# ASH TRAIL ENDPOINTS
# ============================================================================

class _AshTrailRunsResource(Resource):
    """Ash Trail run management"""
    
    def get(self):
        """GET /api/dbs2/ash-trail/runs?book_id=defi_grimoire&limit=10"""
        ensure_ashtrail_tables()
        book_id = request.args.get('book_id', '')
        try:
            limit = min(int(request.args.get('limit', 10) or 10), 50)
        except (ValueError, TypeError):
            limit = 10
        
        query = AshTrailRun.query
        if book_id:
            query = query.filter_by(book_id=book_id)
        
        runs = query.order_by(AshTrailRun.score.desc()).limit(limit).all()
        
        return {
            'book_id': book_id,
            'runs': [r.read(include_trace=False) for r in runs]
        }, 200
    
    @token_required()
    def post(self):
        """POST /api/dbs2/ash-trail/runs - Submit a run"""
        ensure_ashtrail_tables()
        player = get_current_player()
        if not player:
            return {'error': 'Not authenticated', 'message': 'Please log in to save your Ash Trail run'}, 401
        
        data = request.get_json()
        book_id = data.get('book_id', '')
        score = float(data.get('score', 0))
        trace = data.get('trace', [])
        
        if not book_id:
            return {'error': 'book_id required'}, 400
        
        run = AshTrailRun(
            user_id=g.current_user.id,
            book_id=book_id,
            score=score
        )
        run.trace = trace
        
        db.session.add(run)
        db.session.commit()
        
        return {'success': True, 'run': run.read(include_trace=True)}, 201


class _AshTrailRunDetailResource(Resource):
    """Get specific Ash Trail run with trace"""
    
    def get(self, run_id):
        """GET /api/dbs2/ash-trail/runs/<run_id>"""
        ensure_ashtrail_tables()
        run = AshTrailRun.query.get(run_id)
        if not run:
            return {'error': 'Run not found'}, 404
        
        return {'run': run.read(include_trace=True)}, 200


class _AshTrailAIResource(Resource):
    """AI endpoint for Ash Trail (placeholder)"""
    
    @token_required()
    def post(self):
        """POST /api/dbs2/ash-trail/ai"""
        return {'message': 'AI analysis not implemented'}, 501


# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

class _AdminAllPlayers(Resource):
    """Get all players for admin panel"""
    
    def get(self):
        """GET /api/dbs2/admin/players"""
        try:
            ensure_dbs2_tables()
            players = DBS2Player.query.all()
            result = []
            for player in players:
                try:
                    data = player.read()
                    data['minigames_completed'] = format_minigames(player)
                    data['scraps_owned'] = format_scraps_owned(player)
                    result.append(data)
                except Exception as row_err:
                    print('[DBS2] admin/players row error:', row_err)
                    continue
            result.sort(key=lambda x: x.get('crypto', 0), reverse=True)
            return {'players': result, 'count': len(result)}, 200
        except Exception as e:
            import traceback
            traceback.print_exc()
            print('[DBS2] admin/players failed:', e)
            return {'players': [], 'count': 0}, 200


class _AdminPlayerDetail(Resource):
    """Admin manage single player"""
    
    def get(self, user_id):
        """GET /api/dbs2/admin/player/<user_id>"""
        try:
            # Try to find by uid first
            user = User.query.filter_by(_uid=user_id).first()
            if not user:
                # Try numeric ID
                try:
                    user = User.query.get(int(user_id))
                except:
                    pass
            
            if not user:
                return {'error': 'User not found'}, 404
            
            player = DBS2Player.get_by_user_id(user.id)
            if not player:
                return {'error': 'Player not found'}, 404
            
            data = player.read()
            data['minigames_completed'] = format_minigames(player)
            data['scraps_owned'] = format_scraps_owned(player)
            return data, 200
            
        except Exception as e:
            return {'error': str(e)}, 500
    
    def put(self, user_id):
        """PUT /api/dbs2/admin/player/<user_id>"""
        try:
            user = User.query.filter_by(_uid=user_id).first()
            if not user:
                try:
                    user = User.query.get(int(user_id))
                except:
                    pass
            
            if not user:
                return {'error': 'User not found'}, 404
            
            player = DBS2Player.get_by_user_id(user.id)
            if not player:
                return {'error': 'Player not found'}, 404
            
            data = request.get_json() or {}
            
            # Handle crypto/satoshis
            if 'crypto' in data:
                player._crypto = max(0, int(data['crypto']))
            if 'add_crypto' in data:
                player._crypto = max(0, player._crypto + int(data['add_crypto']))
            
            # Handle wallet coins
            if 'wallet_btc' in data:
                player._wallet_btc = max(0.0, float(data['wallet_btc']))
            if 'wallet_eth' in data:
                player._wallet_eth = max(0.0, float(data['wallet_eth']))
            if 'wallet_sol' in data:
                player._wallet_sol = max(0.0, float(data['wallet_sol']))
            if 'wallet_ada' in data:
                player._wallet_ada = max(0.0, float(data['wallet_ada']))
            if 'wallet_doge' in data:
                player._wallet_doge = max(0.0, float(data['wallet_doge']))
            
            # Handle inventory (store as JSON string or list)
            if 'inventory' in data:
                inv = data['inventory']
                if isinstance(inv, list):
                    player._inventory = json.dumps(inv)
                else:
                    player._inventory = inv
            
            # Handle scores (store as JSON string or dict)
            if 'scores' in data:
                scores = data['scores']
                if isinstance(scores, dict):
                    player._scores = json.dumps(scores)
                else:
                    player._scores = scores
            
            # Handle minigame completions
            if 'completed_crypto_miner' in data:
                player._completed_crypto_miner = bool(data['completed_crypto_miner'])
            if 'completed_infinite_user' in data:
                player._completed_infinite_user = bool(data['completed_infinite_user'])
            if 'completed_laundry' in data:
                player._completed_laundry = bool(data['completed_laundry'])
            if 'completed_ash_trail' in data:
                player._completed_ash_trail = bool(data['completed_ash_trail'])
            if 'completed_whackarat' in data:
                player._completed_whackarat = bool(data['completed_whackarat'])
            
            # Handle scrap ownership (NEW)
            if 'scrap_crypto_miner' in data:
                player._scrap_crypto_miner = bool(data['scrap_crypto_miner'])
            if 'scrap_whackarat' in data:
                player._scrap_whackarat = bool(data['scrap_whackarat'])
            if 'scrap_laundry' in data:
                player._scrap_laundry = bool(data['scrap_laundry'])
            if 'scrap_ash_trail' in data:
                player._scrap_ash_trail = bool(data['scrap_ash_trail'])
            if 'scrap_infinite_user' in data:
                player._scrap_infinite_user = bool(data['scrap_infinite_user'])
            
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
                'player': player.read()
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
            ensure_dbs2_tables()
            players = DBS2Player.query.all()
            
            total_players = len(players)
            total_crypto = sum(getattr(p, '_crypto', 0) for p in players)
            avg_crypto = total_crypto / total_players if total_players > 0 else 0
            
            # Sum wallet totals (getattr for missing columns / old schema)
            wallet_totals = {
                'satoshis': total_crypto,
                'bitcoin': sum(getattr(p, '_wallet_btc', 0) or 0 for p in players),
                'ethereum': sum(getattr(p, '_wallet_eth', 0) or 0 for p in players),
                'solana': sum(getattr(p, '_wallet_sol', 0) or 0 for p in players),
                'cardano': sum(getattr(p, '_wallet_ada', 0) or 0 for p in players),
                'dogecoin': sum(getattr(p, '_wallet_doge', 0) or 0 for p in players)
            }
            
            # Count minigame completions
            minigame_counts = {
                'crypto_miner': sum(1 for p in players if getattr(p, '_completed_crypto_miner', False)),
                'infinite_user': sum(1 for p in players if getattr(p, '_completed_infinite_user', False)),
                'laundry': sum(1 for p in players if getattr(p, '_completed_laundry', False)),
                'ash_trail': sum(1 for p in players if getattr(p, '_completed_ash_trail', False)),
                'whackarat': sum(1 for p in players if getattr(p, '_completed_whackarat', False))
            }
            
            # Count scrap ownership
            scrap_counts = {
                'crypto_miner': sum(1 for p in players if getattr(p, '_scrap_crypto_miner', False)),
                'whackarat': sum(1 for p in players if getattr(p, '_scrap_whackarat', False)),
                'laundry': sum(1 for p in players if getattr(p, '_scrap_laundry', False)),
                'ash_trail': sum(1 for p in players if getattr(p, '_scrap_ash_trail', False)),
                'infinite_user': sum(1 for p in players if getattr(p, '_scrap_infinite_user', False))
            }
            
            # Top players (getattr for _crypto in case of old schema)
            sorted_players = sorted(players, key=lambda p: getattr(p, '_crypto', 0), reverse=True)[:5]
            top_players = []
            for p in sorted_players:
                if p.user:
                    top_players.append({
                        'uid': getattr(p.user, '_uid', 'unknown'),
                        'name': getattr(p.user, '_name', 'Unknown'),
                        'crypto': getattr(p, '_crypto', 0),
                        'wallet': p.wallet
                    })
            
            return {
                'total_players': total_players,
                'total_crypto_in_circulation': total_crypto,
                'average_crypto': round(avg_crypto, 2),
                'wallet_totals': wallet_totals,
                'minigame_completions': minigame_counts,
                'scrap_ownership': scrap_counts,
                'top_players': top_players
            }, 200
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print('[DBS2] admin/stats failed:', e)
            # Return zeros so admin panel loads instead of "Error loading"
            return {
                'total_players': 0,
                'total_crypto_in_circulation': 0,
                'average_crypto': 0,
                'wallet_totals': {'satoshis': 0, 'bitcoin': 0, 'ethereum': 0, 'solana': 0, 'cardano': 0, 'dogecoin': 0},
                'minigame_completions': {'crypto_miner': 0, 'infinite_user': 0, 'laundry': 0, 'ash_trail': 0, 'whackarat': 0},
                'scrap_ownership': {'crypto_miner': 0, 'whackarat': 0, 'laundry': 0, 'ash_trail': 0, 'infinite_user': 0},
                'top_players': []
            }, 200


class _AdminBulkUpdate(Resource):
    """Bulk operations on all players"""
    
    def post(self):
        """POST /api/dbs2/admin/bulk"""
        try:
            data = request.get_json()
            action = data.get('action')
            amount = data.get('amount', 0)
            coin = data.get('coin', 'satoshis')
            
            if not action:
                return {'error': 'Action required'}, 400
            
            players = DBS2Player.query.all()
            affected = 0
            
            if action == 'add_crypto':
                for player in players:
                    player._crypto = max(0, player._crypto + int(amount))
                    affected += 1
            
            elif action == 'add_coin':
                for player in players:
                    player.add_to_wallet(coin, amount)
                    affected += 1
            
            elif action == 'set_crypto':
                for player in players:
                    player._crypto = max(0, int(amount))
                    affected += 1
            
            elif action == 'reset_all':
                for player in players:
                    player._crypto = 0
                    player._wallet_btc = 0.0
                    player._wallet_eth = 0.0
                    player._wallet_sol = 0.0
                    player._wallet_ada = 0.0
                    player._wallet_doge = 0.0
                    player._inventory = '[]'
                    player._scores = '{}'
                    player._completed_ash_trail = False
                    player._completed_crypto_miner = False
                    player._completed_whackarat = False
                    player._completed_laundry = False
                    player._completed_infinite_user = False
                    player._completed_all = False
                    # Also reset scraps
                    if hasattr(player, '_scrap_crypto_miner'):
                        player._scrap_crypto_miner = False
                    if hasattr(player, '_scrap_whackarat'):
                        player._scrap_whackarat = False
                    if hasattr(player, '_scrap_laundry'):
                        player._scrap_laundry = False
                    if hasattr(player, '_scrap_ash_trail'):
                        player._scrap_ash_trail = False
                    if hasattr(player, '_scrap_infinite_user'):
                        player._scrap_infinite_user = False
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
# SIMPLE ADMIN ENDPOINTS
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
        """PUT /api/dbs2/player/<uid> - Update player data"""
        try:
            user = User.query.filter_by(_uid=uid).first()
            if not user:
                return {'error': 'User not found'}, 404
            
            player = DBS2Player.get_by_user_id(user.id)
            if not player:
                return {'error': 'Player not found'}, 404
            
            data = request.get_json() or {}
            
            # Handle crypto/satoshis
            if 'crypto' in data:
                player._crypto = max(0, int(data['crypto']))
            if 'add_crypto' in data:
                player._crypto = max(0, player._crypto + int(data['add_crypto']))
            
            # Handle wallet coins
            if 'wallet_btc' in data:
                player._wallet_btc = max(0.0, float(data['wallet_btc']))
            if 'wallet_eth' in data:
                player._wallet_eth = max(0.0, float(data['wallet_eth']))
            if 'wallet_sol' in data:
                player._wallet_sol = max(0.0, float(data['wallet_sol']))
            if 'wallet_ada' in data:
                player._wallet_ada = max(0.0, float(data['wallet_ada']))
            if 'wallet_doge' in data:
                player._wallet_doge = max(0.0, float(data['wallet_doge']))
            
            # Handle inventory (store as JSON string or list)
            if 'inventory' in data:
                inv = data['inventory']
                if isinstance(inv, list):
                    player._inventory = json.dumps(inv)
                else:
                    player._inventory = inv
            
            # Handle scores (store as JSON string or dict)
            if 'scores' in data:
                scores = data['scores']
                if isinstance(scores, dict):
                    player._scores = json.dumps(scores)
                else:
                    player._scores = scores
            
            # Handle minigame completions
            if 'completed_crypto_miner' in data:
                player._completed_crypto_miner = bool(data['completed_crypto_miner'])
            if 'completed_infinite_user' in data:
                player._completed_infinite_user = bool(data['completed_infinite_user'])
            if 'completed_laundry' in data:
                player._completed_laundry = bool(data['completed_laundry'])
            if 'completed_ash_trail' in data:
                player._completed_ash_trail = bool(data['completed_ash_trail'])
            if 'completed_whackarat' in data:
                player._completed_whackarat = bool(data['completed_whackarat'])
            
            # Handle scrap ownership (NEW)
            if 'scrap_crypto_miner' in data:
                player._scrap_crypto_miner = bool(data['scrap_crypto_miner'])
            if 'scrap_whackarat' in data:
                player._scrap_whackarat = bool(data['scrap_whackarat'])
            if 'scrap_laundry' in data:
                player._scrap_laundry = bool(data['scrap_laundry'])
            if 'scrap_ash_trail' in data:
                player._scrap_ash_trail = bool(data['scrap_ash_trail'])
            if 'scrap_infinite_user' in data:
                player._scrap_infinite_user = bool(data['scrap_infinite_user'])
            
            # Update completed_all flag
            player._completed_all = (
                player._completed_ash_trail and
                player._completed_crypto_miner and
                player._completed_whackarat and
                player._completed_laundry and
                player._completed_infinite_user
            )
            
            db.session.commit()
            
            return {
                'message': f'Player {uid} updated successfully',
                'player': player.read()
            }, 200
            
        except Exception as e:
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return {'error': str(e)}, 500


# ============================================================================
# SHOP ENDPOINTS - Uses scrap ownership fields instead of inventory
# ============================================================================

# Shop item definitions with scrap field mapping
SHOP_ITEMS = {
    'scrap_crypto_miner': {
        'name': 'Mining Algorithm Code Scrap',
        'description': 'The core hash algorithm for The Green Machine',
        'price_coin': 'satoshis',
        'price_amount': 500,
        'scrap_field': '_scrap_crypto_miner'
    },
    'scrap_whackarat': {
        'name': 'Security Keys Code Scrap',
        'description': 'Security protocol for scam detection',
        'price_coin': 'dogecoin',
        'price_amount': 10,
        'scrap_field': '_scrap_whackarat'
    },
    'scrap_laundry': {
        'name': 'Transaction Ledger Code Scrap',
        'description': 'Transaction validation module',
        'price_coin': 'cardano',
        'price_amount': 5,
        'scrap_field': '_scrap_laundry'
    },
    'scrap_ash_trail': {
        'name': 'Backup Documentation Code Scrap',
        'description': 'Blockchain audit trail module',
        'price_coin': 'solana',
        'price_amount': 0.05,
        'scrap_field': '_scrap_ash_trail'
    },
    'scrap_infinite_user': {
        'name': 'Master Password List Code Scrap',
        'description': 'Wallet security authentication module',
        'price_coin': 'ethereum',
        'price_amount': 0.0005,
        'scrap_field': '_scrap_infinite_user'
    }
}


class _ShopPurchaseResource(Resource):
    """Handle shop purchases - sets scrap ownership field instead of adding to inventory"""
    
    @token_required()
    def post(self):
        """POST /api/dbs2/shop/purchase - Buy a code scrap from the shop"""
        try:
            player = get_current_player()
            if not player:
                return {'error': 'Player not found'}, 404
            
            data = request.get_json() or {}
            item_id = data.get('item_id')
            
            # Validate item exists
            if item_id not in SHOP_ITEMS:
                return {'error': 'Invalid item'}, 400
            
            item = SHOP_ITEMS[item_id]
            price_coin = item['price_coin']
            price_amount = item['price_amount']
            scrap_field = item.get('scrap_field')
            
            # Check if player already owns this scrap (via scrap field)
            if scrap_field and hasattr(player, scrap_field):
                if getattr(player, scrap_field, False):
                    return {'error': 'You already own this code scrap'}, 400
            
            # Get player's balance for the required coin
            coin_config = SUPPORTED_COINS.get(price_coin)
            if not coin_config:
                return {'error': 'Invalid coin type'}, 400
            
            coin_field = coin_config.get('field')
            current_balance = getattr(player, coin_field, 0) or 0
            
            # Check if player can afford
            if current_balance < price_amount:
                return {
                    'error': f'Insufficient {price_coin}. Need {price_amount}, have {current_balance}'
                }, 400
            
            # Deduct the price
            new_balance = current_balance - price_amount
            setattr(player, coin_field, new_balance)
            
            # Mark scrap as owned (set the scrap field to True)
            if scrap_field and hasattr(player, scrap_field):
                setattr(player, scrap_field, True)
            
            db.session.commit()
            
            return {
                'success': True,
                'message': f"Purchased {item['name']}",
                'item_id': item_id,
                'item_name': item['name'],
                'new_balance': new_balance,
                'coin': price_coin,
                'scrap_owned': True,
                'scraps_owned': format_scraps_owned(player)
            }, 200
            
        except Exception as e:
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return {'error': str(e)}, 500


class _ShopItemsResource(Resource):
    """Get available shop items with ownership status"""
    
    @token_required()
    def get(self):
        """GET /api/dbs2/shop/items - Get shop items with ownership status"""
        try:
            player = get_current_player()
            if not player:
                return {'error': 'Player not found'}, 404
            
            # Build response with ownership status from scrap fields
            items = []
            for item_id, item in SHOP_ITEMS.items():
                coin_config = SUPPORTED_COINS.get(item['price_coin'], {})
                coin_field = coin_config.get('field', '_crypto')
                balance = getattr(player, coin_field, 0) or 0
                
                # Check ownership via scrap field
                scrap_field = item.get('scrap_field')
                owned = False
                if scrap_field and hasattr(player, scrap_field):
                    owned = bool(getattr(player, scrap_field, False))
                
                items.append({
                    'id': item_id,
                    'name': item['name'],
                    'description': item.get('description', ''),
                    'price_coin': item['price_coin'],
                    'price_amount': item['price_amount'],
                    'owned': owned,
                    'can_afford': balance >= item['price_amount'],
                    'balance': balance
                })
            
            return {
                'items': items,
                'scraps_owned': format_scraps_owned(player)
            }, 200
            
        except Exception as e:
            import traceback
            traceback.print_exc()
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
api.add_resource(_MinigameCompleteResource, '/minigames/complete')
api.add_resource(_MinigameRewardResource, '/minigame/reward')

# Wallet endpoints (authenticated)
api.add_resource(_WalletResource, '/wallet')
api.add_resource(_WalletAddCoinResource, '/wallet/add')
api.add_resource(_WalletConvertResource, '/wallet/convert')

# Shop endpoints (authenticated)
api.add_resource(_ShopPurchaseResource, '/shop/purchase')
api.add_resource(_ShopItemsResource, '/shop/items')

# Public endpoints
api.add_resource(_LeaderboardResource, '/leaderboard')
api.add_resource(_MinigameLeaderboardResource, '/leaderboard/minigame')
api.add_resource(_PricesResource, '/prices')
api.add_resource(_BitcoinBoostResource, '/bitcoin-boost')

# Ash Trail endpoints
api.add_resource(_AshTrailRunsResource, '/ash-trail/runs')
api.add_resource(_AshTrailRunDetailResource, '/ash-trail/runs/<int:run_id>')
api.add_resource(_AshTrailAIResource, '/ash-trail/ai')

# Admin endpoints
api.add_resource(_AdminAllPlayers, '/admin/players')
api.add_resource(_AdminPlayerDetail, '/admin/player/<string:user_id>')
api.add_resource(_AdminStats, '/admin/stats')
api.add_resource(_AdminBulkUpdate, '/admin/bulk')

# Simple admin endpoints
api.add_resource(_AdminPlayersSimple, '/players')
api.add_resource(_AdminPlayerSimple, '/player/<string:uid>')