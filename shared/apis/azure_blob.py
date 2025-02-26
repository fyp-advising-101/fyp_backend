import os
import uuid
import logging
from azure.storage.blob import BlobServiceClient, ContentSettings
from azure.core.exceptions import AzureError

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class AzureBlobManager:
    def __init__(self, connection_string: str, container_name="media-gen"):
        """
        Initializes the AzureBlobManager with a connection string and container name.
        
        :param connection_string: The connection string for your Azure Storage account.
        :param container_name: The name of the blob container.
        """
        self.connection_string = connection_string
        self.container_name = container_name
        try:
            self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
        except AzureError as e:
            logging.error(f"Failed to connect to Azure Blob Storage: {e}")
            raise

    def upload_file(self, file_path: str, file_type: str = "image", content_type: str = "image/png") -> dict:
        """
        Uploads a file to Azure Blob Storage and returns a dictionary containing:
          - blob_url: The public URL of the uploaded blob.
          - blob_id: The unique identifier (blob name) used to store the file.
          - file_name: The original name of the file.
        
        :param file_path: The local path of the file to be uploaded.
        :param file_type: The type of file being uploaded (used for folder-like structuring). Default is "image".
        :param content_type: The MIME type of the file.
        :return: A dictionary with the blob details, or None if an error occurs.
        """
        if not os.path.exists(file_path):
            logging.error(f"File not found: {file_path}")
            return None

        try:
            original_file_name = os.path.basename(file_path)
            # Generate a unique blob name (folder structure: images/, videos/, etc.)
            blob_name = f"{file_type}s/{uuid.uuid4().hex}_{original_file_name}"
            
            blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=blob_name)

            # Upload file
            with open(file_path, "rb") as data:
                blob_client.upload_blob(data, 
                                        content_settings=ContentSettings(content_type=content_type), 
                                        overwrite=True)

            blob_url = (
                f"https://{self.blob_service_client.account_name}.blob.core.windows.net/"
                f"{self.container_name}/{blob_name}"
            )

            logging.info(f"File uploaded successfully: {blob_url}")

            return {
                "blob_url": blob_url,
                "blob_id": blob_name,
                "file_name": original_file_name
            }
        except AzureError as e:
            logging.error(f"Azure Upload Error: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error during file upload: {e}")
            return None

    def get_blob(self, blob_id: str) -> bytes:
        """
        Retrieves the blob content from Azure Blob Storage.
        
        :param blob_id: The unique identifier of the blob.
        :return: The file content as bytes, or None if an error occurs.
        """
        if not blob_id:
            logging.error("Invalid blob ID provided for retrieval.")
            return None

        try:
            blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=blob_id)
            download_stream = blob_client.download_blob()
            logging.info(f"Blob retrieved successfully: {blob_id}")
            return download_stream.readall()
        except AzureError as e:
            logging.error(f"Azure Download Error: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error during blob retrieval: {e}")
            return None

    def delete_blob(self, blob_id: str) -> bool:
        """
        Deletes the specified blob from Azure Blob Storage.
        
        :param blob_id: The unique identifier (blob name) of the image.
        :return: True if deletion is successful, False otherwise.
        """
        if not blob_id:
            logging.error("Invalid blob ID provided for deletion.")
            return False

        try:
            blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=blob_id)
            blob_client.delete_blob()
            logging.info(f"Blob deleted successfully: {blob_id}")
            return True
        except AzureError as e:
            logging.error(f"Azure Delete Error: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error during blob deletion: {e}")
            return False
