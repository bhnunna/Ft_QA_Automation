#ftLinuxQAOperations Class.
import getopt, os, sys, fileinput, time
import paramiko
import logging
from socket import gethostname
#---------------------------------------------
import SSHOps
import CommonLibrary as CL

class ftLinuxQAOperations():
    # Variable declarations:
    Import_Operations=('Perform_IPL','Perform_Upgrade','Setup_Baremetal','Setup_Hypervisor', 'Install_Firmware','Configure_Network','Schedule_NetCfg','Generate_NetCfg_Script', 'Install_AUL', 'Install_QATools', 'Update_OS','Install_QATools','Register_OS', 'Unregister_OS')
    All_Operations = Import_Operations[:]
    STD_Operations = Import_Operations[:4]
    #
    OSPLATFORM=sys.platform
    CWD=CL.CWD
    CONFIG = {}
    CONFIG_FILE = r""
    TARGET_HOST = ""
    CONTACT_IPADDR = ""
    QA_OPERATION = ""
    SSHOObj = ""
    PORTNO=22
    USER="root"
    PASSWD="syseng"
    USER_HOME="/root"
    SSC=""
    LINUX_RELEASE=""
       
#=======================================================================================================================
    def __init__(self):
        print("Creating an object of ftLinuxQAOperations")
        return None

    def Set_Config_File(self,FileName): 
        print("----->" + FileName)
        print('CONFIG_FILE' + ' is now set to ' + FileName)
        self.CONFIG_FILE=FileName

    def Set_Host_Name(self,HostName):
        print("----->" + HostName)
        print('TARGET_HOST' + ' is now set to ' + HostName)
        self.TARGET_HOST=HostName

    def Set_Operation_Name(self,QAOpName):
        print("----->" + QAOpName)
        print('QA_OPERATION' + ' is now set to ' + QAOpName)
        self.QA_OPERATION=QAOpName
    
    def Set_Config_Dict(self):
        self.CONFIG=CL.GetDFSec2Dict(self.CONFIG_FILE, self.TARGET_HOST)
        print('CONFIG dictionary is now loaded with keys and values from CONFIG file...')
        print('CONFIG=%s' % self.CONFIG)
        
    def Set_Contact_IpAddr(self, IPAddr=None):
        #self.CONTACT_IPADDR = self.CONFIG['DHCP-IPA'] if self.CONFIG['DHCP-IPA'] else self.CONFIG['STATIC-IPA']
        self.CONTACT_IPADDR = IPAddr
        print('CONTACT_IPADDR is now set to %s ' %  self.CONTACT_IPADDR)
        
    def Set_Linux_Release(self,Linux_Release):
        self.LINUX_RELEASE=Linux_Release
        print('LINUX_RELEASE is now set to %s ' % Linux_Release)
        
    def Get_SSHO_Object(self,**ServerCreds):
        if not ServerCreds:
            ServerCreds=dict((k,self.CONFIG[k]) for k in ('PORTNO','USER','PASSWD'))
            ServerCreds.setdefault('SERVERIP', self.CONTACT_IPADDR)
        SSHOObjName=SSHOps.SSHOps(**ServerCreds)
        return SSHOObjName
        
    def Set_SSHO_Object(self, **ServerCreds):
        print('Obtaining an SSH Operations Object and assigning it to a holder...')
        self.SSHOObj=self.Get_SSHO_Object(**ServerCreds)
        print("Done.")
        
    def Check_Server_Availability(self, HostIP):
        while True:
            print("Checking if the host %s is available on the network..." % HostIP)
            #HOST_UP  = True if os.system("ping -n 1 " + HostIP) is 0 else False
            ExecResults=CL.RunCMD("ping -n 1 " + HostIP)
            print("ReturnCode===>",ExecResults['ReturnCode'])
            #HOST_UP=True if ExecResults['ReturnCode'] is 0 else False
            #if HostIP==True:
            RetCode=ExecResults['ReturnCode']
            HOST_UP=True if RetCode==0 else False
            #
            if HOST_UP:
                print("Host %s is available. Continuing..." % HostIP)
                break
            elif not HOST_UP:
                print("Looks like host %s is not yet available on the network... Next try in 15 minutes..." % HostIP)
                print("Waiting...")
                time.sleep(900)
                                                  
    def Get_SSHClient(self, Ip_Addr):
        try:
            print("Spawning a new SSH Client connection object using host IP address %s and given credentials..." % Ip_Addr)
            S = paramiko.SSHClient()
            S.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            S.connect(Ip_Addr, self.PORTNO, username=self.USER, password=self.PASSWD, look_for_keys=False, allow_agent=False)
            #self.logger.info('%s:%d: connected to upstream %s@%s:%d' % (self.client_address + (upstream.upstream_user, upstream.upstream_host, upstream.upstream_port)))
            print(paramiko.AUTH_SUCCESSFUL)
            #self.SSC=S
            return S
        except paramiko.SSHException:
            #self.logger.critical('%s:%d: connection failed to upstream %s@%s:%d' % (self.client_address + (upstream.upstream_user, upstream.upstream_host, upstream.upstream_port)))
            print(paramiko.AUTH_FAILED)
            return S
        
    def Register_OS(self, CFName=None, SectionHeading=None, SSHObject=None):
        if not CFName:
            CFName=self.CONFIG_FILE
        if not SSHObject:
            SSHObject=self.SSHOObj
        if not SectionHeading:
            SectionHeading='REGISTER_OS'
        #
        CmdInputs=CL.GetDFSec2Dict(CFName, SectionHeading)
        CmdList=[CmdInputs[k] for k in sorted(list(CmdInputs))]
        print("Registering the OS running on host %s with RedHat Network..." % SSHObject.ServerCreds['SERVERIP'])
        print("Command Inputs Dictionary:\n",  CmdInputs)
        print("List of commands to be executed:\n", CmdList)
        SSHObject.Execute_On_Server(None,None,*CmdList)
        
    def Unregister_OS(self, CFName=None , SectionHeading=None , SSHObject=None):
        if not CFName:
            CFName=self.CONFIG_FILE
        if not SSHObject:
            SSHObject=self.SSHOObj
        if not SectionHeading:
            SectionHeading='UNREGISTER_OS'
        #
        CmdInputs=CL.GetDFSec2Dict(CFName, SectionHeading)
        CmdList=[CmdInputs[k] for k in sorted(list(CmdInputs))]
        print("Unregistering the OS running on host %s with RedHat Network..." % SSHObject.ServerCreds['SERVERIP'])
        print("Command Inputs Dictionary:\n",  CmdInputs)
        print("List of commands to be executed:\n", CmdList)
        SSHObject.Execute_On_Server(None,None,*CmdList)
        
    def Update_OS(self, CFName=None , SectionHeading=None , SSHObject=None):
        if not CFName:
            CFName=self.CONFIG_FILE
        if not SSHObject:
            SSHObject=self.SSHOObj
        if not SectionHeading:
            SectionHeading='UPDATE_OS'
        #
        self.Set_Linux_Release(self.CONFIG['LINUX_RELEASE'])
        CmdInputs=CL.GetDFSec2Dict(CFName, SectionHeading)
        CmdArray=[CmdInputs[k] for k in sorted(list(CmdInputs))]
        FileToProbe,ProbeStr=CmdArray[0].split(',')
        CmdToSetVersion=CmdArray[1]+self.LINUX_RELEASE
        CmdToUpdate=CmdArray[2]
        CmdToExit=CmdArray[3]
        CmdToReboot=CmdArray[4]
        CmdList=[CmdToSetVersion,CmdToUpdate,CmdToExit]
        #CmdList=[CmdToSetVersion]
        print("Running OS Updates on host %s..." % SSHObject.ServerCreds['SERVERIP'])
        StringFound=SSHObject.Execute_Probe_Output(FileToProbe, ProbeStr)
        if StringFound:
            self.Unregister_OS()
            self.Register_OS()
            #SSHObject.Execute_On_Server(None,None,*CmdList)
            SSHObject.Execute_Long_Run_Commands(CmdToSetVersion)
            SSHObject.Execute_Long_Run_Commands(CmdToUpdate)            
        else:
            #CmdList.pop(0)
            SSHObject.Execute_On_Server(None,None,*CmdList)
        #
        time.sleep(900)
        
        self.Unregister_OS()
        SSHObject.Execute_Long_Run_Commands(CmdToReboot)
        print("Waiting for 300 seconds...")
        time.sleep(300)
        self.Check_Server_Availability(self.CONTACT_IPADDR)

    def Generate_NetCfg_Script(self, CFName=None , SectionHeading=None):
        if not CFName:
            CFName=self.CONFIG_FILE

        if not SectionHeading:
            SectionHeading='NET_CFG_SCRIPT'
        CmdInputs=CL.GetDFSec2Dict(CFName, SectionHeading)
        Script_Path=CmdInputs.pop('SCRIPT-PATH')
        CmdArray=[CmdInputs[k] for k in sorted(CmdInputs.keys())]
        print("Generating a shell script to change the network configuration on the remote server...")
        CL.Write_Lines_To_File(Script_Path,CmdArray)
        return Script_Path
        
    def Schedule_NetCfg(self, CFName=None, SectionHeading=None, SSHObject=None):
        if not CFName:
            CFName=self.CONFIG_FILE
        if not SectionHeading:
            SectionHeading='SCHEDULE-RUN'
        if not SSHObject:
            SSHObject=self.SSHOObj
        CmdInputs=CL.GetDFSec2Dict(CFName, SectionHeading)
        Script_Name=CmdInputs.pop('SCRIPT-NAME')
        Script_Path=CmdInputs.pop('SCRIPT-PATH')
        Target_Path=CmdInputs.pop('TARGET-PATH')
        CmdList=[CmdInputs[k] for k in sorted(CmdInputs.keys())]
        print("FTP-ing the shell script to the remote server and scheduling a remote run...")
        SSHObject.Sftp_Put_File(Script_Path, Target_Path)        
        SSHObject.Execute_On_Server(None,None,*CmdList)    

    def Install_AUL(self, CFName=None, SectionHeading=None, SSHObject=None):
        if not CFName:
            CFName=self.CONFIG_FILE
        if not SectionHeading:
            SectionHeading='AUL-GENERIC'
        if not SSHObject:
            SSHObject=self.SSHOObj
        CmdInputs=CL.GetDFSec2Dict(CFName, SectionHeading)
        print('Following are the commands lined up for execution on the remote server %s : ' % SSHObject.ServerCreds['SERVERIP'])
        print(CmdInputs)
        SSHObject.Execute_Long_Run_Commands(CmdInputs['MKDIR-FSMOUNT'])
        SSHObject.Execute_Long_Run_Commands(CmdInputs['FSMOUNT-CMD'])
        SSHObject.Execute_Long_Run_Commands(CmdInputs['MKDIR-ISOMOUNT'])
        SSHObject.Execute_Long_Run_Commands(CmdInputs['COPY_ISOFILE'])
        SSHObject.Execute_Long_Run_Commands(CmdInputs['ISOMOUNT-CMD'])
        SSHObject.Execute_Long_Run_Commands(CmdInputs['INSTALL-CMD'])
        print("System is going for a reboot in 60 seconds...")
        SSHObject.Execute_Long_Run_Commands(CmdInputs['REBOOT-CMD'])
        
    def Install_PI_Script(self, CFName=None, SectionHeading=None, SSHObject=None):
        if not CFName:
            CFName=self.CONFIG_FILE
        if not SectionHeading:
            SectionHeading='POSTINSTALL-SCRIPT'
        if not SSHObject:
            SSHObject=self.SSHOObj
        CmdInputs=CL.GetDFSec2Dict(CFName, SectionHeading)
        #CmdInputs['CI3']=self.TARGET_HOST
        print('Executing Postinstall script to install QA TOOLS on remote server %s : ' % SSHObject.ServerCreds['SERVERIP'])
        SSHObject.Execute_On_Server(**CmdInputs) 
                         
    def Install_QATools(self, CFName=None, SectionHeading=None, SSHObject=None):
        if not CFName:
            CFName=self.CONFIG_FILE
        if not SectionHeading:
            SectionHeading='QATOOLS-GENERIC'
        if not SSHObject:
            SSHObject=self.SSHOObj
        print("Performing Install_QATools operation on host %s with IP address %s " %  (self.TARGET_HOST, SSHObject.ServerCreds['SERVERIP']))
        CmdInputs=CL.GetDFSec2Dict(CFName, SectionHeading)
        
        SSHObject.Execute_Long_Run_Commands(CmdInputs['MKDIR_FSMOUNT'])
        SSHObject.Execute_Long_Run_Commands(CmdInputs['FSMOUNT_CMD'])
        SSHObject.Execute_Long_Run_Commands(CmdInputs['COPY_POSTINSTALL_SCRIPT'])
        SSHObject.Execute_Long_Run_Commands(CmdInputs['MKDIR_QAAUTO_DIR'])
        #
        self.Install_PI_Script()
        
    def Verify_FTServer_Version(self, CFName=None, SectionHeading=None, SSHObject=None):
        if not CFName:
            CFName=self.CONFIG_FILE
        if not SectionHeading:
            SectionHeading='VERIFY_AUL_VERSION'
        if not SSHObject:
            SSHObject=self.SSHOObj
        print("Performing post install verification of installed AUL version on host %s with IP address %s " %  (self.TARGET_HOST, SSHObject.ServerCreds['SERVERIP']))
        CmdInputs=CL.GetDFSec2Dict(CFName, SectionHeading)
        print(CmdInputs)
        key,value='CHECK_AUL_VERSION', CmdInputs['CHECK_AUL_VERSION']
        OutputFile=key+".output"
        print("Output file name is %s " % OutputFile)
        RemoteFilePath=self.USER_HOME+"/"+OutputFile
        print("Remote file path is %s " % RemoteFilePath)
        LocalFilePath=self.CWD+"\\"+OutputFile
        print("Local file path is %s " % LocalFilePath)
        SSHObject.Execute_Cmd_Download_OutputFile(value, RemoteFilePath, LocalFilePath)
        if self.QA_OPERATION in ("Perform_IPL", "Verify_FTServer_Version"):
            AUL_Version=CmdInputs['BASELINE_AUL_VERSION']
        elif self.QA_OPERATION=="Perform_Upgrade":
            AUL_Version=CmdInputs['UPGRADED_AUL_VERSION']
            
        if AUL_Version in open(LocalFilePath).read():
            print("SUCCESS: The installed AUL version matches the expected AUL version (%s)..." % AUL_Version)
        else:
            print("FAILURE: The installed AUL version does not match with the expected AUL version..." % AUL_Version)
            print("Please verify the version in the file %s " % LocalFilePath)
        
    def Verify_HW_Duplexing(self, CFName=None, SectionHeading=None, SSHObject=None):
        if not CFName:
            CFName=self.CONFIG_FILE
        if not SectionHeading:
            SectionHeading='VERIFY_HW_DUPLEXING'
        if not SSHObject:
            SSHObject=self.SSHOObj
        print("Performing post install verification of hardware duplexing on host %s with IP address %s " %  (self.TARGET_HOST, SSHObject.ServerCreds['SERVERIP']))
        CmdInputs=CL.GetDFSec2Dict(CFName, SectionHeading)
        OpStateActuals=CmdInputs.fromkeys(CmdInputs)
        print(CmdInputs)
        print(OpStateActuals)
        for key,value in CmdInputs.items():            
            OutputFile=key+".output"
            print("Output file name is %s " % OutputFile)
            RemoteFilePath=self.USER_HOME+"/"+OutputFile
            print("Remote file path is %s " % RemoteFilePath)
            LocalFilePath=self.CWD+"\\"+OutputFile
            print("Local file path is %s " % LocalFilePath)
            SSHObject.Execute_Cmd_Download_OutputFile(value, RemoteFilePath, LocalFilePath)                    
            OPFDict=CL.GetDFWithoutSec2Dict(LocalFilePath)
            print(OPFDict)
            OpStateActuals[key]=OPFDict['Op State']
        print(OpStateActuals)
        OpStateActuals['CHECK_DUPLEX_10']='SIMPLEX'
        OpStateActuals['CHECK_DUPLEX_11']='SIMPLEX'

        if 'SIMPLEX' in OpStateActuals.values():
            print("One of the hardware Op State does not match DUPLEX. Looks like syncing is still on. Next check in 30 minutes...")
            time.sleep(1800)
            self.Verify_HW_Duplexing()
        else:
            print("SUCCESS: All hardware Op States are running as DUPLEX")
            print("Installation of AUL seems to be successful")
            print("DONE.")
        return
                
    def Perform_IPL(self):
        self.Set_Config_Dict()
        self.Set_Contact_IpAddr(self.CONFIG['DHCP-IPA'])
        self.Set_SSHO_Object()
        self.Set_Linux_Release(self.CONFIG['LINUX_RELEASE'])
        #self.Update_OS()
        #self.Generate_NetCfg_Script()
        #self.Schedule_NetCfg()
        self.Install_AUL()
        self.Set_Contact_IpAddr(self.CONFIG['STATIC-IPA'])
        self.Check_Server_Availability(self.CONTACT_IPADDR)
        self.Set_SSHO_Object()
        #self.Install_QATools()
        self.Verify_FTServer_Version()
        self.Verify_HW_Duplexing()      
        
        