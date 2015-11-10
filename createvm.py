#!/usr/bin/python3
"""docstring

"""


import subprocess
import os
import shutil
import errno
import paths


__author__ = 'vgol'


class VirtualMachineExistError(Exception):
    """VirtualMachine.checkvm() raise this exception if VM exists."""
    pass


class VirtualMachine:
    """Main class for VM handling.

    The constructor expects a name of Virtual Machine. It also gets some
    path to Packer templates from paths.py module. Through this class
    methods it is possible to build VM, to check if such VM already exists
    and to remove specified VM.
    """
    def __init__(self, name):
        self.name = name
        self.dir = os.path.join(paths.packer, 'templates', name)
        self.template = '{}.json'.format(name)

    def __str__(self):
        retstr = "Name: {0}\nDirectory: {1}\nTemplate: {2}\n"
        return retstr.format(self.name, self.dir, self.template)

    def checkvm(self):
        """Raise VirtualMachineError if such VM exists. Else return 0"""
        with open('/dev/null') as devnull:
            try:
                subprocess.check_call(['VBoxManage', 'showvminfo', self.name],
                                      stdout=devnull,
                                      stderr=devnull
                                      )
            except subprocess.CalledProcessError:
                return 0
        raise VirtualMachineExistError("{} already exist!".format(self.name))

    def removevm(self):
        """Unregister and remove Virtualbox virtual machine."""
        with open('/dev/null') as devnull:
            subprocess.call(['VBoxManage', 'unregistervm', self.name],
                            stderr=devnull)
        try:
            shutil.rmtree(os.path.join(paths.registered_vms, self.name))
        except OSError as exc:
            if exc.errno == errno.ENOENT:
                pass
            else:
                raise
        return 0

    def buildvm(self):
        """Build and export the virtual machine."""
        templ = os.path.join(self.dir, self.template)
        assert os.path.exists(templ), "%s not found" % self.template
        packer_main = os.path.join(paths.packer, 'bin', 'packer')
        assert os.path.exists(packer_main),\
            "Packer executable -- %s -- not found" % packer_main
        curdir = os.getcwd()
        os.chdir(self.dir)
        subprocess.call([packer_main, 'build', '-force',
                         '-var', 'headless=true', self.template])
        os.chdir(curdir)


def build_vm(vmname):
    """Build virtual machine. Remove existing if needed."""
    v_machine = VirtualMachine(vmname)
    try:
        v_machine.checkvm()
    except VirtualMachineExistError:
        v_machine.removevm()
    v_machine.buildvm()


if __name__ == '__main__':
    build_vm('sudcm')
