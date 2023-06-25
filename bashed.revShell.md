# bashed

# nmap scan


└─$ nmap -sC -sV -o nmap/initial.nmap $IP
Starting Nmap 7.93 ( https://nmap.org ) at 2023-03-08 18:33 EST
Nmap scan report for 10.10.10.68
Host is up (0.052s latency).
Not shown: 999 closed tcp ports (conn-refused)
PORT   STATE SERVICE VERSION
80/tcp open  http    Apache httpd 2.4.18 ((Ubuntu))
| http-title: Arrexel's Development Site
| http-server-header: Apache/2.4.18 (Ubuntu)

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 9.65 seconds

1 port is returned from the nmap scan:

* 80 - apache httpd 2.4.18 - this is likely zenial, which is the same distro as the Shocker box. We know this because of the version of httpd

# http

Web application provides us a github repo with a phpbash shell that takes user input and executes it in a bash shell, then dies. I watched ippsec complete this box 2 weeks ago, so none of this is completely new to me, but I will still do my due diligence and enumerate directories.

## gobuster


└─$ ~/go/bin/gobuster dir -u http://$IP -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -x php,sh,py

===============================================================
Gobuster v3.4
by OJ Reeves (@TheColonial) & Christian Mehlmauer (@firefart)
===============================================================
[+] Url:                     http://10.10.10.68
[+] Method:                  GET
[+] Threads:                 10
[+] Wordlist:                /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt
[+] Negative Status codes:   404
[+] User Agent:              gobuster/3.4
[+] Extensions:              php,sh,py
[+] Timeout:                 10s
===============================================================
2023/03/08 18:44:29 Starting gobuster in directory enumeration mode
===============================================================
/.php                 (Status: 403) [Size: 290]
/images               (Status: 301) [Size: 311] [--> http://10.10.10.68/images/]
/uploads              (Status: 301) [Size: 312] [--> http://10.10.10.68/uploads/]
/php                  (Status: 301) [Size: 308] [--> http://10.10.10.68/php/]
/css                  (Status: 301) [Size: 308] [--> http://10.10.10.68/css/]
/dev                  (Status: 301) [Size: 308] [--> http://10.10.10.68/dev/]
/js                   (Status: 301) [Size: 307] [--> http://10.10.10.68/js/]
/config.php           (Status: 200) [Size: 0]
/fonts                (Status: 301) [Size: 310] [--> http://10.10.10.68/fonts/]
/.php                 (Status: 403) [Size: 290]


Gobuster returned several directories of interest, but /dev contained the phpbash script that was provided in the github repo by the welcome page. This means we have the sourcecode that the server is executing if we need it. My first reverse shell attempt was a python on and it took immediately. I know that ippsec did a few shells before it took. Believe nohup may have been an option to detach...


# privesc

Privesc was interesting on this machine because www-data was permitted to run sudo commands as scriptmanager.

**sudo -u scriptmanager**

I was using a reverse shell to catch as scriptmanager, but I could have just called a shell and I would have had a persistent shell as scriptmanager.

There was a directory /scripts that was owned by scriptmanager and a file was being modified every minute inside. I assumed this was a cronjob being run by root, since the file being modified was owned by root. And the other file in scripts was a python script writing text to the root file.

The python script was being executed by root every minute and writing to the other text file so all I needed to do was change the python script to instead execute a reverse shell and catch it to gain root priv.


# takeaways

* not very challenging, since I watched it 2 weeks ago and its very easy

* I need to spend more time enumerating once I have gotten an initial foothold to learn more about the sytem. While it wasn't necessary for an easy box like this it is good practice and will be needed for more difficult boxes in the future.
