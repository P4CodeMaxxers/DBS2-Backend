"""
DBS2 Player Model - Original structure with multi-coin wallet support
Place this in: model/dbs2_player.py
"""

from __init__ import app, db
from model.user import User
import json
from datetime import datetime


class DBS2Player(db.Model):
    """
    DBS2 Player model with:
    - user_id foreign key to User
    - Individual completion fields for each minigame
    - _crypto for main satoshi balance
    - Multi-coin wallet balances (BTC, ETH, SOL, ADA, DOGE)
    - JSON fields for inventory and scores
    """
    __tablename__ = 'dbs2_players'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to User
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    
    # Main currency (satoshis)
    _crypto = db.Column(db.Integer, default=0)
    
    # Multi-coin wallet balances
    _wallet_btc = db.Column(db.Float, default=0.0)   # Bitcoin
    _wallet_eth = db.Column(db.Float, default=0.0)   # Ethereum
    _wallet_sol = db.Column(db.Float, default=0.0)   # Solana
    _wallet_ada = db.Column(db.Float, default=0.0)   # Cardano
    _wallet_doge = db.Column(db.Float, default=0.0)  # Dogecoin
    
    # JSON fields
    _inventory = db.Column(db.Text, default='[]')
    _scores = db.Column(db.Text, default='{}')
    
    # Individual minigame completion flags
    _completed_crypto_miner = db.Column(db.Boolean, default=False)
    _completed_infinite_user = db.Column(db.Boolean, default=False)
    _completed_laundry = db.Column(db.Boolean, default=False)
    _completed_ash_trail = db.Column(db.Boolean, default=False)
    _completed_whackarat = db.Column(db.Boolean, default=False)
    _completed_all = db.Column(db.Boolean, default=False)
    
    # Intro tracking
    _has_seen_intro = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to User
    user = db.relationship('User', backref=db.backref('dbs2_player', uselist=False, lazy=True))
    
    def __init__(self, user_id):
        self.user_id = user_id
        self._crypto = 0
        self._wallet_btc = 0.0
        self._wallet_eth = 0.0
        self._wallet_sol = 0.0
        self._wallet_ada = 0.0
        self._wallet_doge = 0.0
        self._inventory = '[]'
        self._scores = '{}'
        self._completed_crypto_miner = False
        self._completed_infinite_user = False
        self._completed_laundry = False
        self._completed_ash_trail = False
        self._completed_whackarat = False
        self._completed_all = False
        self._has_seen_intro = False
    
    # ==================== WALLET PROPERTIES ====================
    
    @property
    def wallet(self):
        """Get full wallet as dictionary"""
        return {
            'satoshis': self._crypto,
            'bitcoin': self._wallet_btc or 0.0,
            'ethereum': self._wallet_eth or 0.0,
            'solana': self._wallet_sol or 0.0,
            'cardano': self._wallet_ada or 0.0,
            'dogecoin': self._wallet_doge or 0.0
        }
    
    def add_to_wallet(self, coin_id, amount):
        """Add amount to a specific coin balance"""
        field_map = {
            'satoshis': '_crypto',
            'bitcoin': '_wallet_btc',
            'ethereum': '_wallet_eth',
            'solana': '_wallet_sol',
            'cardano': '_wallet_ada',
            'dogecoin': '_wallet_doge'
        }
        
        if coin_id not in field_map:
            return False
        
        field = field_map[coin_id]
        current = getattr(self, field, 0) or 0
        
        if coin_id == 'satoshis':
            setattr(self, field, max(0, int(current + amount)))
        else:
            setattr(self, field, max(0.0, float(current + amount)))
        
        db.session.commit()
        return True
    
    # ==================== INVENTORY PROPERTY ====================
    
    @property
    def inventory(self):
        """Get inventory as list"""
        try:
            return json.loads(self._inventory)
        except:
            return []
    
    @inventory.setter
    def inventory(self, value):
        """Set inventory from list"""
        if isinstance(value, list):
            self._inventory = json.dumps(value)
        else:
            self._inventory = '[]'
        db.session.commit()
    
    def add_inventory_item(self, item):
        """Add item to inventory"""
        inv = self.inventory
        inv.append(item)
        self._inventory = json.dumps(inv)
        db.session.commit()
        return inv
    
    def remove_inventory_item(self, index):
        """Remove item from inventory by index"""
        inv = self.inventory
        if 0 <= index < len(inv):
            removed = inv.pop(index)
            self._inventory = json.dumps(inv)
            db.session.commit()
            return removed
        return None
    
    # ==================== SCORES PROPERTY ====================
    
    @property
    def scores(self):
        """Get scores as dict"""
        try:
            return json.loads(self._scores)
        except:
            return {}
    
    @scores.setter
    def scores(self, value):
        """Set scores from dict"""
        if isinstance(value, dict):
            self._scores = json.dumps(value)
        else:
            self._scores = '{}'
        db.session.commit()
    
    def update_score(self, game, score):
        """Update score for a game (keeps highest)"""
        current_scores = self.scores
        if game not in current_scores or score > current_scores[game]:
            current_scores[game] = score
            self._scores = json.dumps(current_scores)
            db.session.commit()
        return current_scores
    
    # ==================== UPDATE METHOD ====================
    
    def update(self, data):
        """Update player with dictionary of values"""
        if not data:
            return self
        
        # Crypto/satoshis
        if 'crypto' in data:
            self._crypto = max(0, int(data['crypto']))
        if 'satoshis' in data:
            self._crypto = max(0, int(data['satoshis']))
        if 'add_crypto' in data:
            self._crypto = max(0, self._crypto + int(data['add_crypto']))
        
        # Wallet coins
        if 'wallet_btc' in data:
            self._wallet_btc = max(0.0, float(data['wallet_btc']))
        if 'wallet_eth' in data:
            self._wallet_eth = max(0.0, float(data['wallet_eth']))
        if 'wallet_sol' in data:
            self._wallet_sol = max(0.0, float(data['wallet_sol']))
        if 'wallet_ada' in data:
            self._wallet_ada = max(0.0, float(data['wallet_ada']))
        if 'wallet_doge' in data:
            self._wallet_doge = max(0.0, float(data['wallet_doge']))
        
        # Inventory
        if 'inventory' in data:
            self.inventory = data['inventory']
        
        # Scores
        if 'scores' in data:
            self.scores = data['scores']
        
        # Minigame completions
        if 'completed_crypto_miner' in data:
            self._completed_crypto_miner = bool(data['completed_crypto_miner'])
        if 'completed_infinite_user' in data:
            self._completed_infinite_user = bool(data['completed_infinite_user'])
        if 'completed_laundry' in data:
            self._completed_laundry = bool(data['completed_laundry'])
        if 'completed_ash_trail' in data:
            self._completed_ash_trail = bool(data['completed_ash_trail'])
        if 'completed_whackarat' in data:
            self._completed_whackarat = bool(data['completed_whackarat'])
        
        # Update completed_all flag
        self._completed_all = (
            self._completed_ash_trail and
            self._completed_crypto_miner and
            self._completed_whackarat and
            self._completed_laundry and
            self._completed_infinite_user
        )
        
        # Intro
        if 'has_seen_intro' in data:
            self._has_seen_intro = bool(data['has_seen_intro'])
        
        db.session.commit()
        return self
    
    # ==================== READ METHOD ====================
    
    def read(self):
        """Serialize player to dictionary"""
        user_info = {}
        if self.user:
            user_info = {
                'id': self.user.id,
                'uid': getattr(self.user, '_uid', None),
                'name': getattr(self.user, '_name', None)
            }
        
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_info': user_info,
            'crypto': self._crypto,
            'satoshis': self._crypto,
            'wallet': self.wallet,
            'inventory': self.inventory,
            'scores': self.scores,
            'completed_crypto_miner': self._completed_crypto_miner,
            'completed_infinite_user': self._completed_infinite_user,
            'completed_laundry': self._completed_laundry,
            'completed_ash_trail': self._completed_ash_trail,
            'completed_whackarat': self._completed_whackarat,
            'completed_all': self._completed_all,
            'has_seen_intro': self._has_seen_intro,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    # ==================== STATIC METHODS ====================
    
    @staticmethod
    def get_or_create(user_id):
        """Get existing player or create new one"""
        player = DBS2Player.query.filter_by(user_id=user_id).first()
        if not player:
            player = DBS2Player(user_id)
            db.session.add(player)
            db.session.commit()
        return player
    
    @staticmethod
    def get_by_user_id(user_id):
        """Get player by user_id"""
        return DBS2Player.query.filter_by(user_id=user_id).first()
    
    @staticmethod
    def get_all_players():
        """Get all players as list of dicts"""
        players = DBS2Player.query.all()
        return [p.read() for p in players]
    
    @staticmethod
    def get_leaderboard(limit=10):
        """Get top players by crypto"""
        players = DBS2Player.query.order_by(DBS2Player._crypto.desc()).limit(limit).all()
        leaderboard = []
        for i, player in enumerate(players):
            data = player.read()
            data['rank'] = i + 1
            leaderboard.append(data)
        return leaderboard


def initDBS2Players():
    """Initialize DBS2 players table"""
    with app.app_context():
        db.create_all()
        
        # Create test players if they don't exist
        test_uids = ['west', 'cyrus', 'maya']
        for uid in test_uids:
            user = User.query.filter_by(_uid=uid).first()
            if user:
                if not DBS2Player.query.filter_by(user_id=user.id).first():
                    player = DBS2Player(user.id)
                    player._crypto = 100  # Starting satoshis
                    db.session.add(player)
        
        db.session.commit()
        print("DBS2 Players table initialized")