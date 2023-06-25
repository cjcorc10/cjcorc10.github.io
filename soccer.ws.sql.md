# soccer

## nmap scan


└─$ nmap -sC -sV -o nmap/initial.nmap 10.10.11.194
Starting Nmap 7.93 ( https://nmap.org ) at 2023-03-05 02:08 EST
Nmap scan report for 10.10.11.194
Host is up (0.051s latency).
Not shown: 997 closed tcp ports (conn-refused)
PORT     STATE SERVICE         VERSION
22/tcp   open  ssh             OpenSSH 8.2p1 Ubuntu 4ubuntu0.5 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   3072 ad0d84a3fdcc98a478fef94915dae16d (RSA)
|   256 dfd6a39f68269dfc7c6a0c29e961f00c (ECDSA)
|   256 5797565def793c2fcbdb35fff17c615c (ED25519)
80/tcp   open  http            nginx 1.18.0 (Ubuntu)
| http-server-header: nginx/1.18.0 (Ubuntu)
| http-title: Did not follow redirect to http://soccer.htb/
9091/tcp open  xmltec-xmlmail?
| fingerprint-strings:
|   DNSStatusRequestTCP, DNSVersionBindReqTCP, Help, RPCCheck, SSLSessionReq, drda, informix:
|     HTTP/1.1 400 Bad Request
|     Connection: close

3 ports are showing as open from default scan:

22 - ssh

80 - http nginx 1.18.0 

9091 - unknown, but looks to do with xml.

# http

There is not obvious functionality on the webiste from manual enumeration. No clickable items or other paths.
NO cookies.

* running burp...
    * /tiny - H3K Tiny file manager login. Created by CCP Programmers. Link provided to github/docs and **defualt creds worked for admin access**
        admin:admin@123


Inside of tiny file manager we are able to manage our file *duuhh* and hooray we can upload files!! This file manager is ran on php, so I'm gonna try a php reverse shell... tomaro

The php reverse shell was successfully uploaded to /tiny/uploads and we were able to run it to connect to the machine as www-data.

# enumeration

**Issue**
----------
OS - Ubuntu 20.04.5


**Release**
-----------

DISTRIB ID=Ubuntu
DISTRIB RELEASE=20.04
DISTRIB CODENAME=focal
DISTRIB DESCRIPTION="Ubuntu 20.04.5 LTS"
NAME="Ubuntu"
VERSION="20.04.5 LTS (Focal Fossa)"
ID=ubuntu
ID LIKE=debian
PRETTY NAME="Ubuntu 20.04.5 LTS"
VERSION ID="20.04"
HOME URL="https://www.ubuntu.com/"
SUPPORT URL="https://help.ubuntu.com/"
BUG REPORT URL="https://bugs.launchpad.net/ubuntu/"
PRIVACY POLICY URL="https://www.ubuntu.com/legal/terms-and-policies/privacy-policy"
VERSION CODENAME=focal
UBUNTU CODENAME=focal

**System information**
-----------------------
Linux soccer 5.4.0-135-generic #152-Ubuntu SMP Wed Nov 23 20:19:22 UTC 2022 x86 64 x86 64 x86 64 GNU/Linux


**NO** suid files

**NO** sudo -l for user www-data, since we don't have pass


After glancing at a writeup I realized that I overlooked the nginx server files!! In available-sites we can see the URL paths that nginx will respond to. Here we see a subdomain for soccer.htb as soc-player.soccer.htb.

# soc-player.soccer.htb

On this path there are functions to login, signup, and view the match. Upon signing up you are given a cookie by the server **connect.sid**. But it's not relevant to the vulne


```javascript
       var ws = new WebSocket("ws://soc-player.soccer.htb:9091");
        window.onload = function () {
        
        var btn = document.getElementById('btn');
        var input = document.getElementById('id');
        
        ws.onopen = function (e) {
            console.log('connected to the server')
        }
```
* This snippet is ran on the client side to check if the ticket id is valid or exists.
* A socket is created with the server at port 9091, which we saw as open in the nmap scan. 
* It then gets the btn and id values from the DoM and assigns it to the variables. 
    * id is the input we provide in the id field.

```javascript
function keyOne(e) {
            e.stopPropagation();
            if (e.keyCode === 13) {
                e.preventDefault();
                sendText();
            }
        }
```

* this snippet is a listener for the 'enter' key
* if the enter key is pressed e.stopPropagation stops the event from propagating to other elements in the DOM.
* Th enter keycode is 13, so if enter is pressed, then preventDefualt stops the default behaviour of the enter key
* sendText is defined later on...

```javascript
       function sendText() {
            var msg = input.value;
            if (msg.length > 0) {
                ws.send(JSON.stringify({
                    "id": msg
                }))
            }
```
If the input is greater than 0 we send the input to to the socket as a JSON-formatted string {"id": value}, otherwise ???????? (not included) is appended to the p query, which is the field that reflects the response from the server.

```javascript
       ws.onmessage = function (e) {
        append(e.data)
        }
        
        function append(msg) {
        let p = document.querySelector("p");
        // let randomColor = '#' + Math.floor(Math.random() * 16777215).toString(16);
        // p.style.color = randomColor;
        p.textContent = msg
        }
```
* sets up event listener for ws socket, so that when a message is received from the server it is appended with append()
* append selects the first element in the document that matches "p" and appends msg to it.

**So overall this client side script is taking user input in id and searching if the ticket exists. Then it either returns that it does or does not exist. We know from earlier enumeration that the server is also running mysql, so it's likely querying the db for the ticket id.**

# socket-based blind sqli

Since this vulnerability is blind I will opt to go for the tool sqlmap, otherwise it could be very time consuming. I found a project online that included an application vulnerable to the same blind socket sqli. https://rayhan0x01.github.io/ctf/2021/04/02/blind-sqli-over-websocket-automation.html

I cloned his repo and booted it up in docker for testing and observed how differently sockets communicate from http. It allows asynchronous communication where both sides can send data at the same time and each letter typed is sent throught the socket. However, it differs in the soccer app, because of the js script.

## git project

In the git project there was a vulnerable application and he provided code for an http middleware of sorts. Whereby we will be running a python http server and sending the sqlmap input through it. The python script will then query the application with websockets. This is because sqlmap cannot currently query through ws.

# sqlmap

After running sqlmap with the http middleware configured to attach to the soccer application we were able to extract valuable information.

**sqlmap -u "http://localhost/?id=1"**
    This determined that the socket was vulnerable to timebased sqli, the version of dbms, and the vulnerable query.

**sqlmap -u "http://localhost/?id=1" --currentdb**
    This dropped the the db: **soccer_db**

**sqlmap -u "http://localhost/?id=1" -D soccer_db --tables**
    This dropped the table: **accounts**

**sqlmap -u "http://localhost/?id=1" -D soccer_db -T accounts --dump**
    This dumped the contents of the table accounts:

* columns:
    * id
    * email
    * username
    * password

**Creds**
----------
+------+-------------------+----------------------+----------+
| id   | email             | password             | username |
+------+-------------------+----------------------+----------+
| 1324 | player@player.htb | PlayerOftheMatch2022 | player   |
+------+-------------------+----------------------+----------+

These creds allow us to ssh into the server as player and retreive the user.txt flag.
**68110e37412c48816b160cb98d3f9a51**

# privesc

I couldn't find anything with manual enumeration, but thats to be mostly expected, since I had already performed similar tests earlier as www-data. I was frustrated with this box and didn't want to upload linpeas (like wtf? lazy..) so I peaked at the walkthrough again and read about the vulnerability with player being in doas.conf file.
 
doas is basically sudo -l. A user is inserted into the doas.conf file with the commands that they are permitted to run as root. IN this instance a user was allowed to run dstat as root and after scanning the man pages I learned that dstat allowed plugins. These plugins had to follow a dstat naming convention and exist in either /usr/share/dstat or /usr/local/share/dstat dir.

# dstat

All of the dstat plugins were written in python, which meant all I needed to do was replace the plugin with either a call to su root or a reverse shell. I opted for the reverse shell and placed the dstat_reverse.py file in /usr/locl/share/dstat. Then ran dstat with doas and included the plugin to execute the shell and catch the escalated shell.

doas /usr/bin/dstat --reverse


# takeaway

I feel I did decent on this box up until the end. I just wanted to be done and I don't know why because that takes away from **my** learning experience. I need to not resort back to writeups as often when I'm not reading them before the box is done. Or just read writeups and then complete the box, so I'm familiar and can learn as I go. I feel I cheat myselft when I peak and just know the answer. But other than the end I have a few takeaways about things I learned.

* always check server/application files!
    * I knew that the application was running on an nginx server, but I overlooked checking for subdomains or other application paths there.

* I feel good about the js client side analysis and I need to remember to always check that out, because It could reveal some functionality of the application that isn't obvious.

* **SLOW DOWN**. I was patient for most of this box, but started rushing at the end so that I could move onto the next box, but that not the way learning is done. *b r e a t h e* okay, now read the docs, enumerate, and ask questions!
