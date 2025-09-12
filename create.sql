CREATE DATABASE hotelmatch;
USE hotelmatch;

CREATE TABLE hotels (
    countyCode VARCHAR(10),
    countyName VARCHAR(100),
    cityCode VARCHAR(20),
    cityName VARCHAR(100),
    HotelCode VARCHAR(50) PRIMARY KEY,
    HotelName VARCHAR(255),
    HotelRating VARCHAR(50),
    Address TEXT,
    Attractions TEXT,
    Description TEXT,
    FaxNumber VARCHAR(50),
    HotelFacilities TEXT,
    Map TEXT,
    PhoneNumber VARCHAR(50),
    PinCode VARCHAR(20),
    HotelWebsiteUrl TEXT
);

USE hotelmatch;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

USE hotelmatch;

CREATE TABLE favorites (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    HotelCode VARCHAR(50) NOT NULL
);
USE hotelmatch;

CREATE TABLE user_profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    phone VARCHAR(20),
    address VARCHAR(100),
    city VARCHAR(50),
    country VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
