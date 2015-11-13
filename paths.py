"""The module contains the list of required paths.

packer - absolute path to Packer directory;
packer_templates - absolute path to Packer templates directory;
packer_export - relative (from template dir) path to exported VM;
registered_vms - VM files according to VirtualBox settings;
upload - where to put exported VMs.
"""


from os.path import join


__author__ = 'vgol'


packer = "/home/vgol/packer"
packer_templates = join(packer, "templates")
packer_export = "export"
registered_vms = "/home/vgol/storage/VirtualBox VMs/smolensk_unstable"
upload = "/home/ftp/vm"
