##C:\Users\bnunna\Desktop\Ft_QA_Automation\ftESXAutomation\AUL_Install_upgrade_1.py
import paramiko
import re
import os
import time
import sys
import logging
import configparser
import random
import math
import argparse
import posixpath
import datetime

from src.constants import package_wide_constants
curr_timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
logfile = os.path.join(package_wide_constants.home, 'vmstress_{}.log'.format(curr_timestamp))
print('logfilename is {}'.format(logfile))
package_wide_constants.logfile = logfile

from src.linux_utils.remote_system import RemoteSystem
from src.linux_utils.switch_utils import SwitchUtils
from src.linux_utils.vm_utils import VMUtils
from src.linux_utils.appliance_utils import ApplianceUtils
from src.linux_utils.appliance_utils import AULException
from src.logger_utils.logger import get_logger
from src.linux_utils.share_utils import ShareUtils
from src.linux_utils.common_utils import *

from src.constants.package_wide_constants import *




logger = get_logger(__name__)
logging.basicConfig(level=logging.INFO)
config = configparser.ConfigParser()
config.read('BasicConfig.txt')
section=config.sections()
#assigning BasicConfig.txt variables
input_dir = config[section[0]]['project_dir']
input_subdir = config[section[0]]['build_dir']
app_ip = config[section[0]]['appliance_ip']
app_pwd = config[section[0]]['app_pwd']
host_esx_ip = config[section[0]]['host_esx_ip']
host_esx_pwd = config[section[0]]['host_esx_pw']
host_esx_id = config[section[0]]['host_userid']
aul_upgrade_build=config[section[0]]['aulbuild_upgrade']
#joining file paths
aul_build_path=posixpath.join(ftesx_test1_path,input_dir,input_subdir)
aul_build_upgradepath=posixpath.join(ftesx_test1_path,input_dir,aul_upgrade_build)
source_file_path = '{0}/{1}/{2}/'.format(common_ftesxbuild_path, input_dir, input_subdir)
#mount_aul_dir = posixpath.join(aul_build_dir, source_file_path)
#mount_aul_dir=aul_build_dir+source_file_path

#TODO:  configure appliance to edit appliance ip
#TODO:  clearing all files copied and tools installed
#TODO:  option to execute operation wise
#TODO:
def aul_install (src_obj,dest_obj,skip_signed_driver=None,skip_vibinstall=None,skip_vmdeploy=None,skip_qatools=None):
    '''
    Perform AUL install on appliance
    Parameters:
        src_obj         :   source connection object to get file
        dest_obj        :   destination connection object to copy file
        skip_vmdeploy   :   skips/proceed vm deployment configuration based on value , default value is None
    Return:
        Failure :   Failed or exception
        Success :   AUL install success message with ft-verify command output
    '''
    logger.info ('AUL build source_file_path is {}'.format(aul_build_path))
    logger.info("Get AUL build iso file to proceed AUL install")
    get_aul_builds,_=get_vm_images_info(share_obj,aul_build_path)
    logger.info ("Files presented in {} is :{}".format(aul_build_path,get_aul_builds))
    aul_iso_image=get_file_with_extension(get_aul_builds, 'iso',input_subdir)
    print('aul_iso_image is {}'.format(aul_iso_image))
    copy_aulbuild=copy_vm_image(src_obj,dest_obj,aul_build_path,upload_aul_loation,aul_iso_image)
    if copy_aulbuild:
        logging.info ('AUL Iso image {} has copied successfully on appliance'.format(aul_iso_image))
    else:
        logging.info('AUL build {} not copied .. check logs'.format(aul_iso_image))
        return
    aul_install_flag=app_obj.aul_install(aul_iso_image,host_esx_ip,host_esx_id,host_esx_pwd,skip_signed_driver)
    if aul_install_flag:
       logger.info ("completed aul_install on appliance")
    else:
        logger.info("Installation aborted .. check the logs")
        return
    time.sleep(50)
    logger.info('System is rebooting .. wait for pivot to complete')
    pivot_status = verify_multiple_pivots([host_esx_ip,app_ip],'install')
    reconnect_handles([vm_obj,app_obj])
    print('Host and appliance connected successfully after pivoting')
    create_mpms=app_obj.create_new_ds()
    check_mpmspeed=vm_obj.set_sync_speed()
    check_sync_status=vm_obj.check_sync_status()
    check_duplex_state=app_obj.duplex_state()
    logger.info ("AUL installation including disk sync is successful and system is duplex..")
    if skip_vibinstall :
        logger.info ("skip_vibinstall value has passed..skipping vib tool installation")
    else :
        logger.info("Proceed with vib tool installation..")
        vib_install(share_obj,vm_obj,aul_build_path,input_subdir)
    if skip_qatools:
        logger.info("skip_postinstall_tool is set ..hence skipping qa tools installation..")
    else:
        install_qatools(share_obj,app_obj)
    if skip_vmdeploy:
        logger.info ("skip_vmdeploy is set ..hence skipping vm deployment settings..")
    else:
        run_vm_stress_test(user_images,3)


def run_vm_stress_test (custom_images,total_vms):
    '''
    procedure will configure all vswitch parametes and deploy vms on esxi host and starts stressdeck.in
    Parameters:
        total_vms         :   No of vms to deploy
        custom_images     :   user passed vm images path or custom images path

    Return:
        Pass    :   successful vm deployment message
        fail    :   raise exception or return fail
    '''
    #Datastore Map is {'MPM1': ['centosvfbvbfdb/centosvfbvbfdb.vmx', 'centoos89969/centoos89969.vmx']}
    logger.info("Get existing VM-data configuration with assigned drives info")
    #checking vim-cmd vmsvc/getallvms to view existing vm data with volume names
    existing_ds_vms_map = vm_obj.get_existing_ds_vms_map()
    #Get existing VM-data configuration
    if existing_ds_vms_map is False:
        logger.error('Failed Get existing VM-data configuration')
        return
    #Get ESX VM template path based on vmware version,returns esx path as '/ESX-VMTemplates/ESX-6.5'
    #executes esxcli system version get
    logger.info('Get esx template path')
    esx_image_path = vm_obj.get_esx_temp_path()
    if esx_image_path is False:
        logger.error('Failed to get vmware version with vm path')
        return
    #check vim-cmd vmsvc/getallvms and delete vms with vim-cmd vmsvc/unregister
    wipe_vms_status = vm_obj.wipe_vms()
    if wipe_vms_status is False:
        logger.error('Failed to wipe existing VMs')
        return
    #executes rm -rf "/vmfs/volumes/MPMX/*"
    erase_stale_vm_status = vm_obj.erase_stale_vm_files()
    if erase_stale_vm_status is False:
        logger.error('Failed to clean the stale VM files in datastores')
        return
    print('getting existing datastores')
    #returns volume names [datastore1,MPM1,MPM2]
    existing_ds = vm_obj.get_existing_datastores()
    print('existing Data store are {}'.format(existing_ds))

    logger.info('creating new datastores if possible')
    app_obj.create_new_ds()

    print('getting existing datastores')
    existing_ds = vm_obj.get_existing_datastores()
    print('existing Data store are {}'.format(existing_ds))
    print('getting data datastores')
    data_datastores = [x for x in existing_ds if 'datastore' not in x]    
    print('actual data datastores are {}'.format(data_datastores))
    if len(data_datastores) == 0:
        logger.info ("create data stores to deploy vms")
        drive_list = vm_obj.get_drive_info()
        logger.info("disk_partition_list is {}".format(drive_list[0]))
        logger.info("disk_volume_name is {}".format(drive_list[1]))
        logger.info("full path of data disk are {}".format(drive_list[2]))
        partition_full_path = vm_obj.create_partition(drive_list[0])
        vm_obj.create_datastore(drive_list[1], partition_full_path)

    # returns only data drive volumes ['MPM1','MPM2']
    usable_datastores = vm_obj.get_data_datastores()
    if len(usable_datastores) == 0:
        logger.error('No sufficient data datastores')
    if total_vms == 0:
        total_vms =len(usable_datastores)
    #executes vim getallvms command
    logger.info('getting pre-configured vms')
    pre_configured_vms = vm_obj.get_existing_vms()
    logger.info('Disk cleaning is done successfully, proceed for network configuration')
    logger.info('Check if any vswitch configuration exists other than management network')
    clear_vswitch_status = vm_obj.clear_vswitch1()
    # if clear_Vswitch is pass proceed with creation of switch
    if clear_vswitch_status:
        status = vm_obj.create_59_network1(vswitchname, portgroupname, uplinks)
        if status:
            logger.info('successfully created')
    logger.info('Cleaning of data disks and network creation completed... Proceed with VM deployment')
    
    logger.info('Check if OVFTool already presented on appliance')
    app_obj.check_and_install_ovf_tool(share_obj,app_obj)
    logger.info('Mount {} on appliance to get vms'.format(appliance_mount_dir))
    app_obj.create_share_mount_point(mount_vmstorageip, appliance_mount_dir)
    #mount_vm_dir = posixpath.join(appliance_mount_dir, esx_image_path)
    #returns /root/vmx_template_files/ESX-VMTemplates/ESX-6.5
    mount_vm_dir=appliance_mount_dir+esx_image_path
    logger.info('mount_VM_dir is {}'.format(mount_vm_dir))
    logger.info('getting all vm images')
    logger.info('custom_images are {} '.format(custom_images))
    all_vm_images_info,custom_images = get_vm_images_info(app_obj,mount_vm_dir,custom_images)
    logger.info('all_vm_images_info is {}'.format(all_vm_images_info))
    random.shuffle(all_vm_images_info)
    n = total_vms-len(pre_configured_vms)

    custom_images_info = list()
    default_images_info = list()

    for vm_image_name, vm_image_size in all_vm_images_info:
        if vm_image_name in custom_images:
            custom_images_info.append((vm_image_name, vm_image_size))
        else:
            default_images_info.append((vm_image_name, vm_image_size))

    extra_vm_images_info = custom_images_info+default_images_info[0:n-len(custom_images_info)]
    logger.info('extra_vm_images_info is {}'.format(extra_vm_images_info))
    vm_datastores = list()
    for datastore_name in existing_ds:
        if 'datastore' not in datastore_name:
            vm_datastores.append(datastore_name)
    for datastore_name in vm_datastores:
        if datastore_name not in existing_ds_vms_map:
            existing_ds_vms_map[datastore_name] = list()
    max_vm_count = math.ceil(total_vms/len(vm_datastores))
    pending_vms = list()
    for vm_image_name, vm_image_size in extra_vm_images_info:
        vm_deployed = False
        for datastore_name in vm_datastores:
            datastore_free_space = vm_obj.get_datastore_size(datastore_name)
            if datastore_free_space and datastore_free_space > 2 * vm_image_size and len(existing_ds_vms_map[datastore_name]) < max_vm_count:
                vm_image_abs_path = posixpath.join(mount_vm_dir, vm_image_name)
                datastore_abs_path = posixpath.join(dest_vmdir_path, datastore_name)
                logger.info(f'vm_image_abs_path and datastore_abs_path is {vm_image_abs_path} {datastore_abs_path}')
                sourcetype = 'VMX'
                #logger.info('sourceType is {}'.format(sourceType))
                # logger.info(sourceType,datastore_name,portgroupname,vm_image_abs_path,host_id,share_pwd,host_IP)
                x = random.randint(0, 255)
                vm_name = vm_image_name + str(x)
                vm_deployed = app_obj.ovf_vm_deploy(app_obj,sourcetype, datastore_name, portgroupname, vm_name, vm_image_abs_path, host_esx_id, host_password, host_esx_ip)
        if vm_deployed is False:
            pending_vms.append((vm_image_name, vm_image_size))
    if pending_vms:
        logger.warning('Following vms are not deployed')
        logger.warning('\n'.join(pending_vms))
        return
    else:
        logger.info("Successfully deployed all VMs")
    '''
    logger.info('disconnecting host')
    host_system.disconnect_host()
    logger.info('disconnecting appliance')
    appliance_system.disconnect_host()
    logger.info('disconnecting share')
    share_system.disconnect_host()
    '''

    post_deployment_vms = vm_obj.get_existing_vms()
    logger.info('New_deployed_vms are {}'.format(post_deployment_vms))

    new_vm_ips = vm_obj.get_vm_ipaddr(post_deployment_vms)
    #logger.info('VM ip list is {}'.format(New_VM_Ips))

    for vm_host_ip in new_vm_ips:
        new_vm = RemoteSystem(vm_host_ip, vm_loginid, vm_loginpassword)
        new_vm.connect_host()

        # ls_verify = new_vm.execute_command('ls \n')
        # logger.info(ls_verify)

        cmd = "sed -i 's/pct_of_memory 30/pct_of_memory 100/g' /input_decks/stressdeck.in"
        new_vm.execute_command(cmd)
        cmd = "sed -i 's/threads 4/threads 40/g' /input_decks/stressdeck.in"
        new_vm.execute_command(cmd)
        cmd = "sed -i 's/file_size 100/file_size 1000/g' /input_decks/stressdeck.in"
        new_vm.execute_command(cmd)
        cmd = 'driver -f /input_decks/stressdeck.in -w -i &'
        new_vm.execute_command(cmd)

        stress_deck = new_vm.execute_command('cat /input_decks/stressdeck.in \n')
        print('Editing of stressdeckfile is completed and stress deck file is {}'.format(stress_deck))
        # stress_current_status=new_vm.execute_command('/std_tools/MonitorTests.pl')
        #logger.info('stress_current_status is {}'.format(stress_current_status))
        process_stress_check = new_vm.execute_command('ps -ef | grep stress \n')
        print('current running process of stress deck file is {}'.format(process_stress_check))
        new_vm.disconnect_host()

def vib_install (src_obj, dest_obj,fullpath_of_vibfile,build_number):
    '''
    Perform vib tool installation on esxi host
    Parameters:
        src_obj     :   Source file system handle to get vib image
        dest_obj    :   Destination file system handle to copy vib image
        fullpath_of_vibfile : Vib image full path
    Return:
        Pass    :   returns True with success log message
        Fail    :   returns False with log message
    '''
    logging.info("Installing vib tool on esx host")
    get_vibimage_flag,_ = get_vm_images_info(share_obj, fullpath_of_vibfile)
    ftesx_vib_image = get_file_with_extension(get_vibimage_flag,'vib',build_number)
    copy_vibfile_flag = copy_vm_image(share_obj,vm_obj, fullpath_of_vibfile, upload_vib_location, ftesx_vib_image)
    #vibfilefullpath='/tmp/qatools-6.7.2-122.vib'
    vibfilefullpath = posixpath.join(upload_vib_location,ftesx_vib_image)
    logging.info ("VIB file full path to install on esxi host is {}".format(vibfilefullpath))
    if copy_vibfile_flag:
        logging.info ('vib file {} has copied successfully on appliance'.format(ftesx_vib_image))
        logging.info ("Proceed with vib tools installation on esxi host..")
        vib_install_output = host_system.execute_command('esxcli software vib install -v {} --force'.format(vibfilefullpath))
        time.sleep (20)
        logger.info("vib_install_command output is {}".format(vib_install_output))
        vib_status = re.search(r"The update completed successfully.*reboot", str(vib_install_output))
        #vib_status = re.search (r"Reboot is pending", str(vib_install_output))
        if vib_status:
            logging.info ("vib installed successfully. Now rebooting the  system")
            host_system.execute_command ("reboot")
            time.sleep(20)
            verify_systemstatus = verify_multiple_pivots([host_esx_ip, app_ip])
            reconnect_handles([vm_obj,app_obj])
            vibtool_flag = vm_obj.check_vibtool_status(host_esx_ip)
            logger.info("vibtool check output is {}".format(vibtool_flag))
            if vibtool_flag:
                logger.info ("Installed VIB tool version is {}".format(vibtool_flag))
            return True
        else:
            logger.info ("vib not installed in the system..check logs")
            # TODO: parse for the version and return version
            return False
    else:
        logging.info ('vib file {} not copied..check logs'.format(ftesx_vib_image))
        return

def aul_upgrade (vm_obj,app_obj,share_obj,skip_signed_driver=None,skip_vibinstall = None):
    '''
    Peform AUL upgrade with given new build
    Parameters:
        vm_obj      :   Esx host system handle
        app_obj     :   appliance system handle
        share_obj   :   share system handle
        skip_signed_driver  :   skip/use -n option in ft-install command based on passed value , default is None
        skip_vibinstall     :   skip/perform vib tool install on esxi system based on passed value , default is None
    '''
    logger.info('Given host ip,username and password is {} {} {}'.format(host_esx_ip,host_esx_id,host_esx_pwd))
    #TODO:use upgrade_flag to optimize the code for loops
    #upgrade_flag = True
    logger.info ("AUL build to upgrade is : {}".format(aul_upgrade_build))
    current_aulbuild = app_obj.check_aulbuild(app_ip)
    match_obj = re.search(r'-(.*)', input_dir)
    project = match_obj.group(1)
    # check_aulbuild: 3.7.3-123
    # {project}-{aul_upgrade_build}: 3.5.6-876
    upgrade_build_version = f'{project}-{aul_upgrade_build}'
    logger.info ("given esx build to upgrade is {}".format(upgrade_build_version))
    if current_aulbuild >= upgrade_build_version:
        logger.error ("current installed AUL build and given upgrade AUL build is not with expected values.. check logs..skipping execution")
        sys.exit(0)
    else:
        logger.info ("Check VIB tools status before proceeding AUL upgrade")
        vibtool_flag = vm_obj.check_vibtool_status(host_esx_ip)
        logger.info("vibtool check output is {}".format(vibtool_flag))
        if vibtool_flag:
            logger.info("Vib is installed on esxi host. remove vib tools to proceed AUL upgrade")
            if vm_obj.vib_uninstall():
                verify_systemstatus = verify_multiple_pivots([host_esx_ip, app_ip])
                reconnect_handles([vm_obj,app_obj])
                logger.info("check vib uninstalled successfully")
                logger.info("Proceed with AUL upgrade to {}".format(aul_upgrade_build))
            else:
                raise AULException('Failed to uninstall vibtools')
        else:
            logger.info("Vib tools not installed on esxi host.. proceed with AUL upgrade to {}".format(aul_upgrade_build))
        logger.info('aul upgrade build source_file_path is {}'.format(aul_build_upgradepath))
        #TODO:make get_aul_builds as global var to get all files at once
        get_aul_builds,_ = get_vm_images_info(share_obj, aul_build_upgradepath)
        ftesx_aul_iso_image = get_file_with_extension(get_aul_builds,'iso',aul_upgrade_build)
        copy_auliso_flag = copy_vm_image(share_obj, app_obj, aul_build_upgradepath, upload_aul_loation, ftesx_aul_iso_image)
        if copy_auliso_flag:
            logging.info('AUL build {} has copied successfully on appliance'.format(ftesx_aul_iso_image))
        else:
            logging.info('AUL build {} not copied'.format(ftesx_aul_iso_image))
            return
        aul_upgrade=app_obj.aul_install(ftesx_aul_iso_image,host_esx_ip,host_esx_id,host_esx_pwd,skip_signed_driver)
        if aul_upgrade:
           logger.info ("completed aulupgrade on appliacne.. rebooting system")
        else:
            logger.info("Installation aborted .. check the logs")
            return
        time.sleep(50)
        logger.info('System is rebooting .. wait for few min.. ')
        pivot_status = verify_multiple_pivots([host_esx_ip,app_ip])
        #TODO:use reconnect def to connect hosts
        reconnect_handles([vm_obj,app_obj])
        #ToDO:include validation for pivot_status
        logger.info("system is up with new build..confirm aul build version")
        check_newaulbuild = app_obj.check_aulbuild(app_ip)
        #TODO:change to == in real test
        if check_newaulbuild == upgrade_build_version:
            logger.info("current installed AUL build and given upgrade AUL build is same..")
            logger.info("AUL upgrade is successful")
            check_duplex_state = app_obj.duplex_state()
            #TODO:include vib_install_flag to seperate modules
            if skip_vibinstall:
                logger.info("skip_vib_install value is passed .. VIB installation is skipping")
            else :
                logger.info("Continue with vib installation with given build..")
                vib_install_flag = vib_install(share_obj,vm_obj,aul_build_upgradepath,aul_upgrade_build)
            if skip_vmdeploy:
                logger.info ("skip_vmdeploy is set ..hence skipping vm deployment settings..")
            else:
                run_vm_stress_test (3, user_images)
        else:
            logger.error("Failed to upgrade AUL build to {}".format(aul_upgrade_build))
            raise AULException("FAILED to upgrade AUL .. skipping execution")

def install_qatools (share_obj,app_obj):
    logger.info ('Get VMware version before installing qatools')
    logger.info ("installing qa tools on appliance")
    logger.info ("copy qatools files on appliance")
    logger.info ("full path of qa tools path is {} and file name is {}".format(qatools_dirpath,qatools_filename))
    #134.111.87.198:/test1/projects/esx/6.7/PostKickStart/esx_postinstall.pl
    qatools_fullname = posixpath.join(upload_aul_loation, qatools_filename)
    copy_postinstall_file =copy_vm_image(share_obj,app_obj,qatools_dirpath,upload_aul_loation,qatools_filename)
    if copy_postinstall_file:
        logger.info("{} copied successfully..".format(qatools_filename))
        _ = app_obj.host_handle.execute_command('chmod 777 {}'.format(qatools_fullname))
        install_qatool = app_obj.install_tool('./{}'.format(qatools_filename))
        if install_qatool:
            logger.info("appliance reboot is in progress wait for system to come up..")
            time.sleep (60)
            verify_systemstatus = verify_multiple_pivots([app_ip])
            reconnect_handles([app_obj])
            logger.info("QAtools installation is success..")
        else:
            raise AULException ("qatools installation is not successful on appliance.. check logs")

    else:
        logger.error("{} failed to copy on appliance".format(qatools_filename))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d","--skip_signed_driver", help="skipping -n option during ft-install")
    parser.add_argument("-v","--skip_vibinstall", help="skipping vibtool installlation after AUL upgrade")
    parser.add_argument("-vm","--skip_vmdeploy", help="Skipping vm deployment settings")
    parser.add_argument("-i", "--vmimages", help="passing user defined vm images path")
    parser.add_argument("-n", "--vm_deploy_count", help="Total number of vms to be deploy")
    parser.add_argument("-q","--skip_postinstall_tool",help="skipping qatools installation ")
    args = parser.parse_args()

    if args.skip_signed_driver:
        skip_signed_driver=True
    else:
        skip_signed_driver=False

    if args.skip_vibinstall:
        skip_vibinstall=True
    else:
        skip_vibinstall=False

    if args.skip_vmdeploy:
        skip_vmdeploy=True
    else:
        skip_vmdeploy=False

    if args.vmimages:
        user_images=args.vmimages.split(',')
    else:
        user_images=list()

    if args.vm_deploy_count:
        vm_deploy_count=int(args.vm_deploy_count)
    else:
        vm_deploy_count=0

    if args.skip_postinstall_tool:
        skip_qatools=True
    else:
        skip_qatools=False
    #user_images = args.vmimages.split(',') if args.images else None
    logger.info("skip_vibinstall is {}".format(skip_vibinstall))
    logger.info("skip_signed_driver is {}".format(skip_signed_driver))
    logger.info("skip_vmdeploy is {}".format(skip_vmdeploy))
    logger.info("skip_qatools is {}".format(skip_vmdeploy))

    logger.info("Connect to vmware host")
    host_system = RemoteSystem(host_esx_ip, host_esx_id, host_esx_pwd)
    host_system.connect_host()

    vm_obj = VMUtils(host_system)

    logger.info('Connect to applicance')
    appliance_system = RemoteSystem(app_ip, host_esx_id, app_pwd)
    appliance_system.connect_host()

    app_obj = ApplianceUtils(appliance_system)

    logger.info("Connect to share to retrive vm template files and AUL build images")
    share_system = RemoteSystem(share_ip, share_username, share_pwd)
    share_system.connect_host()

    share_obj = ShareUtils(share_system)
    #get_vm_images_info(share_obj,'/ESX-VMTemplates/ESX-6.7')
    #aul_install(share_obj, app_obj, skip_signed_driver, skip_vibinstall, skip_vmdeploy,skip_qatools)
    run_vm_stress_test(user_images,vm_deploy_count)
    #app_obj.check_and_install_ovf_tool(share_obj, app_obj)
    #aul_upgrade (vm_obj,app_obj,share_obj,skip_signed_driver,skip_vibinstall)
    #install_qatools(share_obj,app_obj)
    #TODO:check preconditions in vib tools also
    #vib_install (share_obj, vm_obj, aul_build_upgradepath,aul_upgrade_build)
    #vm_obj.check_sync_status()
    '''
    vib_uninstall=vm_obj.vib_uninstall()
    if vib_uninstall:
        verify_systemstatus = verify_multiple_pivots([host_esx_ip, app_ip])
        reconnect_handles([vm_obj,app_obj])
        logger.info ("vib uninstalled successfully")
    else:
        logger.error ("problem in uninstalling vib tools")   
    '''