# frolic

## services

nmap scan:
```bash
─$ nmap -sC -sV -o nmap/initial.nmap $IP
Starting Nmap 7.93 ( https://nmap.org ) at 2023-04-20 18:12 EDT
Nmap scan report for 10.129.253.151
Host is up (0.049s latency).
Not shown: 996 closed tcp ports (conn-refused)
PORT     STATE SERVICE     VERSION
22/tcp   open  ssh         OpenSSH 7.2p2 Ubuntu 4ubuntu2.4 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   2048 877b912a0f11b6571ecb9f77cf35e221 (RSA)
|   256 b79b06ddc25e284478411e677d1eb762 (ECDSA)
|   256 21cf166d82a430c3c69cd738bab502b0 (ED25519)
139/tcp  open  netbios-ssn Samba smbd 3.X - 4.X (workgroup: WORKGROUP)
445/tcp  open  netbios-ssn Samba smbd 4.3.11-Ubuntu (workgroup: WORKGROUP)
9999/tcp open  http        nginx 1.10.3 (Ubuntu)
| http-server-header: nginx/1.10.3 (Ubuntu)
| http-title: Welcome to nginx!
Service Info: Host: FROLIC; OS: Linux; CPE: cpe:/o:linux:linux kernel

Host script results:
| clock-skew: mean: -1h49m59s, deviation: 3h10m31s, median: 0s
| nbstat: NetBIOS name: FROLIC, NetBIOS user: <unknown>, NetBIOS MAC: 000000000000 (Xerox)
| smb2-time:
|   date: 2023-04-20T22:13:02
|   start date: N/A
| smb2-security-mode:
|   311:
|     Message signing enabled but not required
| smb-security-mode:
|   account used: guest
|   authentication level: user
|   challenge response: supported
|   message signing: disabled (dangerous, but default)
| smb-os-discovery:
|   OS: Windows 6.1 (Samba 4.3.11-Ubuntu)
|   Computer name: frolic
|   NetBIOS computer name: FROLIC\x00
|   Domain name: \x00
|   FQDN: frolic
|   System time: 2023-04-21T03:43:02+05:30

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 14.74 seconds
```

ports:

* 22 - ssh - likely Ubuntu Xenial
* 139 & 445 - samba 4.3.11 
* 9999 - http - nginx 1.10.3


## smb

```bash
$ smbclient -L //$IP                     
Password for [WORKGROUP\kali]:

        Sharename       Type      Comment
        ---------       ----      -------
        print$          Disk      Printer Drivers
        IPC$            IPC       IPC Service (frolic server (Samba, Ubuntu))
Reconnecting with SMB1 for workgroup listing.

        Server               Comment
        ---------            -------

        Workgroup            Master
        ---------            -------
        WORKGROUP            FROLIC
```

No shares of interest found in smb enumeration

## http

### port 9999
> credentials revealed at /backup/username.txt and /backup/password.txt
**admin:imnothuman**

However these creds don't work on either login form

at /admin when the page is requested a login.js page is also sent which validates the login attempt client-side. This is very dumb, it just gives you the creds
**admin:superduperlooperpassword_lol**
This authentication is irrelevant as it can be passed by simply providing the file name.
After "authenticating" we are returned with a page that consists of !,?, and .'s. No recognizable pattern here.


There is a lot of ctf decoding/decrypting done on the admin/success.html file. I looked past it, but apparently it was encodedin Ook, which I'd never heard of. From there it is base64 decoded and then a zip file is decrypted. Then yet another decoding, but this time it's in brainfuck. Finally we get a password **idkwhatispass**

**found /playsms** mention at /dev/backup and the credentials are admin:idkwhatispass
### port 1880
http server reveals another open port at port 1880 and hostname forlic.htb. So we add forlic.htb:1880 to /etc/hosts and navigate there.
After finding this open port I ran another nmap scan on all ports and 1880 is responding and showing as open.

This port is hosting the application Node-RED


**FINISHED** however I stopped taking notes due to the tedious ctf challenges...
