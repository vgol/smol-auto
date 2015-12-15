"""The module contains the list of required paths.

packer - absolute path to Packer directory;
packer_templates - absolute path to Packer templates directory;
packer_export - relative (from template dir) path to exported VM;
vm_group - testing VM group;
upload - where to put exported VMs.
"""


from os.path import join


__author__ = 'vgol'
__version__ = '1.0.0'


packer = "/home/vgol/packer"
packer_templates = join(packer, "templates")
packer_export = "export"
vm_group = "smolensk_unstable"
upload = "/home/ftp/vm"
