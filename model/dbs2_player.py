"""
DBS2 Player Model - With code scrap ownership fields
Place this in: model/dbs2_player.py

MIGRATION REQUIRED: Run this SQL to add new scrap columns:
ALTER TABLE dbs2_players ADD COLUMN _scrap_crypto_miner BOOLEAN DEFAULT FALSE;
ALTER TABLE dbs2_players ADD COLUMN _scrap_whackarat BOOLEAN DEFAULT FALSE;
ALTER TABLE dbs2_players ADD COLUMN _scrap_laundry BOOLEAN DEFAULT FALSE;
ALTER TABLE dbs2_players ADD COLUMN _scrap_ash_trail BOOLEAN DEFAULT FALSE;
ALTER TABLE dbs2_players ADD COLUMN _scrap_infinite_user BOOLEAN DEFAULT FALSE;
"""

from __init__ import app, db
from model.user import User
import json
from datetime import datetime
class DBS2Player(db.Model):
    
    """
    DBS2 Player model with:
    - user_id foreign key to User
    - Individual completion fields for each minigame (_completed_*)
    - Code scrap ownership fields (_scrap_*) - purchased from shop
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
    
    equipped_character = db.Column(
            db.String(100),
            default='chillguy',
            nullable=False
        )

    # Multi-coin wallet balances
    _wallet_btc = db.Column(db.Float, default=0.0)   # Bitcoin
    _wallet_eth = db.Column(db.Float, default=0.0)   # Ethereum
    _wallet_sol = db.Column(db.Float, default=0.0)   # Solana
    _wallet_ada = db.Column(db.Float, default=0.0)   # Cardano
    _wallet_doge = db.Column(db.Float, default=0.0)  # Dogecoin
    
    # JSON fields
    _inventory = db.Column(db.Text, default='[]')
    _scores = db.Column(db.Text, default='{}')
    
    # Individual minigame completion flags (playing the minigame)
    _completed_crypto_miner = db.Column(db.Boolean, default=False)
    _completed_infinite_user = db.Column(db.Boolean, default=False)
    _completed_laundry = db.Column(db.Boolean, default=False)
    _completed_ash_trail = db.Column(db.Boolean, default=False)
    _completed_whackarat = db.Column(db.Boolean, default=False)
    _completed_all = db.Column(db.Boolean, default=False)
    
    # Code scrap ownership flags (purchased from Closet Shop)
    _scrap_crypto_miner = db.Column(db.Boolean, default=False)
    _scrap_whackarat = db.Column(db.Boolean, default=False)    # Security/CryptoChecker scrap
    _scrap_laundry = db.Column(db.Boolean, default=False)      # Transaction Validator scrap
    _scrap_ash_trail = db.Column(db.Boolean, default=False)
    _scrap_infinite_user = db.Column(db.Boolean, default=False)
    
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
        # Minigame completions
        self._completed_crypto_miner = False
        self._completed_infinite_user = False
        self._completed_laundry = False
        self._completed_ash_trail = False
        self._completed_whackarat = False
        self._completed_all = False
        # Code scrap ownership
        self._scrap_crypto_miner = False
        self._scrap_whackarat = False
        self._scrap_laundry = False
        self._scrap_ash_trail = False
        self._scrap_infinite_user = False
        # Intro
        self._has_seen_intro = False
    
    # ==================== WALLET PROPERTIES ====================
    
    @property
    def wallet(self):
        """Get full wallet as dictionary (getattr for missing columns / old DB schema)"""
        return {
            'satoshis': getattr(self, '_crypto', 0) or 0,
            'bitcoin': getattr(self, '_wallet_btc', 0) or 0.0,
            'ethereum': getattr(self, '_wallet_eth', 0) or 0.0,
            'solana': getattr(self, '_wallet_sol', 0) or 0.0,
            'cardano': getattr(self, '_wallet_ada', 0) or 0.0,
            'dogecoin': getattr(self, '_wallet_doge', 0) or 0.0
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
    
    # ==================== SCRAP OWNERSHIP ====================
    
    @property
    def scraps_owned(self):
        """Get dictionary of scrap ownership status (getattr for missing columns)"""
        return {
            'crypto_miner': getattr(self, '_scrap_crypto_miner', False) or False,
            'whackarat': getattr(self, '_scrap_whackarat', False) or False,
            'laundry': getattr(self, '_scrap_laundry', False) or False,
            'ash_trail': getattr(self, '_scrap_ash_trail', False) or False,
            'infinite_user': getattr(self, '_scrap_infinite_user', False) or False
        }
    
    def owns_scrap(self, scrap_id):
        """Check if player owns a specific scrap"""
        field_map = {
            'scrap_crypto_miner': '_scrap_crypto_miner',
            'scrap_whackarat': '_scrap_whackarat',
            'scrap_laundry': '_scrap_laundry',
            'scrap_ash_trail': '_scrap_ash_trail',
            'scrap_infinite_user': '_scrap_infinite_user',
            # Also allow without prefix
            'crypto_miner': '_scrap_crypto_miner',
            'whackarat': '_scrap_whackarat',
            'laundry': '_scrap_laundry',
            'ash_trail': '_scrap_ash_trail',
            'infinite_user': '_scrap_infinite_user'
        }
        field = field_map.get(scrap_id)
        if field:
            return getattr(self, field, False) or False
        return False
    
    def set_scrap_owned(self, scrap_id, owned=True):
        """Set ownership status for a scrap"""
        field_map = {
            'scrap_crypto_miner': '_scrap_crypto_miner',
            'scrap_whackarat': '_scrap_whackarat',
            'scrap_laundry': '_scrap_laundry',
            'scrap_ash_trail': '_scrap_ash_trail',
            'scrap_infinite_user': '_scrap_infinite_user',
            # Also allow without prefix
            'crypto_miner': '_scrap_crypto_miner',
            'whackarat': '_scrap_whackarat',
            'laundry': '_scrap_laundry',
            'ash_trail': '_scrap_ash_trail',
            'infinite_user': '_scrap_infinite_user'
        }
        field = field_map.get(scrap_id)
        if field:
            setattr(self, field, bool(owned))
            db.session.commit()
            return True
        return False
    
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
        
        # Code scrap ownership
        if 'scrap_crypto_miner' in data:
            self._scrap_crypto_miner = bool(data['scrap_crypto_miner'])
        if 'scrap_whackarat' in data:
            self._scrap_whackarat = bool(data['scrap_whackarat'])
        if 'scrap_laundry' in data:
            self._scrap_laundry = bool(data['scrap_laundry'])
        if 'scrap_ash_trail' in data:
            self._scrap_ash_trail = bool(data['scrap_ash_trail'])
        if 'scrap_infinite_user' in data:
            self._scrap_infinite_user = bool(data['scrap_infinite_user'])
        
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
        
        # Use getattr so missing columns (old DB schema) don't crash
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_info': user_info,
            'crypto': getattr(self, '_crypto', 0),
            'satoshis': getattr(self, '_crypto', 0),
            'wallet': self.wallet,
            'inventory': self.inventory,
            'scores': self.scores,
            # Minigame completions
            'completed_crypto_miner': getattr(self, '_completed_crypto_miner', False),
            'completed_infinite_user': getattr(self, '_completed_infinite_user', False),
            'completed_laundry': getattr(self, '_completed_laundry', False),
            'completed_ash_trail': getattr(self, '_completed_ash_trail', False),
            'completed_whackarat': getattr(self, '_completed_whackarat', False),
            'completed_all': getattr(self, '_completed_all', False),
            # Code scrap ownership
            'scrap_crypto_miner': getattr(self, '_scrap_crypto_miner', False) or False,
            'scrap_whackarat': getattr(self, '_scrap_whackarat', False) or False,
            'scrap_laundry': getattr(self, '_scrap_laundry', False) or False,
            'scrap_ash_trail': getattr(self, '_scrap_ash_trail', False) or False,
            'scrap_infinite_user': getattr(self, '_scrap_infinite_user', False) or False,
            'scraps_owned': self.scraps_owned,
            # Other
            'has_seen_intro': getattr(self, '_has_seen_intro', False),
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


def migrate_dbs2_players_add_scrap_columns():
    """Add scrap (and _has_seen_intro) columns to dbs2_players if missing (SQLite migration)."""
    from sqlalchemy import text
    try:
        result = db.session.execute(text("PRAGMA table_info(dbs2_players)"))
        rows = result.fetchall()
        existing = {row[1] for row in rows}  # column name is index 1
    except Exception:
        return
    columns_to_add = [
        ('_scrap_crypto_miner', 'INTEGER DEFAULT 0'),
        ('_scrap_whackarat', 'INTEGER DEFAULT 0'),
        ('_scrap_laundry', 'INTEGER DEFAULT 0'),
        ('_scrap_ash_trail', 'INTEGER DEFAULT 0'),
        ('_scrap_infinite_user', 'INTEGER DEFAULT 0'),
        ('_has_seen_intro', 'INTEGER DEFAULT 0'),
        ('equipped_character', "TEXT DEFAULT 'chillguy'"),  # 👈 ADD THIS

    ]
    for col_name, col_type in columns_to_add:
        if col_name not in existing:
            try:
                db.session.execute(text(
                    f"ALTER TABLE dbs2_players ADD COLUMN {col_name} {col_type}"
                ))
                db.session.commit()
                print(f'[DBS2] Added column dbs2_players.{col_name}')
            except Exception as e:
                db.session.rollback()
                print(f'[DBS2] migrate add column {col_name}:', e)


def initDBS2Players():
    """Initialize DBS2 players table"""
    with app.app_context():
        db.create_all()
        migrate_dbs2_players_add_scrap_columns()
        
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