# friendZone

* nmap returned:
    * http
    * https
    * smb shares
    * ftp
    * ssh
    * dns

# smb

Admin creds were found on the smb\\$IP\general share, but they didn't work for ssh, ftp, or smb.
admin:WORKWORKHhallelujah@#  

# dns
**dig axfr** is a query used to request a dns zone transfer. This returns all of the dns domains associated with the provided domains in the command:
    **dig axfr @IP domainName**

This command returned many subdomains of interest and I added them all to the /etc/hosts file and used the new tool aquatone to get a quick overview of many websites. *Cool new tool*

# http/https

There are many sites returned from the zone transfer request, so I will need to attempt to enumerate the interesting ones.


# ftp

nada

# PE

user flag: 3f7ec29356d81bb66be161320e4986fc

* www-data has no sudo permissions.
* there are no interesting binaries with SUID set.

* db creds found in /var/www:
    * friend:Agpyu12!0.213$
    * db_name=FZ

**These creds worked to change to the friend user!!**

After uploading and running linPeas, I found a python script in /opt/server-run and saw that friend had write priveleges on the python os module. 

The script in /opt/server-run was part of a crontab being run by root and it imported os, so all I needed to do was write a python reverse script in the os module and the cronjob would call it when it imported the library/module??

And I got **root**!

root flag: f39a02e309c2d2126a6b6257ecfd0502
