import pexpect
import sys
import time

vib= sys.argv[1]
host_esx= sys.argv[2]
esx_pwd=sys.argv[3]
print "Copying vib to esx host"
command="scp /root/%s root@%s:/tmp"%(vib,host_esx)
try:

       #	print "hiiii"
	print command
	child = pexpect.spawn(command)
	child.logfile = sys.stdout
	#i = child.expect(["\(yes\/no\)","Password:")])
	i = child.expect (["\(yes\/no\)", pexpect.EOF, pexpect.TIMEOUT])
	print i
	time.sleep(10)
	if i == 0:
		#print "hi"	
		#child.expect("\(yes\/no\)")
		#child.before
		child.sendline ("yes")
		time.sleep(5)
		child.before
		
	child.expect("Password:")
	time.sleep(5)
	child.sendline (esx_pwd)
	time.sleep(10)
	child.expect(pexpect.EOF)
	child.logfile = sys.stdout
except:
	print "copying is failed "

