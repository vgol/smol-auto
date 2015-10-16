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
    pass


class VirtualMachine:
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
            subprocess.call(['VboxManage', 'unregistervm', self.name],
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
        curdir = os.getcwd()
        packer_main = os.path.join(paths.packer, 'bin', 'packer')
        os.chdir(self.dir)
        subprocess.call([packer_main, 'build', '-force',
                         '-var', 'headless=true', self.template])
        os.chdir(curdir)

if __name__ == '__main__':
    vm = VirtualMachine('sudcm')
    print(vm)
    try:
        vm.checkvm()
    except VirtualMachineExistError:
        vm.removevm()
    vm.buildvm()
