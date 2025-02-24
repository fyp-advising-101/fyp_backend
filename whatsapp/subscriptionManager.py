import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from whatsapp.database import db
from shared.models.user_subscriptions import UserSubscriptions
from shared.models.users import Users
from sqlalchemy.exc import IntegrityError
import logging

def subscribe_user(user_number, category):
    try:
        # Check if user exists
        user = db.session.get(Users, user_number)

        if not user:
            # Create new user
            user = Users(phone_number=user_number)
            db.session.add(user)
            db.session.commit()  # Commit to generate the user entry

        # Check if subscription already exists
        existing_subscription = db.session.get(UserSubscriptions, (user_number, category))

        if existing_subscription:
            return "Subscription Already Exists", 200

        # Add new subscription
        subscription = UserSubscriptions(phone_number=user_number, category=category)
        db.session.add(subscription)
        db.session.commit()

        return f"Subscription to {category} successful", 200

    except IntegrityError as e:
        db.session.rollback()
        logging.error(e)
        return "Subscription Already Exists", 200
    except Exception as e:
        db.session.rollback()
        logging.error(e)
        return "Please try again later", 500

def unsubscribe_user(user_number, category):
    try:
        # Check if the user exists
        user = db.session.get(Users, user_number)
        if not user:
            return "You are not subscribed to anything", 200

        # Check if the subscription exists
        subscription = db.session.get(UserSubscriptions, (user_number, category))
        if not subscription:
            return "You are not subscribed to this category", 200

        # Delete the subscription
        db.session.delete(subscription)
        db.session.commit()

        return f"Unsubscribed from {category} successfully", 200

    except IntegrityError as e:
        db.session.rollback()
        logging.error(e)
        return {"error": "Database integrity error while deleting subscription"}, 400
    except Exception as e:
        db.session.rollback()
        logging.error(e)
        return "Please try again later", 500
