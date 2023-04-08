# mirai

# services

* 22 - ssh
* 80 - http
* 53 - dns

# initial http

When making a web request to the provided url we are returned a blank page. But if we look at the headers of the response we see that we are communicating with a pi-hole, which is usually used to block requests to blacklisted ad websites. So I tried changing the host header and we do start to receive a response. The response states that the host is blocked. But it also returns a hostname where its getting a js script from.

Since I know that dns is open on the machine I can query it for the hostname provided by the response **pi.hole**. This query returns a local ip address that the machine must use to communicate with the host. 



# dns request

dig @ip pi.hole



; <<>> DiG 9.18.11-2-Debian <<>> @10.129.237.52 pi.hole
; (1 server found)
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 43948
;; flags: qr aa rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1

;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags:; udp: 4096
;; QUESTION SECTION:
;pi.hole.                       IN      A

;; ANSWER SECTION:
pi.hole.                300     IN      A       192.168.204.129

;; Query time: 52 msec
;; SERVER: 10.129.237.52#53(10.129.237.52) (UDP)
;; WHEN: Sat Mar 25 15:32:00 EDT 2023
;; MSG SIZE  rcvd: 52


This response returns the local ip **192.168.204.129** we don't have any way of querying that ip, since its local, but we can change our host header to pi.hole.

# http host header

The host header in the http web request tells the server which host to serve to. When the server receives a request with the host as **pi.hole** it forwards the request to **/admin** url. This url returns the web application for pi-hole. I am able to dirbust and find some other .php files on the server, but authentication is required first. 
* default passwords don't work
    * with pi-hole a random password is assigned upon creation

* password field is not vulnerable to sqli

**I reached this part of the box alone, but I ran out of attack surface and needed help**, luckily IPpsec had a walkthrough!

We know that these services are being run on a raspberry pi, since the pi-hole web application. So we can use the **default SSH credentials** and we can logon as pi.

# ssh

privEsc is very easy since pi has all sudo priv, but we need to do a little forensics to retreive the root flag.

# FORENSICS with GREP

The root flag was on the attached usb, which we can view with **lsblk or mount**(so long as its mounted). lsblk will list the storage devices and the location fo the their mountpoint.

Looking on the usb at /media/usbstick/ we see that the file has been deleted from the USB stick and are tasked with recovering its contents.

To do this we will display the bytes on the storage device with xxd and can use grep to filter the results. Or we can use dd to copy the contents of the usb stick to a file and move the file locally so that installed tools can be used. THe latter isn't necessary as we know the format of the flag is alphanumeric undercase 32 bytes long. We will still create a file copy tho, because its important to reserve the original data in forensics.

Our commands:

* dd if=/dev/sdb of=usb.dd
* grep -ar '[a-z,0-9]\{32\}' usb.dd
    * a flag is used for using grep with binary data and r is regex
    * regex pattern is a 32 byte string with lowercase alphanumeric characters

This returns our the root flag.

