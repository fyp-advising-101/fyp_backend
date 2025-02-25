import requests
import logging

class WhatsAppAPI:
    def __init__(self, graph_api_token):
        self.graph_api_token = graph_api_token
        self.business_phone_number_id = '427471850458639'

    def mark_message_as_read(self, message_id):
        requests.post(
            f"https://graph.facebook.com/v18.0/{self.business_phone_number_id}/messages",
            headers={"Authorization": f"Bearer {self.graph_api_token}"},
            json={
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id
            }
        )
    def reply_to_user(self, user_number, reply, message_id):
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
            f"https://graph.facebook.com/v18.0/{self.business_phone_number_id}/messages",
            headers={"Authorization": f"Bearer {self.graph_api_token}"},
            json={
                "messaging_product": "whatsapp",
                "to": user_number,
                "text": {"body": reply},
                "context": {"message_id": message_id}
            }
        )

    def send_template_message(self, phone_number, template, image_url, caption):
        """
        Sends a WhatsApp template message to a user.

        Parameters:
        - business_phone_number_id (str): The WhatsApp Business phone number ID.
        - phone_number (str): The recipient's phone number in international format.
        - template (str): The name of the WhatsApp message template.
        - image_url (str): URL of the image to be included in the message header.
        - caption (str): Text to be included in the body of the message.

        Returns:
        - dict: Response from the WhatsApp API.
        - int: HTTP status code of the response.
        """

        url = f"https://graph.facebook.com/v22.0/{self.business_phone_number_id}/messages"

        headers = {
            "Authorization": f"Bearer {self.graph_api_token}",
            "Content-Type": "application/json"
        }

        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": "+96171482911",
            "type": "template",
            "template": {
                "name": "sports",
                "language": {
                "code": "en"
                },
                "components": [
                {
                    "type": "header",
                    "parameters": [
                    {
                        "type": "image",
                        "image": {
                        "link": "https://postingoninstagram.blob.core.windows.net/media-gen/images/146aa72c8c29448fa0fa9484cc745467_generated_image.png"
                        }
                    }
                    ]
                },
                {
                    "type": "body",
                    "parameters": [
                    {
                        "type": "text",
                        "text": "AUBite"
                    },
                    {
                        "type": "text",
                        "text": "There is a sports event tomorrow. FEA will play against OSB!"
                    }
                    ]
                }
                ]
            }
            }
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx, 5xx)
            return response.json(), response.status_code
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error occurred: {http_err} - Response: {response.text}")
            return {"error": "HTTP error occurred", "details": str(http_err)}, response.status_code
        except requests.exceptions.ConnectionError:
            logging.error("Connection error occurred")
            return {"error": "Connection error occurred"}, 503
        except requests.exceptions.Timeout:
            logging.error("Request timed out")
            return {"error": "Request timed out"}, 504
        except requests.exceptions.RequestException as err:
            logging.error(f"Unexpected error: {err}")
            return {"error": "An unexpected error occurred", "details": str(err)}, 500
        

        
