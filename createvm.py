#!/usr/bin/python3
"""docstring

"""


import subprocess
import os
import shutil
import errno
import multiprocessing
import argparse
import time
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
        self.dir = os.path.join(paths.packer_templates, name)
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


def count_workers():
    """Determine a number of processes for pool. Return int."""
    return multiprocessing.cpu_count() // 2


class Builder:
    """Build given list of virtual machines.

    Constructor require list of VMs as first positional argument.
    It is safe to specify single string here.
    Optional argument threads specify the count of worker processes
    those will actually build VMs from vmlist. The default is
    multiprocessing.cpu_count().
    """
    TIMEOUT = 30

    def __init__(self, vmlist, threads=count_workers()):
        if isinstance(vmlist, str):
            self.vmlist = [vmlist]
        else:
            self.vmlist = vmlist
        self.threads = threads

    def __str__(self):
        return "VM list:\n%s" % '\n'.join(self.vmlist)

    # def _callback(self, vm):
    #     print("{} successfully built".format(vm))
    #     time.sleep(self.TIMEOUT)

    def _build_pool(self, procs, lst):
        pool = multiprocessing.Pool(processes=procs)
        for vm in lst:
            pool.apply_async(build_vm, args=(vm,))
            time.sleep(self.TIMEOUT)
        pool.close()
        pool.join()

    def build(self):
        """Build VMs from self.vmlist."""
        vm_number = len(self.vmlist)
        if vm_number == 1:
            build_vm(self.vmlist[0])
        elif vm_number <= self.threads:
            self._build_pool(vm_number, self.vmlist)

        else:
            tmplist = self.vmlist
            while tmplist:
                self._build_pool(self.threads, tmplist[:self.threads])
                tmplist = tmplist[self.threads:]


class Importer:
    """Import VMs

    """
    pass


class Interface:
    """Options handler.

    """
    desc = "Virtual machines building and importing tool."

    def __init__(self):
        # Create top-level parser.
        self.parser = argparse.ArgumentParser(description=self.desc)
        subhelp = "See 'subcommand -h' for details"
        subparsers = self.parser.add_subparsers(help=subhelp)

        # Create parser for build command.
        build_help = """Build a number of virtual machines.
                    If no VM name specified it will try to discover
                    all templates from Packer 'templates' directory
                    and build VMs.
                    """
        parser_build = subparsers.add_parser('build', help=build_help)
        parser_build.add_argument('VM_NAME',
                                  nargs='*',
                                  help='virtual machine name'
                                  )
        parser_build.add_argument('-f', '--force',
                                  action='store_true',
                                  help='delete existing VM images'
                                  )
        parser_build.add_argument('-m', '--mail',
                                  action='store_true',
                                  help='send mail about new VM images'
                                  )

        # Create parser for import command.
        import_help = """Import specified virtual machines and group
                    then into 'smolensk_unstable'. If a directory
                    given as argument all images from directory
                    will be imported.
                    """
        parser_import = subparsers.add_parser('import', help=import_help)
        parser_import.add_argument('NAME',
                                   nargs='+',
                                   help='path to image or directory'
                                   )
        parser_import.add_argument('-f', '--force',
                                   action='store_true',
                                   help='delete existing VMs'
                                   )

    def get_args(self):
        """Parse arguments from command line."""
        return self.parser.parse_args()


if __name__ == '__main__':
    # Test code
    bld = Builder(['sudcm', 'sufs', 'suac', 'susrv', 'sudcs', 'suodcm', 'suoac'])
    # bld = Builder(['sudcm'])
    # bld = Builder(['sudcm', 'sufs', 'suodcm'])
    print(bld)
    bld.build()
    # iface = Interface()
    # iface.get_args()
    # print(iface.get_args())
