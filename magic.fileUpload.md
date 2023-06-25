# magic

# services

* 22 - ssh
* 80 - http 

# http

file upload vulnerability is present on upload.php and to get to this page we bypassed the login.php authentication with sqli.

The file upload vulnerability required changing the magic numbers and the extension of the file. 
    * attempted to copy paste the beginning of a successfull upload, but it wasn't reading as pdf, so I had to concatenate the first few bytes of jpeg file and a reverse shell script.

# PE

With our initial foothold as www-data we can see the **db.php5** file in side of the **/var/www/Magic/** directory and this file has the dbname, username, and dbpassword:

  **private static $dbName = 'Magic' ;
    private static $dbHost = 'localhost' ;
    private static $dbUsername = 'theseus';
    private static $dbUserPassword = 'iamkingtheseus';**

With the creds for the mysql server we can use this with mysqldump to get the contents of the db. mysql client is not installed on the system, thats why we used mysqldump:

  **INSERT INTO `login` VALUES (1,'admin','Th3s3usW4sK1ng');**

This query was leaked and now we have another password.



545a2e5a167a1241b63963e41a7269d4
31fdfdf018486172117f00c18c4633dc
