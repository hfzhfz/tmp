create user
  * input username password
  * salt -> hash (salt + password)
  * insert users ....
login user
  * input username password
  * select password,id from users where username = $username
  * if match login else login fail
  * save user session with user id, username

upload
  * input image file
  * process tranform image into 3 sizes + original memory
  * persist data into s3 -> key x 4
  * insert into images (...) values (userId, k1,k2....)

display
  * input $userId
  * get keys for all images belong to $userId
    - select * from users u join images i on u.id = i.userId where u.id = $userId;
  * get image files from s3 by keys
  * return files to frontend
