#!/usr/bin/python
import pexpect
import sys
import time
import os
type ="update"
iso = sys.argv[1]
ip=sys.argv[2]
ip1=ip+":"
pwd=sys.argv[3]


image= "/opt/ft/sbin/ft-install " + iso +"  -n"
print image
try:
        child = pexpect.spawn(image)
        child.logfile = sys.stdout
        time.sleep(100)
        child.logfile = sys.stdout
        child.expect (ip1)
        child.sendline (pwd)
        child.logfile = sys.stdout
        child.expect ("\[Y\/n\]:")
        child.sendline ("Y")
        child.logfile = sys.stdout
        time.sleep(15)
        child.expect ("\[Y\/n\]:")
        child.sendline ("Y")
        time.sleep(250)
        child.logfile = sys.stdout
        child.expect ("\[Y\/n\]:")
        child.sendline ("n")
        child.logfile = sys.stdout
        print "installation passsed\n"
        #time.sleep(60)
except:
        print "installation Failed"
