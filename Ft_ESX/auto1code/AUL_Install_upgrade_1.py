import paramiko
import re
import os
import time
import logging
import configparser


host="134.111.87.198"
user="root"
pw="syseng"
#host_esx="192.168.61.56"
#host_esx_pw="syseng01"
port = 22

logging.basicConfig(level=logging.INFO)
my_files = "my_files"
vib_script="vib_copy.py"
aul_script="AUL.py"
AUL_Upgrade1="AUL_Upgrade12.py"
esx_post_install="esx_install.py"
esx_postinstall="esx_postinstall.pl"

config = configparser.ConfigParser()
config.read('c:\\auto\\BasicConfig.txt')
section=config.sections()

input_dir=config [section[0]]['Project_dir']
input_subdir=config [section[0]]['Build_dir']
app=config [section[0]]['App_IP']
app_pwd=config [section[0]]['app_pwd']
host_esx=config [section[0]]['Host_esx_IP']
host_esx_pw=config [section[0]]['host_esx_pw']

transport = paramiko.Transport((host, port))
transport.connect(username = user, password = pw)
sftp = paramiko.SFTPClient.from_transport(transport)

def uplaod_file(file,dest_file):
    transport = paramiko.Transport((app, port))
    #logging.info (app,app_pwd)
    transport.connect(username = user, password = app_pwd)
    sftp = paramiko.SFTPClient.from_transport(transport)
    try:
        sftp.put(file,dest_file,callback=None)
        logging.info ("upload is completed")
    except:
            logging.info ("uplaod is Failed")
            exit


def download_file(file,dest_file):
    try:
        sftp.get(file,dest_file,callback=None)
        logging.info ("download is completed")
    except:
        logging.info ("download is Failed")
        exit()


def ssh_connection(host,user,pw,command):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=pw)
    stdin, stdout, stderr = ssh.exec_command(command)
    #return str(stdout.readlines()).strip("\n")
    return stdout.read().decode('ascii').strip("\n")
    #return str(stdout.readlines()).decode('ascii').strip("\n")


def set_up():
	dest_file = "C:\\auto\\{}".format(my_files)
	#logging.info ("uploading the setup tools  {}".format(my_files))
	upload_loation="/root/{}".format(my_files)
	logging.info (uplaod_file(dest_file,upload_loation))

	logging.info ("untar the my_files ")
	command ="tar -xvf {}".format(my_files)
	logging.info (ssh_connection(app,user,app_pwd,command))
	logging.info ("installing the setup tools ")
	time.sleep(5)
	command="python /root/setuptools-41.0.1/setup.py install"
	logging.info (command)
	logging.info (ssh_connection(app,user,app_pwd,command))
	logging.info ("untar the PIP ")
	time.sleep(20)
	command ="tar -xvf pip-19.1.1.tar.gz"
	logging.info (ssh_connection(app,user,app_pwd,command))
	logging.info ("installing the  PIP ")
	command="cd /root/pip-19.1.1/; python setup.py install"
	logging.info (ssh_connection(app,user,app_pwd,command))
	time.sleep(10)
	logging.info ("installing pexpect")
	command="pip install pexpect"
	logging.info (command)
	logging.info (ssh_connection(app,user,app_pwd,command))
	time.sleep(10)
	command = "pip show  pexpect"
	pdata=ssh_connection(app,user,app_pwd,command)
	if "Version:" in str(pdata):
            logging.info ("prerequisite are met now other things execute:")
	else:
            logging.info ("prerequisite are not met please check")
            exit()

def remove_tar():
	command="rm -rf my_files pip-19.1.1.tar.gz pip-19.1.1 setuptools-41.0.1 "
	logging.info (ssh_connection(app,user,app_pwd,command))



def get_file_vib(files):
	for file1 in files:
            m=re.search(r".*.vib",file1)
            if m:
                vib=m.group()
            m=re.search(r"ftSys_for_ESX.*iso",file1)
    	
            if m:
                file=file1
	return vib,file





def verify_piviot():
    time.sleep(300)
    command="ping -n 1 {}".format((app))
    while True:
        data = os.system(command)
        d=str(data).split(" ")
        logging.info (d)
        if not int(d[0]):
            logging.info ("System UP")
            break
        time.sleep(200)
        logging.info ("System is Pivoting ... not UP will ping after 5 min")

def set_sync_speed():
    logging.info ("set syncing speed of esx ")
    command ="esxcli storage mpm speedLimit  --min=500000 --max=500000"
    logging.info(ssh_connection(host_esx,user,host_esx_pw,command))
    logging.info("ESX sync speed set min:500000 max: 500000 ")
    command="esxcli storage mpm speedLimit"
    logging.info(ssh_connection(host_esx,user,host_esx_pw,command))


def check_sync_status():
    while True:
        command="esxcli storage mpm list"
        data=ssh_connection(host_esx,user,host_esx_pw,command)
        sync=re.search(r"\w+=\d+\.\d+",str(data))
        finish=re.search(r"\w+=\d+\.\dmin",str(data))
        m =re.findall(r"\[\s\w+_?\w+\s\]",str(data))
        if not  "[ syncing ]" in m:
            logging.info ("all disk are synced")
            break
        time.sleep(300)
        logging.info ("Disk are  {0} & {1} please wait after few min will check again".format(sync.group(),finish.group()))
    time.sleep(120)
    logging.info ("Disk are synced now going to appliacne to check duplex state")


def duplex_state():
    logging.info ("running ft-verify coomad pleas wait for output")
    data=ssh_connection(app,user,app_pwd,"/opt/ft/sbin/ft-verify -D")
    time.sleep(60)
    logging.info (data)
    time.sleep(60)
    app_version=re.search(r"\(.*\)",str(data))
    logging.info ("Appliance versiom installed {}".format(app_version.group()))
    app_version1=app_version.group()
    duplex_state=re.search(r"ftServer CRUs duplexed(\s+)(\[\w+\])",str(data))
    if '[PASS]' in duplex_state.group(2):
        duplex_state1="system are duplexed"
        
    else:
        logging.info ("system are not  duplexed some issues")
        exit
    host_esx_pw    return app_version1,duplex_state1
    

def AUL_install():
    set_up()
    remove_tar()
    source_file = "/test1/Aeries_New/ftESX/{0}/{1}".format(input_dir,input_subdir)
    files = sftp.listdir(source_file)
    vib,file=get_file_vib(files)
    source_file = "/test1/Aeries_New/ftESX/{0}/{1}/{2}".format(input_dir,input_subdir,file)
    dest_file = "C:\\auto\\{}".format(file)
    logging.info ("downloading the iso file")
    download_file(source_file,dest_file)
    upload_loation="/root/{}".format(file)
    logging.info ("uploading the iso file")
    uplaod_file(dest_file,upload_loation)
    AUL_file = "C:\\auto\\{}".format(aul_script)
    upload_loation="/root/{}".format(aul_script)
    logging.info ("uploading the Appliance Script")
    uplaod_file(AUL_file,upload_loation)
    logging.info ("Executing AUL script")
    command="python /root/{0} {1} {2} {3}".format(aul_script,file,host_esx,host_esx_pw)
    logging.info ("Installing AUL Please wait.... ....")
    data1=ssh_connection(app,user,app_pwd,command)
    logging.info (data1)
    time.sleep(10)
    m=re.search(r"reboot",str(data1))
    if m.group() == "reboot":
        logging.info ("AUL installed rebooting the applaince ")
        ssh_connection(host_esx,user,host_esx_pw,"reboot")
    else:
        logging.info ("AUL not properly installed so exiting ")
        exit()
    verify_piviot()
    set_sync_speed()
    check_sync_status()
    duplex_state()




def vib_uninstall():
    logging.info ("uninstalling vib tool in esx host")
    command ="esxcli software vib remove --vibname qatools"
    uninstall_vib = ssh_connection(host_esx,user,host_esx_pw,command)
    logging.info(uninstall_vib)        
    vib_uninstall =re.search(r"vib uninstalled susceesfully reboot system",str(uninstall_vib))
    if vib_uninstall:
        logging.info("vib uninstalled susceesfully reboot system")
        ssh_connection(host_esx,user,host_esx_pw,"reboot")
    else:
        logging.info("vib not  installed susceesfully ")
        exit()
    time.sleep(600)

def check_vib():    
    vib_status =ssh_connection(host_esx,user,host_esx_pw,"esxcli software vib list | grep qatools")
    vib_status=re.search(r"qatools",str(vib_status))
    if not vib_status:
        #print ("vib not installed in the system")
        return True
    else:
        print ("vib installed in the system")
        


def vib_install():
    set_up()
    logging.info ("installing vib tool in esx host")
    source_file = "/test1/Aeries_New/ftESX/{0}/{1}".format(input_dir,input_subdir)
    files = sftp.listdir(source_file)
    vib,file=get_file_vib(files)
    dest_file = "C:\\auto\\{}".format(vib)
    logging.info ("downloading the vib file")
    source_file = "/test1/Aeries_New/ftESX/{0}/{1}/{2}".format(input_dir,input_subdir,vib)
    download_file(source_file,dest_file)
    file_s = "C:\\auto\\{}".format(vib_script)
    upload_loation="/root/{}".format(vib_script)
    upload_vib=uplaod_file(file_s,upload_loation)
    file_vib1="/test1/Aeries_New/ftESX/{0}/{1}/{2}".format(input_dir,input_subdir,vib)
    dest_file= "C:\\auto\\{}".format(vib)
    download_vib=download_file(file_vib1,dest_file)
    logging.info (download_vib)
    logging.info ("uploading file {}".format(vib))
    file_vib = "C:\\auto\\{}".format(vib)
    logging.info (file_vib)
    upload_loation="/root/{}".format(vib)
    upload_vib=uplaod_file(file_vib,upload_loation)
    logging.info(upload_vib)
    logging.info ("Copying vib to esx host")
    command="python /root/vib_copy.py {0} {1} {2}".format(vib,host_esx,host_esx_pw)
    logging.info (command)
    data=ssh_connection(app,user,app_pwd,command)
    logging.info (data)
    command ="esxcli software vib install -v /tmp/{} --force".format(vib)
    install_vib = ssh_connection(host_esx,user,host_esx_pw,command)
    logging.info(install_vib)
    vib_install =re.search(r"The update completed successfully",str(install_vib))
    if vib_install:
        logging.info("vib installed susceesfully reboot system")
        ssh_connection(host_esx,user,host_esx_pw,"reboot")
    else:
        logging.info("vib not  installed susceesfully ")
        exit()
    time.sleep(600)
    command = " esxcli software vib list | grep qatool"
    data=ssh_connection(host_esx,user,host_esx_pw,command)
    m=re.search(r"\d.\d.\d-\d+",str(data))
    logging.info ("vib version installaed :{}".format(m.group()))



def AUL_upgrade():
    logging.info("Checking Whether VIB installed in the system ..... ")
    Check_vib = check_vib()
    if Check_vib:
        logging.info("VIB not installed in the system so proceeding with AUL upgrade ")
    else:
        logging.info("VIB is installed in the system so proceeding with VIB uninstall ")
        vib_uninstall()
    logging.info("Checking system health please wait..... ")
    appliance_ver,duplex_state12=duplex_state()
    print (f"current installed applaince version is {appliance_ver}\n")
    print (f"system is healthy & {duplex_state12}\n")
    source_file = "/test1/Aeries_New/ftESX/{0}/{1}".format(input_dir,input_subdir)
    files = sftp.listdir(source_file)
    vib,file=get_file_vib(files)
    source_file = "/test1/Aeries_New/ftESX/{0}/{1}/{2}".format(input_dir,input_subdir,file)
    dest_file = "C:\\auto\\{}".format(file)
    logging.info ("downloading the iso file")
    download_file(source_file,dest_file)
    upload_loation="/root/{}".format(file)
    logging.info ("uploading the iso file")
    uplaod_file(dest_file,upload_loation)
    AUL_file = "C:\\auto\\{}".format(AUL_Upgrade1)
    upload_loation="/root/{}".format(AUL_Upgrade1)
    logging.info ("uploading the Appliance Script")
    uplaod_file(AUL_file,upload_loation)
    logging.info ("Executing upgrade AUL script")
    command="python /root/{0} {1} {2} {3}".format(AUL_Upgrade1,file,host_esx,host_esx_pw)
    time.sleep(60)
    logging.info ("Upgrading AUL Please wait.... ....")
    data1=ssh_connection(app,user,app_pwd,command)
    logging.info (data1)
    m=re.search(r"reboot",str(data1))
    if m.group() == "reboot":
        logging.info ("AUL upgraded rebooting the applaince ")
        ssh_connection(host_esx,user,host_esx_pw,"reboot")
    else:
        logging.info ("AUL not properly installed so exiting ")
        exit()
    verify_piviot()
    #set_sync_speed()
    check_sync_status()
    current_appliance_ver,duplex_state12=duplex_state()
    print (f"AUL is upgraded from {appliance_ver} to {current_appliance_ver}  successfully")
    



def cleanUP():
    print ("cleaning files in appliance ")
    source_file = "/test1/Aeries_New/ftESX/{0}/{1}".format(input_dir,input_subdir)
    files = sftp.listdir(source_file)
    vib,file=get_file_vib(files)
    command="rm -rf AUL.pl  vib_copy.py  {0} {1} {2} ".format(file,my_files,vib)
    print(ssh_connection(app,user,app_pwd,command))
    print ("removing files ")
    ls_files =os.listdir()
    files_reomove=[i for i in ls_files if i.endswith( "iso") or i.endswith("vib")]
    for f in files_reomove:
          os.remove(file)
       

if __name__ == "__main__":
    AUL_upgrade()
    #AUL_install()
    #vib_install()
    #vib_uninstall()
    #AUL_upgrade()
    cleanUP()

    
	
   
