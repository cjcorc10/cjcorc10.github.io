# scriptKiddie

# services

```bash
└─# nmap -sC -sV -o nmap/initial $IP
Starting Nmap 7.93 ( https://nmap.org ) at 2023-06-01 18:59 EDT
Nmap scan report for 10.129.95.150
Host is up (0.049s latency).
Not shown: 998 closed tcp ports (reset)
PORT     STATE SERVICE VERSION
22/tcp   open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.1 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   3072 3c656bc2dfb99d627427a7b8a9d3252c (RSA)
|   256 b9a1785d3c1b25e03cef678d71d3a3ec (ECDSA)
|_  256 8bcf4182c6acef9180377cc94511e843 (ED25519)
5000/tcp open  http    Werkzeug httpd 0.16.1 (Python 3.8.5)
|_http-title: k1d'5 h4ck3r t00l5
|_http-server-header: Werkzeug/0.16.1 Python/3.8.5
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 9.49 seconds
```
only 2 ports are open on this device:
* 22 - ssh - Ubuntu, focal
* 5000 - httpd - Werkzeug
    * Werkzeug is WSGI web application library typically used with Flask


### http

The website had 3 main functions:
* nmap scan
* msvenom payload generator
* searchsploit searcher

All three of these functions are likely invoking the binaries on the cmd line and we are able to find a vulnerability in msfvenom. This vulnerability CVE 2020-7384 should be pretty straight forward however I could not get the python script to work from exploitdb and metasploit could not encode the payload. Unfortunately I hit a wall and will have to come back to this machine...
