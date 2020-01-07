Based on https://access.redhat.com/solutions/637583 :

# yum update
# reboot
[...]
# yum install subscription-manager
# subscription-manager register
# subscription-manager attach
# subscription-manager repos --enable rhel-6-server-extras-rpms
# subscription-manager repos --enable rhel-6-server-optional-rpms
# yum -y install preupgrade-assistant preupgrade-assistant-ui preupgrade-assistant-el6toel7 redhat-upgrade-tool httpd
# cp -v /etc/httpd/conf.d/99-preup-httpd.conf{.public,}
# setsebool httpd_run_preupgrade on
# iptables -I INPUT -m state --state NEW -p tcp --dport 8099 -j ACCEPT
# service httpd restart
# preupg -u http://localhost:8099/submit/
[...]
# preupg -u http://localhost:8099/submit/
[...]
# redhat-upgrade-tool --network 7.6 --instrepo http://download.eng.brq.redhat.com/released/RHEL-7/7.6/Server/x86_64/os/
# reboot
[...]
# grub2-mkconfig -o /boot/grub2/grub.cfg
# grub2-install /dev/sda
# reboot
[...]
# yum update
# reboot


If md-based RAID is used
------------------------
# cat /boot/grub/grub.cfg
# echo 'GRUB_CMDLINE_LINUX="rd.md.uuid=52770bb7:c89207c2:0726612d:f56ae5f0 rd.luks=0 rd.lvm.lv=vg_raid5/root rd.lvm.lv=vg_raid5/swap rd.dm=0"' >> /etc/default/grub
# grub2-mkconfig -o /boot/grub2/grub.cfg
# grub2-install /dev/sda
# reboot
