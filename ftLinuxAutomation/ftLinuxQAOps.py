#ftLinuxQAOps.py

import getopt, os, sys
from ftLinuxQAOperations import *
#
#=====================================Variable Declarations==============================================================================
global Obj
global QAOperation

#========================================================================================================================================
def EvaluateArgs():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hf:s:o:", ["help", "file=", "server=", "operation="])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(err)
        Usage()
        sys.exit(2)

    Cfg_given=False
    Opr_given=False
    Srv_given=False
	
    for o, a in opts:
        if o in ("-o", "--operation"):
            Opr_given=True
            print('QA Operation mandated is %s ' % a )
            Obj.Set_Operation_Name(a)
            QAOperation=a
            
        elif o in ("-s", "--server"):
            Srv_given=True
            print('Target server specified is %s ' % a )
            Obj.Set_Host_Name(a)
            
        elif o in ("-f", "--file"):
            Cfg_given=True
            print('Setting QA Operations Config file to : %s ' %  a )
            Obj.Set_Config_File(a)
            
        elif o in ("-h", "--help"):
            Usage()
            sys.exit()
        else:
            assert False, "Unhandled option."
	
    if False in (Cfg_given, Opr_given, Srv_given):
        print("ERROR: One of the mandatory parameters is missing. Must specify mandatory parameters.")
        Usage()
        sys.exit(2)
        
    # if not Cfg_given:
        # print("Config file was not given. Must specify a Config file.")
        # Usage()
        # sys.exit(2)
        
    # if not Opr_given:
        # print("QA Operation not specified. Must specify a QA Operation.")
        # Usage()
        # sys.exit(2)        
    
    print('List of major QA operations : ')
    print(">>>>" , args)
    global Operations
    Operations=Obj.STD_Operations if len(args)==0 else args
    print(Operations)
    Illegal_Operations=[Operation for Operation in Operations if Operation not in Obj.All_Operations]
    if (Illegal_Operations):
        print("Illegal operation names supplied : ", Illegal_Operations)
        Usage()
        sys.exit()
#========================================================================================================================================
def Usage():
    print("Usage: To be constructed...")
    print("Config file , Target Server IP address and Operation name  are mandatory options. ")
    print("All supported QA operations:")
    print(Obj.STD_Operations)

    print("Additionally available QA operations:")
    print([Operation for Operation in Obj.All_Operations if Operation not in Obj.STD_Operations])
#========================================================================================================================================

if __name__ == "__main__":
    Obj=ftLinuxQAOperations()
    Operations=[]
    QAOperation=""
    #
    EvaluateArgs()
    
    print(Obj.All_Operations)
    
    print(sys.argv)
    
    print("----->",Operations)
    #Obj.Perform_IPL()
    Obj.Set_Config_Dict()
    Obj.Set_Contact_IpAddr(Obj.CONFIG['DHCP-IPA'])
    #Obj.Set_Contact_IpAddr(Obj.CONFIG['STATIC-IPA'])
    Obj.Set_SSHO_Object()
    # ##Obj.Get_SSHClient()
    # ##Obj.SSHOObj=Obj.Get_SSHO_Object()
    # #Obj.Unregister_OS()
    # #Obj.Register_OS()
    # Obj.Set_Linux_Release(Obj.CONFIG['LINUX_RELEASE'])
    # #Obj.Update_OS()
    # #Obj.Generate_NetCfg_Script()
    # #Obj.Schedule_NetCfg()
    # #Obj.Install_AUL()
    # #print("Waiting untill server is reachable over network... (40 minutes)")
    # #time.sleep(2400)
    #Obj.Set_Contact_IpAddr(Obj.CONFIG['STATIC-IPA'])
    #Obj.Check_Server_Availability(Obj.CONTACT_IPADDR)
    #Obj.Set_SSHO_Object()
    #Obj.Unregister_OS()
    #Obj.Register_OS()
    #Obj.Install_QATools()
    #Obj.Verify_FTServer_Version()
    #Obj.Verify_HW_Duplexing()
    QAOperation=Obj.QA_OPERATION
    print('+++' + QAOperation)
    getattr(Obj,QAOperation)()
    # #Obj.Install_QATools()
    # #[getattr(Obj, Operation)() for Operation in Operations]
        # #print("***>",action)
        # #getattr(Obj,action)()
        # #Remember to implement error check and save_error routine later.


