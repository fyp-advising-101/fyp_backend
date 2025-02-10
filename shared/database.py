from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Fetch the database connection URL from the environment variables
VAULT_URL = "https://advising101vault.vault.azure.net"
credential = DefaultAzureCredential()
client = SecretClient(vault_url=VAULT_URL, credential=credential)
mysql_password = client.get_secret("DB-PASSWORD").value
ssl_cert = client.get_secret("DigiCert-CA-Cert").value
cert = "-----BEGIN CERTIFICATE-----\n" + '\n'.join([ssl_cert[i:i+64] for i in range(0, len(ssl_cert), 64)]) + "\n-----END CERTIFICATE-----"
os.makedirs('tmp', exist_ok=True)
cert_path = "./tmp/DigiCertGlobalRootCA.crt.pem"
with open(cert_path, "w") as f:
    f.write(cert)
DATABASE_URL = f'mysql+pymysql://advisor:{mysql_password}@mysqladvising101.mysql.database.azure.com:3306/fyp_db?ssl_ca={cert_path}'

# Create a SQLAlchemy engine instance to manage the connection to the database
# The `echo=True` parameter enables logging of SQL queries for debugging purposes
engine = create_engine(DATABASE_URL, echo=True)

# Create a session factory bound to the database engine
# - `autocommit=False`: Disables automatic commit of transactions, giving more control over database operations.
# - `autoflush=False`: Disables automatic flushing of changes to the database to avoid unexpected behaviors.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
