from datetime import datetime
import json

from __init__ import db


class AshTrailRun(db.Model):
    """
    Stores a single Ash Trail run (ghost replay) for a specific book.

    book_id: one of 'defi_grimoire' | 'lost_ledger' | 'proof_of_burn'
    trace: list of points in grid space [{x, y}, ...] serialized as JSON text
    """

    __tablename__ = 'ashtrail_runs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    book_id = db.Column(db.String(64), nullable=False, index=True)
    score = db.Column(db.Float, nullable=False, default=0)
    _trace = db.Column(db.Text, nullable=False, default='[]')
    guest_name = db.Column(db.String(128), nullable=True)  # Display name when run is from unauthenticated guest
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship('User', backref=db.backref('ashtrail_runs', lazy=True))

    @property
    def trace(self):
        try:
            return json.loads(self._trace)
        except Exception:
            return []

    @trace.setter
    def trace(self, points):
        self._trace = json.dumps(points) if isinstance(points, list) else '[]'

    def read(self, include_trace=False):
        user_info = {}
        if self.user:
            display_name = self.guest_name if self.guest_name else getattr(self.user, '_name', None)
            user_info = {
                'uid': getattr(self.user, '_uid', None),
                'name': display_name or getattr(self.user, '_name', None),
            }
        payload = {
            'id': self.id,
            'user_info': user_info,
            'book_id': self.book_id,
            'score': self.score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if include_trace:
            payload['trace'] = self.trace
        return payload


