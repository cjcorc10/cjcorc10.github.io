# writer

# creds

# services

* 22 - ssh - OpenSSH 8.2p1 Ubuntu 4ubuntu0.2
* 80 - http - Apache httpd 2.4.41 - Ubuntu focal fox
    * writer.htb
* 139 & 445 - netbois & smb - smb 4.6.2

# smb

        Sharename       Type      Comment
        ---------       ----      -------
        print$          Disk      Printer Drivers
        writer2_project Disk
        IPC$            IPC       IPC Service (writer server (Samba, Ubuntu))

# http

/adminstrative page has sqli vulnerability:

## **sqlmap**

**sqlmap -u "http://writer.htb/administrative" --data "uname=test&password=test" --current-db**
returned: **'writer'**

**sqlmap -u "http://writer.htb/administrative" --data "uname=test&password=test" -D writer --tables**
returned: **site, stories, users**

**sqlmap -u "http://writer.htb/administrative" --data "uname=test&passowrd=test" -D writer -T users --dump**
returned: 

+----+------------------+--------+----------------------------------+----------+--------------+
| id | email            | status | password                         | username | date_created |
+----+------------------+--------+----------------------------------+----------+--------------+
| 1  | admin@writer.htb | Active | 118e48794631a9612484ca8b55f622d0 | admin    | NULL         |
+----+------------------+--------+----------------------------------+----------+--------------+

John was unable to crack the hash

This dbms includes a function that allows queries to get the contents of files so tomorow I am going to write a python script to request common linux lfi files to learn more about the system:

# python script

I wrote a python script in /scripts/ that uses the **LOAD_FILE()** function to get the contents of files. I found a good list of linux lfi files and iterated through the files with my python script and then had a directory full of files from the server on my local machine in /scripts/files/

# interesting files

There was one interesting file that was an **apache-sites-available conf file** that listed the directory of the application being servered by apache. This was in **/var/www/writer.htb/** and it was using the webservergatewayinterface file wsgi. Inside of this file the interface is defined for the webserver to serve the application. In this file it imported __init__.py from the app folder as the interface.

# __init__.py

The file was the driver for the web application as I like to call it. It defined the functions used for each url served by the application. There are db creds leaked in this file:
* **user='admin', password='ToughPasswordToCrack'**

There was also a vulnerable function used for addStory, where the user input is unsanitized when uploading an image with the image_url method in the POST request. This function passes the name of the file, which is defined by the user directly into an os.system call. The only requirement for a file to be uploaded is for .jpg to exist somewhere in the name. Steps to exploit:
* upload file with reverse shell command as filename
* include .jpg somewhere in the filename
* get rid of special characters by base64 encoding the payload
* upload the file with image and then image_url to run the command in os.system

After catching the reverse shell we are logged in as www-data.

# PE

I found another application in /var/www/ named **writer2_project**. Then inside of this applications directory was a settings.py file for the database with django. 
* djangouser:DjangoSuperPassword

Now we had access to the dev database of mysql and we were able to view the **auth_user** table and retreive the password hash for kyle and crack it with hashcat on pc:
* **pbkdf2_sha256$260000$wJO3ztk0fOlcbssnS1wJPD$bbTyCB8dYWMGYlz4dSArozTY7wcZCS7DV6l5dpuXM4A=:marcoantonio**

# PE pt. 2

Now we can login as Kyle 

Kyle has the user flag in his home directory:

**d460570cbe3931481930239f4e6446e2**

## MTA - **postfix**
Kyle is apart of the smb and filter groups. If we search for files owned by the filter group we see one that located in the /etc/postfix directory. Postfix is a open-source MAIL TRANSFER AGEN (MTA) that is used to send and receive emails. An MTA is responsible for delivering email messages between mail servers. When an email is sent, the senders client communicates with the MTA, which then routes the  message to reach the recipients mail server.

The file in the directory is disclaimer and this is a shell script that is being used as a filter for incoming mail. The filter is defined in master.cf:

**smtpd -o content_filter=dfilt:**
* this line is a configuration directive for the POSTFIX mail server. It's telling the smtp daemon to use a content filter for incoming mail. The content filter is **dfilt**, which is defined below

**flags=Rq user=john argv=/etc/postfix/disclaimer -f ${sender} -- ${recipient}**

* this specifies the command and its arguments to be executed wehn mail passes through the content filter. Since john is the user specified as the one that executes the content filter, we should be able to **inject a reverse shell into the shell script** and get access to the user John.
* this script is typically executed to add a disclaimer, but since its executed as the user john, we should be able to privEsc.

After we have a shell with john we can go copy his private key and use it to sign in with ssh to get a more stable shell.

# PE pt. 3 - getting ROOT

John is part of the Managers group and after searching for files belonging to that group we see that the **/etc/apt/apt.conf.d/** directory is owned by the managers group. This directory is used to store all the configuration snippets for apt. It is read and included whenever apt runs. We can see that apt is being run as a process by root at the moment, so this must be getting called frequently. 

**When a conf directory is writable by the user, we should google "/whatever/conf/path persistence" to learn about how we can get persistence if we control the dircetory.**

We can create a new file in the directory and it will be read and executed the next time apt is ran.
`` APT::Update::Pre-Invoke {"chmod 4777 /bin/bash"};``

This command will set the suid of bin/bash the next time that apt is called with root privs. Then from there we need to run ``bash -p`` to have persisitence as ROOT

Root flag: **98b37d7934ad5db7c06ac7031a7acf26**
