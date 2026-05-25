#!/usr/bin/env python3
"""Admin script: create an API key for an existing user."""

import sys
import secrets
import hashlib
import uuid
import datetime
from db import SessionLocal, User, ApiKey


def create_api_key(email: str, name: str = "primary") -> None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"ERROR: User '{email}' not found.")
            sys.exit(1)

        prefix = "acr_"
        raw_key = prefix + secrets.token_hex(20)
        display_prefix = raw_key[:len(prefix) + 8]
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        api_key = ApiKey(
            id=str(uuid.uuid4()),
            user_id=user.id,
            name=name,
            key_prefix=display_prefix,
            key_hash=key_hash,
            is_active=True,
            created_at=datetime.datetime.utcnow(),
        )
        db.add(api_key)
        db.commit()

        print(f"API key created for {email}")
        print(f"Key ID:  {api_key.id}")
        print(f"API Key: {raw_key}")
        print("Save this key — it will not be shown again.")
    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python create_api_key.py <email> [key-name]")
        sys.exit(1)
    email = sys.argv[1].strip().lower()
    name = sys.argv[2] if len(sys.argv) > 2 else "primary"
    create_api_key(email, name)
