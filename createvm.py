#!/usr/bin/python3
"""docstring

"""


from sys import stderr
from email.mime.text import MIMEText
from email.header import Header
import subprocess
import os
import shutil
import errno
import multiprocessing
import argparse
import time
import smtplib
import paths
import infomail


__author__ = 'vgol'


class VirtualMachineExistsError(Exception):
    """VirtualMachine.checkvm() raise this exception if VM exists."""
    pass


def get_machine_folder():
    """Determine default machine folder. Return str."""
    properties = subprocess.check_output(['VBoxManage', 'list',
                                          'systemproperties'])
    prop_name = "Default machine folder:"
    skip = len(prop_name)
    machine_folder = ''
    for line in properties.decode().split('\n'):
        if prop_name in line:
            machine_folder = line[skip:].lstrip()
            break
    assert machine_folder != '', "Default machine folder is unknown"
    return machine_folder


class VirtualMachine:
    """Main class for VM handling.

    The constructor expects a name of Virtual Machine. It also gets some
    path to Packer templates from paths.py module. Through this class
    methods it is possible to build VM, to check if such VM already exists
    and to remove specified VM.
    """
    def __init__(self, name):
        assert os.path.exists('/usr/bin/VBoxManage'), "VBoxManage not found"
        self.name = name
        self.dir = os.path.join(paths.packer_templates, name)
        self.template = '{}.json'.format(name)

    def __str__(self):
        retstr = "Name: {0}\nDirectory: {1}\nTemplate: {2}\n"
        return retstr.format(self.name, self.dir, self.template)

    def _checkreg(self):
        """Check for VM using VBoxManage.

         If exist return True. Else return False
         """
        retval = True
        try:
            with open('/dev/null') as devnull:
                subprocess.check_call(['VBoxManage', 'showvminfo', self.name],
                                      stdout=devnull,
                                      stderr=devnull
                                      )
        except subprocess.CalledProcessError:
            retval = False
        return retval

    def _checkfiles(self):
        """Check for VM files. Return True if exists. Else False."""
        mf = get_machine_folder()
        inroot = os.path.exists(os.path.join(mf, self.name))
        insu = os.path.exists(os.path.join(mf, paths.vm_group, self.name))
        return inroot or insu

    def checkvm(self):
        """Raise VirtualMachineError if such VM exists. Else return 0"""
        if self._checkreg() or self._checkfiles():
            err = "{} already exist!".format(self.name)
            raise VirtualMachineExistsError(err)
        return 0

    def removevm(self):
        """Unregister and remove Virtualbox virtual machine."""
        # Try to unregister VM. Ignore errors.
        with open('/dev/null') as devnull:
            subprocess.call(['VBoxManage', 'unregistervm', self.name],
                            stderr=devnull)

        # Try to remove VM files from paths.vm_group. If no such file
        # then try to remove it from VirtualBox default machine folder.
        mf = get_machine_folder()
        try:
            shutil.rmtree(os.path.join(mf, paths.vm_group, self.name))
        except OSError as exc:
            if exc.errno == errno.ENOENT:
                shutil.rmtree(os.path.join(mf, self.name))
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

    def _groupvm(self):
        group = '/' + paths.vm_group
        subprocess.call(['VBoxManage', 'modifyvm', self.name,
                         '--groups', group])

    def importvm(self, ova):
        """Import VM and group into paths.vm_group."""
        assert os.path.exists(ova), "{} not found" % ova
        subprocess.call(['VBoxManage', 'import', ova,
                        '--options', 'keepallmacs'])
        time.sleep(10)
        self._groupvm()
        return self.name


def build_vm(vmname):
    """Build virtual machine. Remove existing if needed."""
    v_machine = VirtualMachine(vmname)
    try:
        v_machine.checkvm()
    except VirtualMachineExistsError:
        v_machine.removevm()
    return v_machine.buildvm()


def just_import(ova):
    """Import VM and group it. Return str.

    Import VM from specified ova and return VM name.
    If VM with such name already exists raise VirtualMachineExistsError.
    """
    name = os.path.split(ova)[1].split('.')[0]
    v_machine = VirtualMachine(name)
    # This must throw exception if such VM already exists.
    try:
        v_machine.checkvm()
    except VirtualMachineExistsError:
        print("WARNING: %s already exists. Skipping...")
    else:
        v_machine.importvm(ova)
    return name


def force_import(ova):
    """Import and group VM. Remove existing if needed."""
    name = os.path.split(ova)[1].split('.')[0]
    v_machine = VirtualMachine(name)
    try:
        v_machine.checkvm()
    except VirtualMachineExistsError:
        v_machine.removevm()
    v_machine.importvm(ova)
    return name


def count_workers():
    """Determine a number of processes for pool. Return int."""
    return multiprocessing.cpu_count() // 2


class VMHandler:
    """Base class for dealing with lists of VirtualMachines

    This class must be subclassed.
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
        print("{} successfully handled".format(vm))
        self.results.append(vm)


class Builder(VMHandler):
    """Build given list of virtual machines.

    Constructor require list of VMs as first positional argument.
    It is safe to specify single string here.
    Optional argument threads specify the count of worker processes
    those will actually build VMs from vmlist. The default is
    multiprocessing.cpu_count().
    """
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
                        print("{} is missing. Skipping...", file=stderr)
                    else:
                        raise
                else:
                    raise
            else:
                uploaded.append(os.path.split(image)[1])
        return upload_to, uploaded

    @staticmethod
    def _prepare_message(msg):
        """Prepare MIME message. Return email.mime.MIMEText."""
        msg_mime = MIMEText(msg, 'text', 'utf-8')
        msg_mime['From'] = Header(infomail.fromaddr, charset='utf-8')
        msg_mime['To'] = Header(', '.join(infomail.toaddrs),
                                charset='utf-8')
        msg_mime['Subject'] = Header("VirtualBox images built",
                                     charset='utf-8')
        return msg_mime

    def mail(self, upload_dir):
        """Send info mail using data from imfomail.py

        Argument upload_dir required for making download URL
         for recipients.
        Prepare and send message through smtplib.SMTP
        """
        url = infomail.download_url.format(os.path.split(upload_dir)[1])
        mymessage = infomail.text_message.format(url)
        mymessage = self._prepare_message(mymessage)
        errpref = "SMTP Problem:"
        smtpconn = smtplib.SMTP(infomail.smtphost, infomail.smtpport)
        try:
            smtpconn.sendmail(infomail.fromaddr,
                              infomail.toaddrs,
                              mymessage.as_string())
        except smtplib.SMTPRecipientsRefused:
            print(errpref, end=' ', file=stderr)
            print("All recipients {} refused".format(infomail.toaddrs),
                  file=stderr)
        except smtplib.SMTPHeloError:
            print(errpref, end=' ', file=stderr)
            print("Server didn't reply properly to the HELLO", file=stderr)
        except smtplib.SMTPSenderRefused:
            print(errpref, "Server didn't accept sender", infomail.fromaddr,
                  file=stderr)
        except smtplib.SMTPDataError:
            print(errpref, "Server didn't accept mail data", file=stderr)
        finally:
            smtpconn.quit()


class Importer(VMHandler):
    """Import given list of virtual machines.

    Constructor require list of exported VMs (.ova) as first
    positional argument. It is safe to specify single string here.
    Optional argument threads specify the count of worker processes
    those will actually import VMs from vmlist. The default is
    multiprocessing.cpu_count().
    """
    def _import_pool(self, procs, lst, func):
        pool = multiprocessing.Pool(processes=procs)
        for vm in lst:
            pool.apply_async(func, args=(vm,), callback=self._callback)
            time.sleep(self._TIMEOUT)
        pool.close()
        pool.join()

    def vmimport(self, func=just_import):
        """Import virtual machines from self.vmlist."""
        ovas = len(self.vmlist)
        if ovas == 1:
            vmname = func(self.vmlist[0])
            self.results.append(vmname)
        elif ovas <= self.threads:
            self._import_pool(ovas, self.vmlist, func)
        else:
            tmplist = self.vmlist
            while tmplist:
                self._import_pool(self.threads, tmplist[:self.threads], func)
                tmplist = tmplist[self.threads:]
        return self.results


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
    def _discover_templates():
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
            bld = Builder(self._discover_templates())
        bld.build()
        result = bld.upload()
        if self.args.mail:
            bld.mail(result[0])
        return result

    @staticmethod
    def _ova_from_dir(directory):
        """Retrieve list of .ova from dir. Return list."""
        res = []
        for file in os.listdir(directory):
            if file.endswith('.ova'):
                res.append(os.path.join(directory, file))
        return res

    def _prepare_ovas(self):
        """Get list of .ova from self.args. Return list."""
        ovalist = []
        for name in self.args.NAME:
            if name.endswith('.ova'):
                ovalist.append(name)
            elif os.path.isdir(name):
                ovalist.extend(self._ova_from_dir(name))
            else:
                print("%s doesn't looks like directory or OVA" % name,
                      file=stderr)
        return ovalist

    def _import(self):
        """Get the list of .ova from arguments and import. Return list."""
        if self.args.force:
            myfunc = force_import
        else:
            myfunc = just_import
        ovas = self._prepare_ovas()
        if len(ovas) > 0:
            imprt = Importer(ovas)
            result = imprt.vmimport(func=myfunc)
        else:
            print("No images found in %s" % self.args.NAME, file=stderr)
            result = None
        return result

    def main(self):
        """Perform actions according to the given command and options.

        Build command:
        Build from given as arguments list of VMs. If no arguments
        given then call self._discover to determine the list of VMs
        from existing Packer templates.

        Import command:
        Expect at least one argument. If it is directory then all
        images from that directory will be exported. If it is image
        or list of images then it will import all of it.
        """
        if hasattr(self.args, 'VM_NAME'):
            self._build()
        else:
            self._import()


if __name__ == '__main__':
    iface = Interface()
    iface.main()
