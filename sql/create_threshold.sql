CREATE DATABASE cloudWatch;
USE cloudWatch;

CREATE TABLE workers
(
  id int NOT NULL,
  grow_ratio int NOT NULL,
  shrink_ratio int NOT NULL,
  grow_threshold int NOT NULL,
  shrink_threshold int NOT NULL,
  PRIMARY KEY (id)
);

