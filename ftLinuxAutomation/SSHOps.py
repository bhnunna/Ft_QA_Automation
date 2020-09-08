#Class for server operations using Paramiko SSH connection. 
import paramiko
#import logging
from socket import gethostname
import CommonLibrary as CL
import time

class SSHOps():
    # Variable declarations:
    SSC=None
    Channel=None
    Output=None
    ServerCreds=None
    SFC=None
    CWD=CL.CWD
    
    def __init__(self, **ServerCreds):
        print('Creating an object for all SSH Operations : Server-->ServerCreds["SERVERIP"], User-->ServerCreds["USER"] and his password...')
        self.SSC=self.Get_SSHClient(**ServerCreds)
        self.ServerCreds=ServerCreds
        print("===>>",self.ServerCreds)
        if self.SSC:
            print('SSH Client Object successfully created...')
        else:
            print("Probably Server connection got aborted.")
        return None
    
    def Get_SSHClient(self, **ServerCreds):
        try:
            print("Spawning a new SSH Client connection object using host IP address %s and given credentials..." % ServerCreds["SERVERIP"])
            S = paramiko.SSHClient()
            S.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            S.connect(ServerCreds["SERVERIP"], ServerCreds["PORTNO"], username=ServerCreds["USER"], password=ServerCreds["PASSWD"], look_for_keys=False, allow_agent=False)
            #self.logger.info('%s:%d: connected to upstream %s@%s:%d' % (self.client_address + (upstream.upstream_user, upstream.upstream_host, upstream.upstream_port)))
            print("Paramiko AUTH_SUCCESSFUL : %s" % paramiko.AUTH_SUCCESSFUL)
            return S
        except paramiko.SSHException:
            #self.logger.critical('%s:%d: connection failed to upstream %s@%s:%d' % (self.client_address + (upstream.upstream_user, upstream.upstream_host, upstream.upstream_port)))
            print("Paramiko AUTH_FAILED : %s" % paramiko.AUTH_FAILED)
            return None

    # def Get_Session_Channel(self, Client):
        # print('Requesting a new channel to the server, of type "session".')
        # Channel = Client.get_transport().open_session()
        # Channel.get_pty()
        # Channel.invoke_shell()
        # return Channel
    def Get_Session_Client(self):
        print('Requesting a new client to the server, of type "SSH client".')
        self.Client = self.SSC
        
    def Execute_Long_Run_Commands(self,LongRunCmd):
        self.Get_Session_Client()
        print('Executing the following command on the remote server : ')
        print(LongRunCmd)
        print('This command may take some time to complete. Please be patient...')
        stdin_, stdout_, stderr_ = self.Client.exec_command(LongRunCmd)
        #stdout_.channel.recv_exit_status()
        Exit_Status=stdout_.channel.recv_exit_status()
        if Exit_Status==0:
            print("Done. Command completed successfully! Exit Status : %s " % Exit_Status)
        else:
            print("Error! Something went wrong. Exit Status : %s " % Exit_Status)
        lines = stdout_.readlines()
        for line in lines:
            print(line)
                
    def Get_Session_Channel(self):
        print('Requesting a new channel to the server, of type "session".')
        self.Channel = self.SSC.get_transport().open_session()
        self.Channel.get_pty()
        self.Channel.invoke_shell()
        self.Channel.settimeout(1500)
        #return Channel

    def Receive_Channel_Output(self):
        self.Output=self.Channel.recv(65000).decode('utf-8')
        print(self.Output)


    def SeePromptPutInput(self,Prompt, Input):
        if Prompt in self.Output:
            self.Channel.send(Input+'\n')
            
    def BlindlyPutInput(self,Input):
        print("Sending the input : %s " % Input) 
        self.Channel.send(Input+'\n')
        # if self.Channel.recv_ready():
            # print("Now it is Receive ready...")
            # self.Receive_Channel_Output() 
        #Exit_Status=self.Channel.recv_exit_status()
        #return Exit_Status
        return

    def WaitUntilRR(self):
        while not self.Channel.recv_ready() and not self.Channel.exit_status_ready():
            #while True:
            time.sleep(20)
            if not self.Channel.recv_ready():
                print("Waiting to receive command output...")
                time.sleep(5)
                #self.Receive_Channel_Output()    
            #
            elif not self.Channel.exit_status_ready():
                print('Execution is still in course...')
                time.sleep(20)
                #break
            #
        print("Now it is Receive ready...")
        self.Receive_Channel_Output()    
        return
            
    def Execute_On_Server(self,CFName=None, SectionHeading=None, *CmdList, **CmdDict):
        self.Get_Session_Channel()
        CmdInputs={}
        #
        if SectionHeading and CFName:
            print('Looking for command and inputs in the {SH} Section-heading of the {CFN} config file...'.format(SH=SectionHeading,CFN=CFName))
            CmdInputs=CL.GetDFSec2Dict(CFName, SectionHeading)
            print("Command Inputs Dictionary:\n",  CmdInputs)
            self.Execute_On_Server(**CmdInputs)
            return
        #
        elif CmdList:
            for Cmd in CmdList:
                self.WaitUntilRR()
                print('Executing : ' + Cmd)
                self.BlindlyPutInput(Cmd)
                #self.WaitUntilRR()
            self.WaitUntilRR()
            self.Receive_Channel_Output()
            self.Channel.close()
            return
        #
        elif CmdDict:
            print("Command Inputs Dictionary:\n %s " % CmdDict)
            CmdLine=CmdDict['CMDLINE']
            OnlyInputs={d:CmdDict[d] for d in CmdDict if d!='CMDLINE'}
            print('Command line : %s ' % CmdLine)
            print("Only Inputs Dictionary:\n",  OnlyInputs)
            print("Executing the following command on the remote host...")
            print(CmdLine)
            self.WaitUntilRR()
            print('Executing : ' + CmdLine)
            self.BlindlyPutInput(CmdLine)
            #
            for key,val in sorted(OnlyInputs.items()):
                print(key,'--->', val)
                print("Sending the input : %s " % val)
                self.WaitUntilRR()
                self.BlindlyPutInput(val)
            #    
            self.WaitUntilRR()
            self.Receive_Channel_Output()
            self.Channel.close()
            return
        #
        else:
            print("Invalid parameters given to the method.")
            self.Channel.close()
            return
            
    def Execute_Probe_Output(self,CmdLine,ProbeStr):
        self.Get_Session_Channel()
        CmdLineOutput=""
        StrFound=None
        self.WaitUntilRR()
        print('Executing : ' + CmdLine)
        self.BlindlyPutInput(CmdLine)
        self.Receive_Channel_Output()
        CmdLineOutput+=self.Output
        time.sleep(5)
        self.Receive_Channel_Output()
        CmdLineOutput+=self.Output
        print("==>",CmdLineOutput)
        if ProbeStr in CmdLineOutput:
            StrFound=True
            print("The given string %s was very much present in the command output!" % ProbeStr)
            print("StrFound : %s" % StrFound)
        else:
            StrFound=False
            print("The given string %s was NOT present in the command output!" % ProbeStr)
            print("StrFound : %s" % StrFound)
        self.Channel.close()
        #self.Channel.transport.close()
        return StrFound
        
    def Sftp_Get_File(self, RemoteFilePath, LocalFilePath):
        print("Opening an sftp connection to server %s " % self.ServerCreds["SERVERIP"])
        self.SFC=self.SSC.open_sftp()
        print("Trasferring remote file %s over sftp connection from the server %s as local file %s " % (RemoteFilePath, self.ServerCreds["SERVERIP"], LocalFilePath))
        self.SFC.get(RemoteFilePath, LocalFilePath)
        print("Done.")
        self.SFC.close()
        
    def Sftp_Put_File(self, LocalFilePath, RemoteFilePath):
        print("Opening an sftp connection to server %s " % self.ServerCreds["SERVERIP"])
        self.SFC=self.SSC.open_sftp()
        print("Trasferring local file %s over sftp connection to the server %s as remote file %s " % (LocalFilePath, self.ServerCreds["SERVERIP"], RemoteFilePath))
        self.SFC.put(LocalFilePath, RemoteFilePath)
        print("Done.")
        self.SFC.close()
        
    def Execute_Cmd_Download_OutputFile(self, CmdLine, RemoteFilePath, LocalFilePath):
        Final_CmdLine="%s | tee %s " % (CmdLine, RemoteFilePath)
        print("Executing the following command on the remote server %s and storing the output in the file %s " % (self.ServerCreds["SERVERIP"], RemoteFilePath))
        print(Final_CmdLine)
        self.Execute_Long_Run_Commands(Final_CmdLine)
        self.Sftp_Get_File(RemoteFilePath, LocalFilePath)
        