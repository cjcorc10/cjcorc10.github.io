# swagShop

# nmap scan


└─$ nmap -sC -sV -o nmap/initial.nmap $IP
Starting Nmap 7.93 ( https://nmap.org ) at 2023-03-12 19:37 EDT
Nmap scan report for 10.129.227.10
Host is up (0.049s latency).
Not shown: 998 closed tcp ports (conn-refused)
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.2p2 Ubuntu 4ubuntu2.8 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   2048 b6552bd24e8fa3817261379a12f624ec (RSA)
|   256 2e30007a92f0893059c17756ad51c0ba (ECDSA)
|_  256 4c50d5f270c5fdc4b2f0bc4220326434 (ED25519)
80/tcp open  http    Apache httpd 2.4.18 ((Ubuntu))
|_http-server-header: Apache/2.4.18 (Ubuntu)
|_http-title: Did not follow redirect to http://swagshop.htb/
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 10.50 seconds

2 ports open:

* 20 - ssh - ubuntu is being run on the server
* 80 - http - apache 2.4.18 point to xenial as the version of buntu.

# http

Since ssh has almost no attack surface we are going to enumerate the web server for potential vulnerabilites.
The web app is a storefront run on magento. 

-application run on php. (index.php)

I am going to manually spider the application while gobuster runs in the background.

*potential creds for root found in app/etc/local.xml:*
* root:fMVWh7bDHpgZkyfqQXreTjU9

Bottom of web app reveals that the version was created in 2014. And I found 3 CVE's for magento all from 2015.
One for sql injection, php file execution, and arbirtrary php code execution.

**CVE-2015-1397 
CVE-2015-1398
CVE-2015-1399**

# EXPLAINING THE EXPLOIT
Magento uses modules, which are directories that contain different peices of functionality. Each module contain **controllers**, which are PHP class files that define **actions**(public methods in that class).

Each incoming request is parsed to understand which **module, controller, and action** is being requested by the user. The **PATH_INFO** variable, which is the section of the URI following the requested script or file. For example in GET /index.php**/TEST/ME/HERE**. PATH_INFO="/TEST/ME/HERE"

This variable contains the requested model, controller, and action name in this format: 
> GET /index.php/**[MODULE_NAME]/[CONTROLLER_NAME]/[ACTION_NAME]**

The **dynamic controller** loading logic uses the algorithm:
1. Determine if [MODULE_NAME] exists in the modules white list.
2. If it exists, contstuct a class name in this format: Mage_[MODULE_NAME]\_[CONTROLLER_NAME]\_CONTROLLER
3. Find a class file by replacing \_'s with /'s and appending a .php extension
4. If the file is found, include it.

For example:

> GET /index.php/downloadable/file/ 

The following class is loaded:

> Mage_DOWNLOADABLE_FILEController

# CONTROLLED INJECTIONS
When an admin attempts to load a controller, the system appends the string 'Adminhtml' after the module name. So our previous example would look like:

> GET /index.php/**admin/**downloadable/file/

And the loaded class would be:

> Mage_Downloadable_Adminhtml_Downloadable_FileController
    * the module is repeated after the Adminhtml prefix.

Therefore ontop of the LFI we've discovered we can also bypass authentication by injecting Adminhtml_[MODULENAME] into the request like so:

> GET /index.php/downloadable/**Adminhtml_Downloadable_File/**

Which will return the same format as the admin requested class:

> Mage_Downloadable_Adminhtml_Downloadable_FileController

This weakness bypasses session management, because no credentials are checked, Magento's code will validate the session as admin only if the request contains the /admin/ prefix, and fails to detect the **controller injection**. 

## BEST FOOT 'FORWARDED'
Aparrently, some of the modules implement additional checks for priveleges, so this won't work on every module.
However, upon reviewing how the Authentication mechanism works, when a user is requesting to load an admin controller, as long as **'forwarded'** is includes as parameter of the request, the controller should not be changed. This means that we are able to use admin controllers so long as the modules themselves don't implement priv checks.

# MAGE: LEVEL 90
The controller Cms_Wysiwg in the Adminhtml module has only one action named **directive**, which loads an image using a given path.



# scripts

Luckily there are public scripts used to exploit this vulnerability. I downloaded the two scripts and had to do a lot of editing on the second one due to the way that python3 handles bytes and string concatenation. 

PE was very easy on this machine. 

# takeaway

* I think that I spent a little too much time in the weeds on this box, while I could have just understood what the xploit was doing like, sql, or directory traversal. This box almost took me 3 days. Thats why the writeup ended suddenly.

* I am still going to read the php blog ippsec recommended tho for php object deserialization attacks.
