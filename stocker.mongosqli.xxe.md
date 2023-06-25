# stocker

# nmap scan


└─$ nmap -sC -sV -o nmap/initial.nmap $IP
Starting Nmap 7.93 ( https://nmap.org ) at 2023-03-08 21:57 EST
Nmap scan report for 10.10.11.196
Host is up (0.048s latency).
Not shown: 998 closed tcp ports (conn-refused)
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.5 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   3072 3d12971d86bc161683608f4f06e6d54e (RSA)
|   256 7c4d1a7868ce1200df491037f9ad174f (ECDSA)
|   256 dd978050a5bacd7d55e827ed28fdaa3b (ED25519)
80/tcp open  http    nginx 1.18.0 (Ubuntu)
| http-title: Did not follow redirect to http://stocker.htb
| http-server-header: nginx/1.18.0 (Ubuntu)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 9.18 seconds


2 ports returned as open from initial nmap scan:

* 22 ssh - leaked version of package OpenSSH 8.2p1 as 4ubuntu0.5, this can give us some clues about the age of the system or if the system has been kept up to date. According to launchpad this was release in march 2022, so its a year old.

* 80 http - nginx 1.18.0 was released apr 2020.
    * add stocker.htb to /etc/hosts

# http 

There is no functionality on the web app, so I attempted to enumerate directories and there was nothing of interest. Then I figured that there had to be a subdomain and I tried using gobuster, which kept returning 0 subdomains.

## FFuF

FFuf did return the subdomain **dev**

```bash
ffuf -w /usr/share/wordlists/SecList/Discovery/DNS/subdomains-top1million-110000.txt  -u http://stocker.htb -H "Host: FUZZ.stocker.htb"
```
I didn't realize that this is the way to bruteforce subdomains. By using the Host header we search for subdomains...




# dev.stocker.htb

Placeholder for username is jsmith

Inside of dev.stocker.htb the username has a placeholder jsmith, which I think is just a rabbit hole, because I was stuck on bruteforcing passwords for an hour at least. But, after nothing was returned I decided to check a writeup and it looks like the page is vulnerable to nosqli.

I tested sql initially with special characters and noticed all the characters '=;/ were being encoded, so I assumed that it wasn't vulnerable. **However** I am unfamiliar with nsoql syntax and how it accepts JSON as input. So here we go...

NoSQL (not only sql) is a new concept of data storage which is non-relational. NoSQL offers a new data model and query formats make the old SQL injection attacks irrelevant. There are now databases and collections when querying for data the format looks like so:

```nosql

    db.users.find(
        { age: { $gt: 18} },
        { name: 1, address: 1}
    ).limit(5)
```
This selects the database db, collections users, and executes the find method on the collection with query object. MongoDB expects input in JSON array format and has query operators:

* $ne - *not equal*
* $gt - *greater than*
* $regex - *regular expression*
* $where - *clause that lets you specify a script to filter results*

The following json form injection will query username that is not equal to null and password not equal to null.

```json
{"username": {"$ne": null}, "password": {"$ne": null}}
```

**I need to be on the lookout for sql injection ESPECIALLY IN AUTHENTICATION MECHANISMS LIKE LOGIN forms. I got too caught up in the placeholder and was stuck on that**

The injection example above actually worked on this website as well. All that was needed to be changed is the Content-type header to application/json and then inject the example.

# /stock

This directory of the web application has ecommerce functionality where you add items to your cart (all with client side js btw) and then submit your order with /api/order. The order is submitted **in json** and then the application creates a receipt based on the items purchased and returns the **order id**

**order id** is used to fetch the receipt from **/api/po**. 

From here we can see the items ordered reflected with the total price.

I messed around with the prices of the items in the request and noticed it allowed the prices to go negative, so I inferred that there was almost no input sanitization. It didn't occur to me that this could be injected with html for xss. I discovered this in the writeup. But it does make sense.

The name of the product can be changed to any arbitrary value. The document is likely being crafted form html, so it is vulnerable to xss. **iframe** tag can be used to reference other documents inside of HTML. So this can be used for LFI!!

# xss/ssrf/lfi

By injecting an iframe with a well known file path such as /etc/passwd, we can get the server to search for the file and then include it in the html document. 

## exploit 

I did some work with xxs, so I understand the concept, but iframes are new to me. iframe is a type of tag that specifies an inline frame, which embeds another document into the html. 

```html
<iframe src=file:///etc/passwd></iframe>
```
This embedded the the /etc/passwd file into the receipt and now we had a working lfi to enumerate the machine. Some formatting was required since the inline frame was quite small, but attributes height and width can be used to fix that.


```html
<iframe src=file:///etc/passwd width=500px height=1500px></iframe>
```

The /etc/passwd wasn't of much use to us, but we did learn that angoose's shell is /bin/bash, so we want to find that accounts credentials.

## lfi 

Other files of interest are always going to be in the /var/www/ directory because this is our web app environment and often credentials could be stored in backend files. angooses creds were found in the js driver file index.js.

**angoose:IHeardPassphrasesArePrettySecure**


user flag: efd30288a96f39f6c3a96924a093ea25

# privEsc

angoose has sudo privelge with the command **/usr/bin/node /usr/local/scripts/*.js***

With node sudo priv we are allowd to run any arbitrary js file. This is because node is used to run .js files in the node.js environment (aka outside the browser).

So we can run any js file with this because the wildcard is used in the command. This allows us to traverse directories to go to a directory that we actually have write permissions. So I created a reverse shell in js in the /tmp directoyr and caught it with nc.

**sudo /usr/bin/node /usr/local/scripts/../../../tmp/reverse.js**

root flag: 5bc08b30cea4bd0065f2aa6f98f20f35


# takeaways

* got stuck bruteforcing passwords for way too long because of placeholder
* moved on from broken authentication mechanism in sqli way too quickly (submitted a few special chars)
* overlooked xss in HTML doc generation
* overlooked purpose of node. * wilcard includes directories, I thought that it had to be included in same dir


