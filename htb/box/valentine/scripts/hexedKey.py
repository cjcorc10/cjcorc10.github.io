#!/usr/bin/python3
import sys


fileName = sys.argv[1]
#open the local file with hex key
with open(fileName, "r") as file:
    file_contents = file.read()

#decode files from hex
decoded_file = bytes.fromhex(file_contents)
#decode the bytes as ascii
decoded_ascii_string = decoded_file.decode('ascii')

#write the decoded file to a file
with open("outputKey", "w") as outFile:
    outFile.write(decoded_ascii_string)
