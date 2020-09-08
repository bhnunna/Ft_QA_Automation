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
	time.sleep(10)
        child.sendline ("             ")
	i = child.expect(['\(yes\/no\)', 'option:'],timeout=20) 
	if i == 0:
		child.sendline ("yes")
		child.logfile = sys.stdout
        time.sleep(5)
        child.sendline ("3")
        child.logfile = sys.stdout
        child.expect ('machine\[\]:')
        child.sendline (ip)
        child.logfile = sys.stdout
        child.expect (ip1)
        child.sendline (pwd)
        child.logfile = sys.stdout
        time.sleep(60)
        child.expect ("\[Y\/n\]:")
        child.sendline ("Y")
        child.logfile = sys.stdout
        time.sleep(10)
        child.expect ("\[Y\/n\]:")
        child.sendline ("Y")
        child.logfile = sys.stdout
        time.sleep(20)
        print child.before
        child.expect ("\[Y\/n\]:")
        child.sendline ("Y")
        print child.before
        time.sleep(60)
        child.logfile = sys.stdout
        print child.before
        child.expect ("\[Y\/n\]:")
        child.sendline ("n")
        time.sleep(30)
        c="shutdown --reboot 0 ; exit"
        print c
        os.system(c)
        time.sleep(5)
        print child.before
        print "installation passsed"
        #time.sleep(60)
except:
        print "installation Failed"
