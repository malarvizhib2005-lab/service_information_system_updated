import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv("DB_NAME", "service_db")


def get_connection():
    """Create and return a MySQL connection using environment settings."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "malar@2005"),
        database=DB_NAME,
    )


def ensure_database_schema():
    """Create the database and make sure required serviceInfo columns exist."""
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "malar@2005"),
        autocommit=True,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            cur.execute(f"USE `{DB_NAME}`")
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS serviceInfo (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(128) NOT NULL,
                    email VARCHAR(128),
                    customerID INT UNSIGNED,
                    companyName VARCHAR(191),
                    customerManual TINYINT(1) NOT NULL DEFAULT 0,
                    phoneNumber VARCHAR(128),
                    productID VARCHAR(128),
                    productType VARCHAR(128),
                    issueDescription TEXT,
                    locationID INT,
                    locationName VARCHAR(128),
                    religionName VARCHAR(128),
                    regionID INT,
                    regionName VARCHAR(128),
                    issueImages TEXT,
                    requestTime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    reqIpAddr VARCHAR(128),
                    subcategoryID INT,
                    subcategoryName VARCHAR(255),
                    status VARCHAR(64) NOT NULL DEFAULT 'RECEIVED',
                    userID INT,
                    remarks TEXT,
                    createdAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    closedAt DATETIME NULL,
                    isReopened TINYINT(1) NOT NULL DEFAULT 0,
                    tatTargetDays INT NOT NULL DEFAULT 7
                )
                """
            )
            cur.execute("SHOW COLUMNS FROM serviceInfo LIKE 'religionName'")
            if not cur.fetchone():
                cur.execute("ALTER TABLE serviceInfo ADD COLUMN religionName VARCHAR(128) AFTER locationName")
    finally:
        conn.close()
