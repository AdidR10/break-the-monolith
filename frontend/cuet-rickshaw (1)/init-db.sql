-- Initialize CUET Rickshaw Database

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS cuet_rickshaw;

-- Use the database
\c cuet_rickshaw;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    user_type VARCHAR(20) NOT NULL CHECK (user_type IN ('STUDENT', 'RICKSHAW_DRIVER')),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Student profiles table
CREATE TABLE IF NOT EXISTS student_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    student_id VARCHAR(20) UNIQUE NOT NULL,
    department VARCHAR(100),
    batch VARCHAR(10),
    year INTEGER,
    total_rides INTEGER DEFAULT 0,
    is_verified BOOLEAN DEFAULT false,
    emergency_contact VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Rickshaw profiles table
CREATE TABLE IF NOT EXISTS rickshaw_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    rickshaw_number VARCHAR(20) UNIQUE NOT NULL,
    license_number VARCHAR(50),
    is_available BOOLEAN DEFAULT true,
    current_location VARCHAR(255),
    current_latitude DECIMAL(10, 8),
    current_longitude DECIMAL(11, 8),
    total_rides INTEGER DEFAULT 0,
    rating DECIMAL(3, 2) DEFAULT 0.00,
    rating_count INTEGER DEFAULT 0,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Locations table
CREATE TABLE IF NOT EXISTS locations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    address TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Wallets table
CREATE TABLE IF NOT EXISTS wallets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    balance DECIMAL(10, 2) DEFAULT 0.00,
    currency VARCHAR(3) DEFAULT 'BDT',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default locations
INSERT INTO locations (name, latitude, longitude, address) VALUES
('CUET Main Gate', 22.4625, 91.9689, 'CUET Main Gate, Chittagong'),
('CUET Library', 22.4635, 91.9695, 'CUET Central Library'),
('CUET Cafeteria', 22.4640, 91.9700, 'CUET Student Cafeteria'),
('CUET Residential Area', 22.4620, 91.9680, 'CUET Student Residential Area'),
('CUET Academic Building', 22.4630, 91.9690, 'CUET Academic Complex'),
('Chittagong Medical College', 22.3569, 91.7832, 'Chittagong Medical College Hospital'),
('GEC More', 22.3792, 91.8159, 'GEC Circle, Chittagong'),
('Agrabad Commercial Area', 22.3384, 91.8317, 'Agrabad Commercial Area'),
('New Market', 22.3384, 91.8317, 'New Market, Chittagong'),
('Chittagong Railway Station', 22.3569, 91.7832, 'Chittagong Railway Station');

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);
CREATE INDEX IF NOT EXISTS idx_users_type ON users(user_type);
CREATE INDEX IF NOT EXISTS idx_student_profiles_user_id ON student_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_rickshaw_profiles_user_id ON rickshaw_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_rickshaw_profiles_available ON rickshaw_profiles(is_available);
CREATE INDEX IF NOT EXISTS idx_locations_active ON locations(is_active);
CREATE INDEX IF NOT EXISTS idx_wallets_user_id ON wallets(user_id);
