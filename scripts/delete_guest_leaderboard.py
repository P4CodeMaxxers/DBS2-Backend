#!/usr/bin/env python3
"""
Remove all guest users from DBS2 leaderboards:
- Deletes DBS2Player rows for guest users (main Satoshis + minigame leaderboards).
- Deletes AshTrailRun rows for the shared guest user (Ash Trail runs list).

Keeps the _ashtrail_guest User so future guest runs can still be stored.

Usage (from repo root):
  python scripts/delete_guest_leaderboard.py
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app, db
from model.user import User
from model.dbs2_player import DBS2Player
from model.ashtrail_run import AshTrailRun


def main():
    with app.app_context():
        # Guest users: shared Ash Trail guest and any Guest_* signups
        guest_users = User.query.filter(
            (User._uid == '_ashtrail_guest') | (User._name.like('Guest_%'))
        ).all()
        if not guest_users:
            print('No guest users found.')
            return
        guest_ids = [u.id for u in guest_users]
        print(f'Found {len(guest_ids)} guest user(s): {[f"{u._name}(id={u.id})" for u in guest_users]}')

        # Remove from main + minigame leaderboards (DBS2Player)
        deleted_players = DBS2Player.query.filter(DBS2Player.user_id.in_(guest_ids)).all()
        for p in deleted_players:
            db.session.delete(p)
        if deleted_players:
            print(f'Deleted {len(deleted_players)} DBS2Player row(s) (leaderboard entries).')

        # Remove guest Ash Trail runs (so they disappear from Ash Trail runs list)
        deleted_runs = AshTrailRun.query.filter(AshTrailRun.user_id.in_(guest_ids)).all()
        for r in deleted_runs:
            db.session.delete(r)
        if deleted_runs:
            print(f'Deleted {len(deleted_runs)} AshTrailRun row(s) (guest runs).')

        if deleted_players or deleted_runs:
            db.session.commit()
            print('Done. Guest users removed from leaderboards.')
        else:
            print('No leaderboard or run entries to delete.')


if __name__ == '__main__':
    main()
