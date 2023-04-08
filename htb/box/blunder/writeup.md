# blunder

# services

* 21 - ftp 

* 80 - http - apache httpd 2.4.41 Ubuntu **focal**

# ftp 

Attempting to connect to ftp results in 'connection refused'


# http

This website uses BLUDIT CMS from 2019. I have found a vulnerability in this version of BLUDIT, where the bruteforce prevention can be bypassed by manipulating the X-Forwarded-For header in the request. The application uses this field to determine the number of failed attempts.

**found username in todo.txt file**
* **fergus**

There are several scripts available online, but I want to improve my python scripting skills, so I am going to write a brute force script that changes the X-Forwarded-For header in each request.

Used **cewl** to gather a wordlist for bruteforcing and then the script successfully got the password.

creds:

**fergus:RolandDeschain**



# creds


hugo:Password120

user: f77e33a1f7abd2e12c13ee0687979a5b
root: 9278fb65e632b011cf445b6e1be23fb9
