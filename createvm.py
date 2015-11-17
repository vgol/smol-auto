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
        return os.path.join(self.dir, paths.packer_export,
                            self.name + '.ova')


def build_vm(vmname):
    """Build virtual machine. Remove existing if needed."""
    v_machine = VirtualMachine(vmname)
    try:
        v_machine.checkvm()
    except VirtualMachineExistError:
        v_machine.removevm()
    return v_machine.buildvm()


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
    _TIMEOUT = 30
    results = []

    def __init__(self, vmlist, threads=count_workers()):
        if isinstance(vmlist, str):
            self.vmlist = [vmlist]
        else:
            self.vmlist = vmlist
        self.threads = threads

    def __str__(self):
        return "VM list:\n%s" % '\n'.join(self.vmlist)

    def _callback(self, vm):
        print("{} successfully built".format(vm))
        self.results.append(vm)

    def _build_pool(self, procs, lst):
        pool = multiprocessing.Pool(processes=procs)
        for vm in lst:
            pool.apply_async(build_vm, args=(vm,), callback=self._callback)
            time.sleep(self._TIMEOUT)
        pool.close()
        pool.join()

    def build(self):
        """Build VMs from self.vmlist."""
        vm_number = len(self.vmlist)
        if vm_number == 1:
            ova = build_vm(self.vmlist[0])
            self.results.append(ova)
        elif vm_number <= self.threads:
            self._build_pool(vm_number, self.vmlist)
        else:
            tmplist = self.vmlist
            while tmplist:
                self._build_pool(self.threads, tmplist[:self.threads])
                tmplist = tmplist[self.threads:]
        return self.results

    @staticmethod
    def _upload_dir():
        """Create the directory using current date."""
        upldir = os.path.join(paths.upload, time.strftime('%d-%m-%Y'))
        print("Upload directory: {}".format(upldir))
        try:
            os.mkdir(upldir)
        except OSError as exc:
            # If directory already exists just warn but
            #  don't raise the exception.
            if exc.errno == errno.EEXIST:
                print("WARNING: Directory already exist!",
                      "All images will be replaced!")
            else:
                raise
        return upldir

    @staticmethod
    def _remove_existing(img):
        """Remove img. Return img if removed. Else None."""
        if os.path.exists(img):
            os.unlink(img)
            return img

    def upload(self, ignore_missing=True):
        """Move VM images to paths.upload directory."""
        assert self.results, "Parameter 'results' is empty."
        upload_to = self._upload_dir()
        uploaded = []
        for image in self.results:
            basename = os.path.split(image)[1]
            dest = os.path.join(upload_to, basename)
            self._remove_existing(dest)
            try:
                shutil.move(image, upload_to)
                os.chmod(dest, 0o0644)
            except IOError as imgexc:
                # If ignore_missing is True then check for errno.
                # Else raise exception.
                if ignore_missing:
                    # Do not raise exception if image file not found.
                    if (imgexc.errno == errno.ENOENT and
                            imgexc.filename == image):
                        print("{} is missing. Skipping...")
                    else:
                        raise
                else:
                    raise
            else:
                uploaded.append(os.path.split(image)[1])
        return upload_to, uploaded

    def mail(self):
        """Send mail to employees."""
        print("Not implemented")


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
        self.args = self.parser.parse_args()

    @staticmethod
    def _discover():
        """Look into Packer templates dir and return template's list."""
        vms = []
        for file in os.listdir(paths.packer_templates):
            json = os.path.join(paths.packer_templates,
                                file, file + '.json')
            if os.path.exists(json):
                vms.append(file)
        return vms

    def _build(self):
        """Build and upload VMs through Builder class methods

        Build from given as arguments list of VMs. If no arguments
        given then call self._discover to determine the list of VMs
        from existing Packer templates.
        """
        if self.args.VM_NAME:
            bld = Builder(self.args.VM_NAME)
        else:
            bld = Builder(self._discover())
        bld.build()
        result = bld.upload()
        if self.args.mail:
            bld.mail()
        return result

    def _import(self):
        pass

    def main(self):
        """docstring will be here..."""
        if hasattr(self.args, 'VM_NAME'):
            self._build()
        else:
            self._import()


if __name__ == '__main__':
    iface = Interface()
    iface.main()
