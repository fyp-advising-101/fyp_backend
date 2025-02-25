import requests

class WhatsAppAPI:
    def __init__(self, graph_api_token):
        self.graph_api_token = graph_api_token

    def mark_message_as_read(self, business_phone_number_id, message_id):
        requests.post(
            f"https://graph.facebook.com/v18.0/{business_phone_number_id}/messages",
            headers={"Authorization": f"Bearer {self.graph_api_token}"},
            json={
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id
            }
        )
    def reply_to_user(self, business_phone_number_id, user_number, reply, message_id):
        """
        Sends a reply to a user via WhatsApp using the Meta Graph API.
        
        This function sends a message from the business's WhatsApp number to a user,
        replying to a specific message the user sent.
        
        Args:
            business_phone_number_id (str): The ID of the business's WhatsApp phone number.
            user_number (str): The phone number of the recipient.
            reply (str): The message content to be sent as a reply.
            message_id (str): The ID of the message being replied to.
        
        Returns:
            None
        """
        requests.post(
            f"https://graph.facebook.com/v18.0/{business_phone_number_id}/messages",
            headers={"Authorization": f"Bearer {self.graph_api_token}"},
            json={
                "messaging_product": "whatsapp",
                "to": user_number,
                "text": {"body": reply},
                "context": {"message_id": message_id}
            }
        )