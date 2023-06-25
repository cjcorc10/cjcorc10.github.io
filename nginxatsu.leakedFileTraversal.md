# nginxatsu

This web application creates nginx config files based on input from users.

# Web enumeration

Request an index.php file from the application and there is a comment inside that reveals the /storage directory on the server. /storage holds all the crafted index files and a backup file: v1_db_backup_1604123342.tar.gz

Inside of this backup files the db type is revealed to be sqlite v3. Looks like possibly usernames with hashes are also leaked. Also several db statements are leaked in this file that must have been made to create the db.


me0wthnginxatsu     me0wth@makelarid.esfe30ac62a73059c49f1946a998dafb51pxshScUrK8vDTzsfGfrxsNFABltD4Y8C7ZH5J9f0TSiiAhzfRRNtXUQMT6j1U3RjGP9B

Giovann1nginxatsu   giv@makelarid.es535829606e10fdbeb9b64f9089499a7aVxecX953b2mmn2koUIDaKxE7A0qoqFQoIGtWX5qfMC98lRGzYkxZYdrjDxkhFJB2B3Lk

jrnginxatsu         adm-01@makelarid.ese7816e9a10590b1e33b87ec2fa65e6cdvyKTms6YOrZIRdc8FdcRWE4t58umCuUMQoQqOUbcc8qLe9vtp7sAIOHEy1lztXfDRhvQ


makelarid.es is a CTF website.

All of the potential creds are base64 encoded, but after decoding I don't recognize what they could be.


# sqli?

Have a feeling that the main login page may be vulnerable to sqli. It is not..


# backup file

download the backup file and use sqlite3 to query the tables stored in the file and we are given the same information as above, but this time we can see how the tables were created and which string in the entry is the password.

**Passwords**

* e7816e9a10590b1e33b87ec2fa65e6cd

* 535829606e10fdbeb9b64f9089499a7a

* fe30ac62a73059c49f1946a998dafb51

The other values after the passwords are the api tokens of the users.

Now that the passwords are separated from the api tokens JOHN is able to start cracking.
Since I wasn't sure the format of how john liked the hashes, I just separated the hashes by themselves.

**I had to use a hash identifier because John was using the wrong hash algo to crack** it was actually md5 and after specifying this algo a hash was quickly cracked.

* me0wth:adminadmin1


# Takeaways

In this box I almost made it all the way without looking at a writeup. The mistake I made was giving up too early on the credentials that I did find and plus I never downloaded the file that I found. After downloading the file and being given the dbms it was trivial to find the password for one of the admins. 

I need to work on slowing down and finishing my though process. Sometimes I feel myself rushing to try and speed run a box, however that is the opposite of what needs to be done. I must be methodical in my approach and thouroughly think out the paths for exploiting the target.
