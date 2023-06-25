# shocker

# nmap scan


└─$ nmap -sC -sV -o nmap/initial.nmap 10.10.10.56
Starting Nmap 7.93 ( https://nmap.org ) at 2023-03-07 21:01 EST
Nmap scan report for 10.10.10.56
Host is up (0.048s latency).
Not shown: 998 closed tcp ports (conn-refused)
PORT     STATE SERVICE VERSION
80/tcp   open  http    Apache httpd 2.4.18 ((Ubuntu))
| http-server-header: Apache/2.4.18 (Ubuntu)
| http-title: Site doesn't have a title (text/html).
2222/tcp open  ssh     OpenSSH 7.2p2 Ubuntu 4ubuntu2.2 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   2048 c4f8ade8f80477decf150d630a187e49 (RSA)
|   256 228fb197bf0f1708fc7e2c8fe9773a48 (ECDSA)
|   256 e6ac27a3b5a9f1123c34a55d5beb3de9 (ED25519)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 9.86 seconds


2 ports returned open:

* 80 - appache httpd 2.4.18 - web server  (box so old ubuntu doesn't list package info for apache type)

* 2222 - OpenSSH 7.2p2 Ubuntu 4ubuntu2.2 


# http

The home page is a picture of a bug that says "Don't bug me!". There is no functionality to this path. I had gobuster running and was at 30% when I decided to look at a walkthrough, because I had exhausted all other options. I discovered that there is a forbidden directory cgi-bin/. Since my gobuster would have eventually found it anyway I don't feel too bad about it. 

I decided to run gobuster on the directory cgi-bin since I didn't have permissions to view the files in the directory I could test to see if the access control is broken and the victim misconfigured the file permissions.

**user.sh** file was found in /cgi-bin

since the file was a shell file located inside of cgi-bin, which is where scripts are stored and permitted to run or execute after receiving a request from a user. These should not be public facing directories. 

This one was actually not public but the .sh script was reachable. Since the script is in bash, we will run nmap with the shellshock script to test for the shelshock vuln and its **vulnerable**

# shellshock

Shellshock is a rce vulnerability found in bash back in 2014. Legit functions are defined in environment variables and then when another bash shell is spawned by the same process, the child process inherits the parents environment variables and that runs our defined function.
 
example:

```bash
x='() { :;}; echo vuln' bash -c "echo test"

#returns:

    vuln
    test
```

The function defined is calling **echo vuln** and is placed in the **x** environment variable. Then when bash is called to execute the command **echo test** the bash environment variables are loaded and the function in x is called.


# exploiting

In our box we have the file user.sh. When requesting the file we are able to view the output of the file and since its in the cgi-bin directory we know that its executing there. So we need to create environment variables with shellshock functions. So how do we accomplish this? **HEADERS**

When requests are sent to the server and cgi-bin scripts are run the server is going to load information about the request into the environment for the bash script to use if needed. That means that if we place shellshock functions into our http request headers the server will load the values into environment variables, which will in turn be loaded by the child bash process called by the server. Executing the functions and giving us the results in the response.

the nmap script tested for the vulnerability, but I had to manually exploit it, because the rfc for HTTP 1.1 there must be an empty line in between the headers of the packet and the data returned and the script was not sending an echo before the payload. 

# privEsc

After gaining an initial foothold in the system, privesc was trivial as the user had sudo permissions for perl, so I could either run

```perl
    sudo /usr/bin/perl -e 'exec("/bin/bash")'
```

or use a reverse shell.
