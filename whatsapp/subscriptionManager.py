import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.database import SessionLocal
from shared.models.user_subscriptions import UserSubscriptions
from shared.models.users import Users
from sqlalchemy.exc import IntegrityError
import logging

def subscribe_user(user_number, category):
    """
    Subscribes a user to a specific category.
    
    This function checks if the user exists in the database. If not, it creates a new user entry.
    Then, it verifies if the user is already subscribed to the given category. If they are,
    it returns a message indicating the subscription already exists. Otherwise, it creates
    a new subscription entry in the database.
    
    Args:
        user_number (str): The phone number of the user.
        category (str): The category the user wants to subscribe to.
    
    Returns:
        tuple: A message string and an HTTP status code.
        - "Subscription Already Exists", 200: If the user is already subscribed.
        - "Subscription to {category} successful", 200: If the subscription is successful.
        - "Please try again later", 500: If an unexpected error occurs.
    """
    db_session = SessionLocal()
    try:
        # Check if user exists
        user = db_session.get(Users, user_number)

        if not user:
            # Create new user
            user = Users(phone_number=user_number)
            db_session.add(user)
            db_session.commit()  # Commit to generate the user entry

        # Check if subscription already exists
        existing_subscription = db_session.get(UserSubscriptions, (user_number, category))

        if existing_subscription:
            return "Subscription Already Exists", 200

        # Add new subscription
        subscription = UserSubscriptions(phone_number=user_number, category=category)
        db_session.add(subscription)
        db_session.commit()

        return f"Subscription to {category} successful", 200

    except IntegrityError as e:
        db_session.rollback()
        logging.error(e)
        return "Subscription Already Exists", 200
    except Exception as e:
        db_session.rollback()
        logging.error(e)
        return "Please try again later", 503
    finally:
        db_session.close()

def unsubscribe_user(user_number, category):
    """
    Unsubscribes a user from a specific category.
    
    This function checks if the user exists in the database. If they do not exist,
    it returns a message indicating that the user is not subscribed to anything.
    Then, it checks if the user is subscribed to the given category. If not, it
    returns a message indicating the user is not subscribed to that category.
    If the subscription exists, it deletes the subscription entry from the database.
    
    Args:
        user_number (str): The phone number of the user.
        category (str): The category the user wants to unsubscribe from.
    
    Returns:
        tuple: A message string and an HTTP status code.
        - "You are not subscribed to anything", 200: If the user does not exist.
        - "You are not subscribed to this category", 200: If the user is not subscribed to the category.
        - "Unsubscribed from {category} successfully", 200: If the unsubscription is successful.
        - {"error": "Database integrity error while deleting subscription"}, 400: If a database integrity error occurs.
        - "Please try again later", 500: If an unexpected error occurs.
    """
    db_session = SessionLocal()
    try:
        # Check if the user exists
        user = db_session.get(Users, user_number)
        if not user:
            return "You are not subscribed to anything", 200

        # Check if the subscription exists
        subscription = db_session.get(UserSubscriptions, (user_number, category))
        if not subscription:
            return "You are not subscribed to this category", 200

        # Delete the subscription
        db_session.delete(subscription)
        db_session.commit()

        return f"Unsubscribed from {category} successfully", 200

    except IntegrityError as e:
        db_session.rollback()
        logging.error(e)
        return {"error": "Database integrity error while deleting subscription"}, 400
    except Exception as e:
        db_session.rollback()
        logging.error(e)
        return "Please try again later", 503
    finally:
        db_session.close()
