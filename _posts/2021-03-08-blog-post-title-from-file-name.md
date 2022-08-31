## TryHackMe - Daily Bugle

This room requires us to compromise a Joomla CMS account via SQLi, practice cracking hashes and escalate priveleges by taking advantage of yum.

### NMAP scan
![image](https://user-images.githubusercontent.com/79766677/187769052-9ba0538d-9b17-4e74-8d07-0a10eb65f2e2.png)

ports 22, 80, and 3306 are open.

22 - ssh

80 - Apache httpd 2.4.6

3306 - mariadb with mysql

The output also tells us that the website is using Joomla CMS


#### Some T-SQL Code

```tsql
SELECT This, [Is], A, Code, Block -- Using SSMS style syntax highlighting
    , REVERSE('abc')
FROM dbo.SomeTable s
    CROSS JOIN dbo.OtherTable o;
```

#### Some PowerShell Code

```powershell
Write-Host "This is a powershell Code block";

# There are many other languages you can use, but the style has to be loaded first

ForEach ($thing in $things) {
    Write-Output "It highlights it using the GitHub style"
}
```
