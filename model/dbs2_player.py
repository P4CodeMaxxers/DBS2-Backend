from datetime import datetime
from __init__ import db
from sqlalchemy.exc import IntegrityError
import json


class DBS2Player(db.Model):
    __tablename__ = 'dbs2_players'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    _crypto = db.Column(db.Integer, default=0)
    _inventory = db.Column(db.Text, default='[]')
    _scores = db.Column(db.Text, default='{}')
    
    _completed_ash_trail = db.Column(db.Boolean, default=False)
    _completed_crypto_miner = db.Column(db.Boolean, default=False)
    _completed_whackarat = db.Column(db.Boolean, default=False)
    _completed_laundry = db.Column(db.Boolean, default=False)
    _completed_infinite_user = db.Column(db.Boolean, default=False)
    _completed_all = db.Column(db.Boolean, default=False)
    _escaped = db.Column(db.Boolean, default=False)
    
    _created_at = db.Column(db.DateTime, default=datetime.utcnow)
    _updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('dbs2_player', uselist=False))
    
    def __init__(self, user_id, crypto=0, inventory=None, scores=None):
        self.user_id = user_id
        self._crypto = crypto
        self._inventory = json.dumps(inventory) if inventory else '[]'
        self._scores = json.dumps(scores) if scores else '{}'
    
    @property
    def crypto(self):
        return self._crypto
    
    @crypto.setter
    def crypto(self, value):
        self._crypto = max(0, value)
    
    @property
    def inventory(self):
        try:
            return json.loads(self._inventory)
        except:
            return []
    
    @inventory.setter
    def inventory(self, items):
        self._inventory = json.dumps(items) if isinstance(items, list) else '[]'
    
    @property
    def scores(self):
        try:
            return json.loads(self._scores)
        except:
            return {}
    
    @scores.setter
    def scores(self, score_dict):
        self._scores = json.dumps(score_dict) if isinstance(score_dict, dict) else '{}'
    
    def create(self):
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except IntegrityError:
            db.session.rollback()
            return None
    
    def read(self):
        user_info = {}
        if self.user:
            user_info = {
                'uid': getattr(self.user, '_uid', None),
                'name': getattr(self.user, '_name', None),
            }
        
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_info': user_info,
            'crypto': self._crypto,
            'inventory': self.inventory,
            'scores': self.scores,
            'completed_ash_trail': self._completed_ash_trail,
            'completed_crypto_miner': self._completed_crypto_miner,
            'completed_whackarat': self._completed_whackarat,
            'completed_laundry': self._completed_laundry,
            'completed_infinite_user': self._completed_infinite_user,
            'completed_all': self._completed_all,
            'escaped': self._escaped,
            'created_at': self._created_at.isoformat() if self._created_at else None,
            'updated_at': self._updated_at.isoformat() if self._updated_at else None
        }
    
    def update(self, data):
        if 'crypto' in data:
            self._crypto = data['crypto']
        if 'add_crypto' in data:
            self._crypto += data['add_crypto']
        if 'inventory' in data:
            self.inventory = data['inventory']
        if 'scores' in data:
            self.scores = data['scores']
        if 'completed_ash_trail' in data:
            self._completed_ash_trail = data['completed_ash_trail']
        if 'completed_crypto_miner' in data:
            self._completed_crypto_miner = data['completed_crypto_miner']
        if 'completed_whackarat' in data:
            self._completed_whackarat = data['completed_whackarat']
        if 'completed_laundry' in data:
            self._completed_laundry = data['completed_laundry']
        if 'completed_infinite_user' in data:
            self._completed_infinite_user = data['completed_infinite_user']
        if 'escaped' in data:
            self._escaped = data['escaped']
        
        self._completed_all = (
            self._completed_ash_trail and
            self._completed_crypto_miner and
            self._completed_whackarat and
            self._completed_laundry and
            self._completed_infinite_user
        )
        
        try:
            db.session.commit()
            return self
        except:
            db.session.rollback()
            return None
    
    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except:
            db.session.rollback()
            return False
    
    def add_inventory_item(self, item):
        current = self.inventory
        current.append(item)
        self.inventory = current
        db.session.commit()
        return self.inventory
    
    def remove_inventory_item(self, index):
        current = self.inventory
        if 0 <= index < len(current):
            removed = current.pop(index)
            self.inventory = current
            db.session.commit()
            return removed
        return None
    
    def update_score(self, game_name, score):
        current = self.scores
        if game_name not in current or score > current[game_name]:
            current[game_name] = score
            self.scores = current
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def get_by_user_id(user_id):
        return DBS2Player.query.filter_by(user_id=user_id).first()
    
    @staticmethod
    def get_or_create(user_id):
        player = DBS2Player.get_by_user_id(user_id)
        if player is None:
            player = DBS2Player(user_id=user_id)
            player.create()
        return player
    
    @staticmethod
    def get_leaderboard(limit=10):
        players = DBS2Player.query.order_by(DBS2Player._crypto.desc()).limit(limit).all()
        leaderboard = []
        rank = 1
        for player in players:
            entry = player.read()
            entry['rank'] = rank
            leaderboard.append(entry)
            rank += 1
        return leaderboard
    
    @staticmethod
    def get_all_players():
        players = DBS2Player.query.all()
        return [p.read() for p in players]


def initDBS2Players():
    db.create_all()
    
    from model.user import User
    
    test_users = [
        {
            'uid': 'west',
            'name': 'West',
            'crypto': 1250,
            'inventory': [
                {'id': 'scrap1', 'name': 'DeFi Grimoire Page', 'found_at': 'bookshelf'},
                {'id': 'scrap2', 'name': 'Laundry Code', 'found_at': 'laundry'}
            ],
            'scores': {'ash_trail': 95, 'crypto_miner': 1500, 'whackarat': 800},
            'completed_ash_trail': True,
            'completed_crypto_miner': True,
            'completed_whackarat': True,
            'completed_laundry': True,
            'completed_infinite_user': True
        },
        {
            'uid': 'cyrus',
            'name': 'Cyrus',
            'crypto': 980,
            'inventory': [
                {'id': 'scrap1', 'name': 'DeFi Grimoire Page', 'found_at': 'bookshelf'}
            ],
            'scores': {'ash_trail': 88, 'crypto_miner': 1200, 'whackarat': 650},
            'completed_ash_trail': True,
            'completed_crypto_miner': True,
            'completed_whackarat': True,
            'completed_laundry': False,
            'completed_infinite_user': False
        },
        {
            'uid': 'maya',
            'name': 'Maya',
            'crypto': 750,
            'inventory': [],
            'scores': {'ash_trail': 72, 'crypto_miner': 900},
            'completed_ash_trail': True,
            'completed_crypto_miner': True,
            'completed_whackarat': False,
            'completed_laundry': False,
            'completed_infinite_user': False
        }
    ]
    
    for data in test_users:
        user = User.query.filter_by(_uid=data['uid']).first()
        if not user:
            user = User(name=data['name'], uid=data['uid'], password='dbs2test')
            user.create()
        
        player = DBS2Player.get_by_user_id(user.id)
        if not player:
            player = DBS2Player(
                user_id=user.id,
                crypto=data['crypto'],
                inventory=data['inventory'],
                scores=data['scores']
            )
            player._completed_ash_trail = data['completed_ash_trail']
            player._completed_crypto_miner = data['completed_crypto_miner']
            player._completed_whackarat = data['completed_whackarat']
            player._completed_laundry = data['completed_laundry']
            player._completed_infinite_user = data['completed_infinite_user']
            player._completed_all = all([
                data['completed_ash_trail'],
                data['completed_crypto_miner'],
                data['completed_whackarat'],
                data['completed_laundry'],
                data['completed_infinite_user']
            ])
            player.create()
    
    print("DBS2 Players initialized with test users: West, Cyrus, Maya")