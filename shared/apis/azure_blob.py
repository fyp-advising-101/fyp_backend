import os
import uuid
from azure.storage.blob import BlobServiceClient, ContentSettings

class AzureBlobManager:
    def __init__(self, connection_string: str, container_name="media-gen"):
        """
        Initializes the AzureBlobUploader with a connection string and container name.
        
        :param connection_string: The connection string for your Azure Storage account.
        :param container_name: The name of the blob container.
        """
        self.connection_string = connection_string
        self.container_name = container_name
        self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)

    def upload_file(self, file_path: str, file_type: str = "image", content_type: str = "image/png") -> dict:
        """
        Uploads a file to Azure Blob Storage and returns a dictionary containing:
          - blob_url: The public URL of the uploaded blob.
          - blob_id: The unique identifier (blob name) used to store the file.
          - file_name: The original name of the file.
        
        :param file_path: The local path of the file to be uploaded.
        :param file_type: The type of file being uploaded (used for folder-like structuring). Default is "image".
        :return: A dictionary with the blob details, or None if an error occurs.
        """
        try:
            original_file_name = os.path.basename(file_path)
            # Generate a unique blob name which will serve as the blob's "ID"
            blob_name = f"{file_type}s/{uuid.uuid4().hex}_{original_file_name}"
            
            blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=blob_name)

            with open(file_path, "rb") as data:
                blob_client.upload_blob(data, 
                                        content_settings=ContentSettings(content_type=content_type), 
                                        overwrite=True)

            blob_url = (
                f"https://{self.blob_service_client.account_name}.blob.core.windows.net/"
                f"{self.container_name}/{blob_name}"
            )
            
            return {
                "blob_url": blob_url,
                "blob_id": blob_name,
                "file_name": original_file_name
            }
        except Exception as e:
            print(f"Azure Upload Error: {str(e)}")
            return None

    def get_blob(self, blob_id: str) -> bytes:
        """
        Retrieves the blob content from Azure Blob Storage.
        
        :param blob_id: The unique identifier of the blob.
        :return: The image content as bytes, or None if an error occurs.
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=blob_id)
            download_stream = blob_client.download_blob()
            return download_stream.readall()
        except Exception as e:
            print(f"Azure Download Error: {str(e)}")
            return None

    def delete_blob(self, blob_id: str) -> bool:
        """
        Deletes the specified blob from Azure Blob Storage.
        
        :param blob_id: The unique identifier (blob name) of the image.
        :return: True if deletion is successful, False otherwise.
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=blob_id)
            blob_client.delete_blob()
            return True
        except Exception as e:
            print(f"Azure Delete Error: {str(e)}")
            return False

