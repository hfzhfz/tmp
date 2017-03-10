CREATE DATABASE webimage;
USE webimage;

CREATE TABLE users
(
  id int NOT NULL AUTO_INCREMENT,
  username varchar(255) NOT NULL UNIQUE,
  salt varchar(32),
  password varchar(64),
  PRIMARY KEY (id)
);

ALTER TABLE `users` ADD INDEX (username);

CREATE TABLE images(
  imageId int NOT NULL AUTO_INCREMENT,
  userId int NOT NULL,
  key1 varchar(255),
  key2 varchar(255),
  key3 varchar(255),
  key4 varchar(255),
  PRIMARY KEY(imageId),
  FOREIGN KEY(userId) REFERENCES users(id)
);
