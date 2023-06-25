# blocky

creds:

root:8YsqfCTnvxAUeduzjNSXe22

## nmap scan

* 21 - ftp - proftpd 1.3.5a
* 22 - ssh - OpenSSH 7.2p1 Ubuntu 4ubuntu2.2
* 80 - 80 http - Apache httpd 2.4.18
* 8192 - sophos - Sophos is a comprehensive cybersecurity suite that protects endpoints, networks and cloud environments.


# ftp

* anonymous login not supported

# http


/.php                 (Status: 403) [Size: 289]
/index.php            (Status: 301) [Size: 0] [--> http://blocky.htb/]                  *empty*
/wiki                 (Status: 301) [Size: 307] [--> http://blocky.htb/wiki/]           front of the site
/wp-content           (Status: 301) [Size: 313] [--> http://blocky.htb/wp-content/]     *empty*
/wp-login.php         (Status: 200) [Size: 2397]                                        wp login
/plugins              (Status: 301) [Size: 310] [--> http://blocky.htb/plugins/]        stores all plugins used to extend the functionality of the wp site.
/license.txt          (Status: 200) [Size: 19935]                                       wp license
/wp-includes          (Status: 301) [Size: 314] [--> http://blocky.htb/wp-includes/]    /wp-includes contains the core wp files essential to the functioing of the site.
/javascript           (Status: 301) [Size: 313] [--> http://blocky.htb/javascript/]     *403*
/wp-trackback.php     (Status: 200) [Size: 135]                                         *nonstandard* xml formatted response
/wp-admin             (Status: 301) [Size: 311] [--> http://blocky.htb/wp-admin/]       reroute to wp-login to authenticate
/phpmyadmin           (Status: 301) [Size: 313] [--> http://blocky.htb/phpmyadmin/]     phpmyadmin login screen


From the directories enumerated I know that wp-login has an authentication vuln where its mishandling errors and reporting to the user that specifically the username is incorrect. So I am going to brute force that until I get a username.

We are going to run **wpscan** on this site to enumerate users. (also a new tool)

Nothing was found in the scan, but using the common author parameter on wordpresses index.php main page, we found a username **notch**. With this username and the password found earlier in the java file we are able to connect with ssh and then PE is 2ez with sudo all:all priveleges all that was needed was **sudo su** and we were ROOT.!


**BUT** this was a little too easy and ipp took a harder way, so i wanted to also. If we acted like this PE didn't exist and instead looked for another way we could...

Going to the /var/www/html directory, because thats where the website is being hosted and having a look at the config file for wp will give us another set of credentials for the db that is being hosted on the server. We know that phpmyadmin is a url path on the machine and this service is used to manage a mysql database that wordpress uses to maintain/authenticate its users. 

So we find the password in the config file in the root directory of the website, login to phpmyadmin, and then replace the password of the user notch with a newly crafted hashed password. 

```php
echo password_hash('reddish', PASSWORD_DEFAULT);
$2y$10$KhXRUJkhycVAbu9t0ZMNGeoWKf15EpUlpDu6Z9w4JvRRXQasWX7q2
```
Now that we know the password we are able to login to the wp-login portal and edit the website. We can insert a php reverse shell into the theme of this website and now we are logged on with www-data.



## plugins

One of the .jar archives contained a username and password for root.

I didn't know this but .class java files can be decompiled and viewed in java with jd-gui. This is a great tool so that now we don't have tot view .class files as binaries.


