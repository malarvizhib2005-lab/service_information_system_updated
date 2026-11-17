CREATE DATABASE IF NOT EXISTS service_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE service_db;

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
);

-- Optional sample records for testing
INSERT INTO serviceInfo
(name, email, phoneNumber, companyName, productID, productType,
 issueDescription, locationName, religionName, regionName, status, remarks, tatTargetDays)
VALUES
('Mahalabala Krishna', 'krishna@example.com', '9876543210', 'Example Ltd',
 'PRD-101', 'Hardware', 'Device is not powering on', 'Bangalore', 'Hindu',
 'South', 'CLOSED', 'Resolved and verified', 7),
('Nandha Kumar', 'nandha@example.com', '9876501234', 'Demo Company',
 'PRD-102', 'Software', 'Application login issue', 'Chennai', 'Christian',
 'South', 'WIP', 'Troubleshooting in progress', 7);
