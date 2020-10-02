- originally used for el7->el8 migration of covscan.usersys.redhat.com
- based on https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/8/html-single/upgrading_from_rhel_7_to_rhel_8 :

# yum install subscription-manager
# subscription-manager register
# subscription-manager attach
# subscription-manager repos --enable rhel-7-server-rpms
# subscription-manager repos --enable rhel-7-server-extras-rpms
# subscription-manager release --unset
# yum update
# reboot
[...]
# yum install leapp leapp-repository
# export LEAPP_GRUB_DEVICE=/dev/vda
# leapp preupgrade

- if asked to do so, download an attachment from:

    https://access.redhat.com/articles/3664871

- transfer the file to the host being upgraded and unpack:
    $ scp /tmp/leapp-data11.tar.gz root@covscan.usersys.redhat.com:
    $ ssh root@covscan.usersys.redhat.com
    # tar -xzf leapp-data11.tar.gz -C /etc/leapp/files

# sed -re 's|^#(PermitRootLogin yes)$|\1|' -i /etc/ssh/sshd_config
# leapp upgrade
# reboot

Set up DDNS
-----------
- based on:
    https://mojo.redhat.com/people/jhutar/blog/2018/12/18/how-to-get-your-own-usersysredhatcom-hostname-aka-ddns
    http://hdn.corp.redhat.com/rhel8-csb/repoview/redhat-internal-ddns-client.html

# ssh root@10.37.135.114
# yum-config-manager --add-repo http://hdn.corp.redhat.com/rhel8-csb/
# rpm --import http://hdn.corp.redhat.com/rhel8-csb/RPM-GPG-KEY-helpdesk
# yum install redhat-internal-ddns-client
# redhat-internal-ddns-client.sh config
# redhat-internal-ddns-client.sh enable
# reboot
