# Agile Write-Up

## Services

### Nmap Scan

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

The Nmap scan report revealed two open ports:
- SSH (22/tcp) running OpenSSH 8.9p1 Ubuntu 3ubuntu0.1
- HTTP (80/tcp) running Nginx 1.18.0 (Ubuntu)

### Discovered Services

* SSH (Port 22) - Reveals Jammy OS according to Launchpad
* HTTP (Port 80) - Nginx 1.18.0 - URL **superpass.htb**

## HTTP Analysis

The server frequently loses connection to the database and returns an error message with the query. The query does not seem to be injectable as it uses parameterized variables.
But we are able to create an account on the site and from the /download page another error is returned. It is verbose and reveals the expected parameter of the request.
```python
with open(f'/tmp/{fn}', 'rb') as f:
```
So, the web page /download expects the parameter `?fn=filename` to read a file from. And it's vulnerable to **path traversal** as we can retrieve the `/etc/passwd` file without having to bypass any filters.

### Path Traversal Findings

The `/etc/passwd` file reveals several users of interest:

```bash
dev_admin:x:1003:1003::/home/dev_admin:/bin/bash
edwards:x:1002:1002::/home/edwards:/bin/bash
corum:x:1000:1000:corum:/home/corum:/bin/bash
runner:x:1001:1001::/app/app-testing/:/bin/sh
```
Unfortunately, attempts to grab files from the users in the `/home` directory fail with a "permission denied" error.

### Werkzeug Debugger

The error page returned is a debugger that contains a shell environment for code execution! This is the Werkzeug debugger that works with Flask. This debugger includes a shell environment where we can issue shell commands in Python, but it's protected by a PIN. Fortunately, with our **Local File Inclusion (LFI)** vulnerability, we can retrieve all the information that goes into creating the PIN.

## Privilege Escalation - www-data

Credentials were found in `/app/config_prod.json`: `superpassuser:dSA6l7q*yIVs$39Ml6ywvgK`. These credentials can be used to connect to the MySQL database `superpass`.

```bash
(venv) www-data@agile:/app$ mysql -u superpassuser -p superpass
```

Inside the `superpass` database, there is a `passwords` table:
```mysql
mysql> SELECT * FROM passwords;
```
This table contains plaintext passwords, and the `agile` password for `corum` successfully authenticates to SSH.

## Privilege Escalation - corum

After running `linpeas`, a process was highlighted for further investigation:

```bash
runner     41171  0.1  2.6 34023392 10428 ?       Sl   08:40   0:03 /opt/google/chrome/chrome --no-sandbox --headless --disable-dev-shm-usage --disable-software-rasterizer --disable-background-timer-throttling --disable-breakpad --disable-client-side-phishing-detection --disable-cloud-import --disable-default-apps --disable-extensions --disable-gpu --disable-hang-monitor --disable-popup-blocking --disable-prompt-on-repost --disable-sync --enable-automation --enable-blink-features=ShadowDOMV0 --enable-logging --headless --log-level=0 --no-first-run --no-service-autorun --password-store=basic --remote-debugging-port=41829 --test-type=webdriver --use-mock-keychain --user-data-dir=/tmp/.com.google.Chrome.Zakvlz --window-size=1420,1080 data:,
```

The **--remote-debugging-port** option allows us to connect to the debugging session at localhost:41829. Since we don't have a display in the SSH connection, we will need to use port forwarding from our local machine and open up Chrome from there.

```bash
└─$ ssh -fN -L 9998:localhost:41829 corum@superpass.htb                                                             
```

Next, we configure Network Targets in Chrome, inspect the remote host, and retrieve additional credentials: `edwards:d07867c6267dcb5df0af`.

## Privilege Escalation - edwards

Immediately, we check for sudo privileges with edwards and find two commands, both using `sudoedit`:

```bash
edwards@agile:~$ sudo -l
```

This version of `sudo` on the box is vulnerable to CVE-2023-22809, a vulnerability that allows users to declare a separate file to edit while using `sudoedit`. As long as the user that we are editing a file with (in this case it's `dev_admin`) has permission to the file, we can edit it.

We added the command `chmod u+s /bin/bash` to the `activate` script. Now, we just need to wait for the `test_and_update.sh` script to run. This is why the box is called Agile - because the application is frequently being deployed.

At the end of this, we achieve root access

