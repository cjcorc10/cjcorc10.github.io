# tabby

# creds

# services

* 22 - ssh
* 80 - http - Apache httpd 2.4.41
* 8008 - http - Apache tomcat


# http

**port 80**
The web server is running a generic bootstrap web page with not much functionality. However there is a lfi vulnerability in the parameter file. The lfi cannot be escalated to rce, because the calling function simply gets the contents of the file, it does not execute the file. But we can use this to read well known system files or configuration files of other running services. There appears to be 0 sanitization on the parameter.

# tomcat
**port 8080**
Port 8080 is running tomcat and the index page reveals information about the configuration and version of the tomcat running. In order to access the manager directory in tomcat, we need to authenticate as a user within the manager group. In tomcat all users and their privileges are stored in the **tomcat-users.xml** file. 

So with a working LFI and a target file, we just need to probe the system for tomcat-users.xml

# LFI 

In the welcome page on port 8080 its disclosed that this tomcat is configured with **CATALINA_HOME**, which is located at **/usr/share/tomcat9**. And the tomcat users file is stored in **/etc/tomcat-users.xml**, so if we concatenate these paths we get the path to the file. **/usr/share/tomcat9/etc/tomcat-users.xml**

This file reveals the credentials to the tomcat user and we can know authenticate as a user with priveleges to deploy applications within Tomcat, **but wait!** this tomcat is configured so that only user physically present (requests coming from the server) can deploy applications. Ippsec showed that sometimes a tomcat proxy could be present, however this was not ran on this box. 

# deploying tomcat .war files from the command line

You can deploy web apps with tomcat through the web interface provided in /manager/html or by the command line with the endpoint /manager/text/deploy. For this machine, only a user issuing requests from the server is able to access /manager/html, so we had to issue a curl request to **manager/text/deploy** in order to deploy our web app. Tomcat uses .war archives in order to deploy web apps, so all thats needed is a malicious jsp file zipped into a war archive and then we'll upload it via curl.

```bash
curl -u your_username:your_password -T path/to/your/webapp.war "http://IP:8080/manager/text/deploy?path=/yourAppPath&update=true"
```
Now we can navigate to /yourAppPath on port 8080 and have access to our malicious application. From there we have RCE and are able to execute a reverse shell

## reverse shell

For some reason this machine was unable to execute a reverse shell directly from memory, so we needed to upload a reverse shell script to disk and then run the script to get a reverse shell.

# PE

Backup archiv found within /var/www/html. This archive is password protected so we transfer it to attack machine and attempt to crack the password with zip2john -> john. **to transfer to our machine we base encoded the contents of the archive then copied to attack machine and decoded**. John successfully cracked the password on physical os **admin@it**. 

We cracked the archive however there wasn't anything interesting inside. **BUT** we did get a password and hopefully one of the users on the box re-used their password for the archive encryption. And as it turns out the password used for the archive was the same as for the user ash. Now to root.

ash user is apart of the lxd group, so this is an easy path to root. 

on hacktricks.xyz there is a tutorial for setting up a container with a lightweight alpine image. Then setting up this image in a container with root priveleges and mounting the root filesystem to the container. From there you start/execute the image and then navigate to /mnt/root for root priveleges on the original file system.
