## TryHackMe - Relevant

This room is meant to be a simulation of a black box penetration test.

### Nmap scan

![image](https://user-images.githubusercontent.com/79766677/188251758-a5b9f7bc-4037-401c-ac8f-2db7ef123d3d.png)

The machine is running Microsoft IIS httpd 10.0 on server 80 and has smb running on port 45. It's a windows machine so we can remote in if we get credentials.


### SMB

Listing the shares with smbclient and we see the share netw4ksrv. This share is accessible with no password and we see a passwords file stored in the share.

![image](https://user-images.githubusercontent.com/79766677/188251863-77e4e11c-51a7-403d-90f0-16611a2333f4.png)


It's base64 encoded, but after decoding we get a pair of credentials:

![image](https://user-images.githubusercontent.com/79766677/188251907-0bfd4db2-922d-4fb8-9e0a-9ae4839d8cfc.png)

