# luanne

# services

* 22 - ssh OpenBSD
* 80 - http nginx
* 9001 - httpd medusa 1.12

# http

Both of the http servers require authentication to access and admin/admin types are failing. 
**robots.txt** does give us a hint that /weather is working on port 80 despite it returning 400.

After looking up default creds for the only type of info we've been able to gather **medusa default creds**, we see an example of defualt creds in the official docs. 
**user:123**

The application is an interface for a process supervisor with limitied functionality.
    * view running processes
    * view memory
    * view uptime

Running processes gives us some information as to what is currently running on the server and we see that another httpd is currrenlty listening on port 3000 and its listed as WEATHER
``
/usr/libexec/httpd -u -X -s -i 127.0.0.1 -I 3001 -L weather /home/r.michaels/devel/webapi/weather.lua -P /var/run/httpd_devel.pid -U r.michaels -b /home/r.michaels/devel/www
``

This must be reachable at /weather on port 80.

# fuzzing /weather

robots.txt disclosed that /weather was listening despite returning 400, so we run gobuster and find **forecast**, which responds with information about paramters to provide. **"No city specified. Use 'city=list' to list available cities."** This parameter allows us to view the forecast for a provided city.

Now to fuzz this endpoint with hopes of injecting native code.

Fuzzing with /usr/share/wordlists/SecList/Fuzzing/special-chars.txt, returns a different response for '. We know this is endpoint is ran on lua, so the comment is --.
With '-- we still aren't able to get normal performance from the request, so we FUZZ again, between the single quote and comment:

``$ ffuf -u http://10.129.121.240/weather/forecast?city=\'FUZZ-- -w /usr/share/wordlists/SecList/Fuzzing/special-chars.txt``

This returns ')', which makes sense because our input is likely being passed to a function like forecast('input')
Now we use the syntax in lua to run bash commands.

``GET /weather/forecast?city=')os.execute("echo+hi")--`` returns a reflected response 'hi'

Now that we have rce, we can send a reverse shell with sh.

