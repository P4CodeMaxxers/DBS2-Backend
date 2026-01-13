# model/dbs2_player.py
# Updated DBS2 Player model with multi-coin wallet support

from sqlite3 import IntegrityError
from __init__ import app, db
import json

# Supported cryptocurrencies
SUPPORTED_COINS = ['bitcoin', 'ethereum', 'solana', 'cardano', 'dogecoin']

class DBS2Player(db.Model):
    """
    DBS2 Player model with wallet supporting multiple cryptocurrencies.
    
    Wallet structure:
    {
        "satoshis": 0,       # Main score currency (1 BTC = 100,000,000 satoshis)
        "bitcoin": 0.0,      # BTC balance
        "ethereum": 0.0,     # ETH balance
        "solana": 0.0,       # SOL balance
        "cardano": 0.0,      # ADA balance
        "dogecoin": 0.0      # DOGE balance
    }
    """
    __tablename__ = 'dbs2_players'
    
    id = db.Column(db.Integer, primary_key=True)
    _uid = db.Column(db.String(255), unique=True, nullable=False)
    _wallet = db.Column(db.Text, default='{}')
    _inventory = db.Column(db.Text, default='[]')
    _scores = db.Column(db.Text, default='{}')
    _minigames_completed = db.Column(db.Text, default='{}')
    _has_seen_intro = db.Column(db.Boolean, default=False)
    
    def __init__(self, uid):
        self._uid = uid
        self._wallet = json.dumps(self._default_wallet())
        self._inventory = '[]'
        self._scores = '{}'
        self._minigames_completed = '{}'
        self._has_seen_intro = False
    
    @staticmethod
    def _default_wallet():
        """Return default empty wallet structure"""
        return {
            'satoshis': 0,
            'bitcoin': 0.0,
            'ethereum': 0.0,
            'solana': 0.0,
            'cardano': 0.0,
            'dogecoin': 0.0
        }
    
    # ==================== WALLET PROPERTIES ====================
    
    @property
    def wallet(self):
        """Get wallet as dictionary"""
        try:
            w = json.loads(self._wallet)
            # Ensure all coins exist
            default = self._default_wallet()
            for key in default:
                if key not in w:
                    w[key] = default[key]
            return w
        except:
            return self._default_wallet()
    
    @wallet.setter
    def wallet(self, wallet_dict):
        """Set wallet from dictionary"""
        if isinstance(wallet_dict, dict):
            self._wallet = json.dumps(wallet_dict)
        else:
            self._wallet = json.dumps(self._default_wallet())
    
    @property
    def satoshis(self):
        """Get satoshi balance (main score)"""
        return self.wallet.get('satoshis', 0)
    
    @property
    def crypto(self):
        """Backwards compatibility - returns satoshis"""
        return self.satoshis
    
    # ==================== WALLET METHODS ====================
    
    def add_satoshis(self, amount):
        """Add satoshis to wallet"""
        w = self.wallet
        w['satoshis'] = w.get('satoshis', 0) + int(amount)
        self.wallet = w
        db.session.commit()
        return w['satoshis']
    
    def add_coin(self, coin_id, amount):
        """Add cryptocurrency to wallet"""
        if coin_id not in SUPPORTED_COINS:
            return None
        w = self.wallet
        w[coin_id] = w.get(coin_id, 0.0) + float(amount)
        self.wallet = w
        db.session.commit()
        return w[coin_id]
    
    def update_wallet(self, updates):
        """
        Update multiple wallet balances at once.
        
        Args:
            updates (dict): {'satoshis': 100, 'bitcoin': 0.001, ...}
        
        Returns:
            dict: Updated wallet
        """
        w = self.wallet
        for key, amount in updates.items():
            if key == 'satoshis':
                w['satoshis'] = w.get('satoshis', 0) + int(amount)
            elif key in SUPPORTED_COINS:
                w[key] = w.get(key, 0.0) + float(amount)
        self.wallet = w
        db.session.commit()
        return w
    
    def convert_to_satoshis(self, coin_id, amount, exchange_rate):
        """
        Convert cryptocurrency to satoshis.
        
        Args:
            coin_id (str): Coin to convert (e.g., 'bitcoin')
            amount (float): Amount of coin to convert
            exchange_rate (float): Current USD price of coin
        
        Returns:
            dict: {'success': bool, 'satoshis_gained': int, 'wallet': dict}
        """
        if coin_id not in SUPPORTED_COINS:
            return {'success': False, 'error': 'Invalid coin'}
        
        w = self.wallet
        current_balance = w.get(coin_id, 0.0)
        
        if amount > current_balance:
            return {'success': False, 'error': 'Insufficient balance'}
        
        # Convert: coin_amount * USD_price * 100 (1 USD = 100 satoshis in our game)
        satoshis_gained = int(amount * exchange_rate * 100)
        
        w[coin_id] = current_balance - amount
        w['satoshis'] = w.get('satoshis', 0) + satoshis_gained
        self.wallet = w
        db.session.commit()
        
        return {
            'success': True,
            'satoshis_gained': satoshis_gained,
            'wallet': w
        }
    
    # ==================== LEGACY CRYPTO METHODS (backwards compat) ====================
    
    def add_crypto(self, amount):
        """Backwards compatibility - adds satoshis"""
        return self.add_satoshis(amount)
    
    def set_crypto(self, amount):
        """Backwards compatibility - sets satoshis"""
        w = self.wallet
        w['satoshis'] = int(amount)
        self.wallet = w
        db.session.commit()
        return w['satoshis']
    
    # ==================== INVENTORY METHODS ====================
    
    @property
    def inventory(self):
        try:
            return json.loads(self._inventory)
        except:
            return []
    
    @inventory.setter
    def inventory(self, inv_list):
        self._inventory = json.dumps(inv_list) if isinstance(inv_list, list) else '[]'
    
    def add_inventory_item(self, item):
        inv = self.inventory
        inv.append(item)
        self._inventory = json.dumps(inv)
        db.session.commit()
        return inv
    
    def remove_inventory_item(self, index):
        inv = self.inventory
        if 0 <= index < len(inv):
            removed = inv.pop(index)
            self._inventory = json.dumps(inv)
            db.session.commit()
            return removed
        return None
    
    # ==================== SCORES METHODS ====================
    
    @property
    def scores(self):
        try:
            return json.loads(self._scores)
        except:
            return {}
    
    @scores.setter
    def scores(self, score_dict):
        self._scores = json.dumps(score_dict) if isinstance(score_dict, dict) else '{}'
    
    def update_score(self, game, score):
        """Update score for a game (keeps highest)"""
        current = self.scores
        if game not in current or score > current[game]:
            current[game] = score
            self._scores = json.dumps(current)
            db.session.commit()
        return current
    
    # ==================== MINIGAMES METHODS ====================
    
    @property
    def minigames_completed(self):
        try:
            return json.loads(self._minigames_completed)
        except:
            return {}
    
    @minigames_completed.setter
    def minigames_completed(self, completed_dict):
        self._minigames_completed = json.dumps(completed_dict) if isinstance(completed_dict, dict) else '{}'
    
    def complete_minigame(self, game_name):
        completed = self.minigames_completed
        completed[game_name] = True
        self._minigames_completed = json.dumps(completed)
        db.session.commit()
        return completed
    
    def is_minigame_completed(self, game_name):
        return self.minigames_completed.get(game_name, False)
    
    # ==================== INTRO TRACKING ====================
    
    @property
    def has_seen_intro(self):
        return self._has_seen_intro
    
    def mark_intro_seen(self):
        self._has_seen_intro = True
        db.session.commit()
        return True
    
    # ==================== UID PROPERTY ====================
    
    @property
    def uid(self):
        return self._uid
    
    # ==================== STATIC METHODS ====================
    
    @staticmethod
    def get_or_create(uid):
        """Get existing player or create new one"""
        player = DBS2Player.query.filter_by(_uid=uid).first()
        if not player:
            player = DBS2Player(uid)
            db.session.add(player)
            db.session.commit()
        return player
    
    @staticmethod
    def get_all_players():
        """Get all players for leaderboard"""
        return DBS2Player.query.all()
    
    # ==================== SERIALIZATION ====================
    
    def to_dict(self):
        """Serialize player to dictionary"""
        return {
            'uid': self.uid,
            'wallet': self.wallet,
            'satoshis': self.satoshis,
            'crypto': self.crypto,  # backwards compat
            'inventory': self.inventory,
            'scores': self.scores,
            'minigames_completed': self.minigames_completed,
            'has_seen_intro': self.has_seen_intro
        }


def initDBS2Players():
    """Initialize DBS2 players table"""
    with app.app_context():
        db.create_all()
        
        # Create test players if they don't exist
        test_users = ['west', 'cyrus', 'maya']
        for uid in test_users:
            if not DBS2Player.query.filter_by(_uid=uid).first():
                player = DBS2Player(uid)
                player.add_satoshis(100)  # Starting satoshis
                db.session.add(player)
        
        db.session.commit()
        print("DBS2 Players table initialized")