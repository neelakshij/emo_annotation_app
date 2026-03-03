-- Create tables for Images, Users, Annotations:

CREATE TABLE images (
  image_id SERIAL PRIMARY KEY,
  file_path TEXT NOT NULL UNIQUE,
  filename TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- users table uses unique token per user
CREATE TABLE users (
  user_id SERIAL PRIMARY KEY,
  user_name VARCHAR(100) UNIQUE NOT NULL,
  user_token VARCHAR(36) UNIQUE NOT NULL,
  last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE annotations (
  annotation_id SERIAL PRIMARY KEY,
  image_id INTEGER NOT NULL REFERENCES images(image_id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  emotion_label VARCHAR(50) NOT NULL,
  remark TEXT,
  annotated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);    
