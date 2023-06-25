# valentine

# services

* 22 - ssh

* 80 - http

* 443 - https


# http

The web application displays an image on the front page. enumerating directories lead to several places of interest:
* /encode - base64 encodes data
* /decode - base64 decodes data
* /dev - includes a hex encoded, encrypted private key and notes hinting at a flaw with the encode functionality on the site.

# rsa priv key

A rsa private key is extracted from the /dev directory and after decoding it, it appears to be encoded with a passphrase. Running john with ssh2john and it doesn't appear to be making any progress on cracking the passphrase. 

I need to take a look at the functionality of the encoding provided on the web application, since the notes mentioned that needed fixing.(**XXS VULN**)

This vulnerability lead to nothing. The iframe did not work, because the server does not store anything, **but it does have memory**.

This server is vulnerable to the heartbleed exploit, which uses the heartbeat mechanism in ssl to ask for more memory than sent and the server leaks memory to the user.

This exploit has several python scripts to choose from and they all perform the heartbeat and specify the string was much longer than the actual request. This causes the server to leak the memory and we can search it for recent data passed to the server.

# PE

The privEsc for this box is a running tmux process that is attached to a socket. The socket is owned by the user root and the group hype. Our user is in the hype group, so we just need to attach a tmux session to the socket and we will have **ROOT**
