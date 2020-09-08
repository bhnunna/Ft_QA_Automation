sed -i '/DEFROUTE=yes/ s/yes/no/'  /etc/sysconfig/network-scripts/ifcfg-bond1
sed -i '/BOOTPROTO=dhcp/ s/dhcp/static/' /etc/sysconfig/network-scripts/ifcfg-bond0
sed -i '$ a IPADDR=192.168.61.50'  /etc/sysconfig/network-scripts/ifcfg-bond0
sed -i '$ a NETMASK=255.255.255.0'  /etc/sysconfig/network-scripts/ifcfg-bond0
sed -i '$ a GATEWAY=192.168.61.1'  /etc/sysconfig/network-scripts/ifcfg-bond0
service network restart &
