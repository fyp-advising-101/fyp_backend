from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

class AzureKeyVault:
    def __init__(self, vault_url="https://advising101vault.vault.azure.net"):
        self.vault_url = vault_url
        self.credential = DefaultAzureCredential()
        self.client = SecretClient(vault_url=self.vault_url, credential=self.credential)

    def get_secret(self, secret_name: str) -> str:
        """
        Retrieve a secret from the Azure Key Vault.

        :param secret_name: The name of the secret to retrieve.
        :return: The value of the secret.
        """
        secret_bundle = self.client.get_secret(secret_name)
        return secret_bundle.value

