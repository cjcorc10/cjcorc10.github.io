## TryHackMe - Daily Bugle

This room requires us to compromise a Joomla CMS account via SQLi, practice cracking hashes and escalate priveleges by taking advantage of yum.

### NMAP scan
![image](https://user-images.githubusercontent.com/79766677/187769052-9ba0538d-9b17-4e74-8d07-0a10eb65f2e2.png)

ports 22, 80, and 3306 are open.

22 - ssh

80 - Apache httpd 2.4.6, running Joomla

3306 - mysql

The output also tells us that the website is using Joomla CMS




### Gobuster scan
Since we know it's hosting a website we will use gobuster to enumerate

![image](https://user-images.githubusercontent.com/79766677/187802234-6df6d18e-22e0-477e-82a1-3fe4ab4ea8f2.png)




Going to /administrator we find the Joomla login page:

![image](https://user-images.githubusercontent.com/79766677/187802487-d4443e19-4efd-4dcf-936f-d6ab30005040.png)


Now we need to find a way to get the version of Joomla to check for any known vulnerabilities.


Going back to the gobuster scan we notice that some text files were found (README, LICENSE, and htacccess) and we can find the version of Joomla in the README.txt file.

### Exploiting Joomla 
After some research, I found a python script to exploit 3.7.0 on github.

The script returned account information for Super User jonah, including a password hash:

![image](https://user-images.githubusercontent.com/79766677/187804226-05589c47-60ff-4b7e-9a48-c30974f7adbc.png)

After about 10 minutes John cracks jonah's password and we get credentials to login to joomla.

