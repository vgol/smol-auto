import pexpect
import subprocess
import os
import sys
import shutil
import shlex
from time import sleep


__author__ = 'vgol'
__version__ = '0.1'


# admin/admin and K/M passwords:
admin_admin = 'sUHRmHcf'
km = 'aiYPwN9p'
passwd = '/tmp/ald-passwd'


def setup_module():
    """Initialize ALD server using password file."""
    with open(passwd, 'w') as pwd:
        pwd.write("admin/admin:{a}\nK/M:{k}\n".format(a=admin_admin, k=km))
    os.chmod(passwd, 0o0600)
    init = "ald-init init --force --pass-file={}".format(passwd)
    subprocess.check_output(shlex.split(init))


def teardown_module():
    """Clean up ALD server."""
    destroy = "ald-init destroy --force --pass-file={}".format(passwd)
    subprocess.check_output(shlex.split(destroy))
    os.remove(passwd)
    clean_dirs('/ald_export_home')


def clean_dirs(export_dir):
    """If export_dir isn't empty then remove all subdirectories."""
    contain = os.listdir(export_dir)
    count = 0
    if contain:
        for home in contain:
            if os.path.isfile(home):
                continue
            shutil.rmtree(os.path.join(export_dir, home))
            count += 1
    return count


class TestCreateUsers:
    """Create users and groups."""
    create_user_dialog = {
        '01-padmin': "Введите пароль администратора ALD:",
        '02-puser': "Введите новый пароль для пользователя '%s':",
        '03-prepeat': "Повторите пароль:",
        '04-uid': "Введите идентификатор пользователя \(UID\) \[[0-9]+\]:",
        '05-gcreate': "Создать новую первичную группу .* \[yes\]:",
        '06-group': "Введите имя новой первичной .* \[%s\]:",
        '07-gid': "Введите идентификатор группы \(GID\) \[[0-9]+\]:",
        '08-gdesc': "Введите описание группы .*:",
        '09-shell': "Введите командную оболочку .* \[/bin/bash\]:",
        '10-fstype': "Введите тип ФС .* local, nfs, cifs\):",
        '11-fserv': "Введите сервер домашнего каталога .*:",
        '12-homedir': "Введите домашний .*\[/ald_home/%s\]: ",
        '13-fname': "Введите полное имя пользователя \[%s\]:",
        '14-gecos': "Введите параметр GECOS .*\[%s,,,\]:",
        '15-udesc': "Введите описание пользователя:",
        '16-policy': "Введите политику пароля для пользователя \[default\]:",
        '17-chpass': "Установить флаг .*\(yes/no\) \[no\]:",
        '18-correct': "Всё правильно\? \(yes/no\) \[no\]:"
    }

    def test_create_default_validname_user(self):
        """Create user with all default settings."""
        user = 'petrovich'
        user_password = 'xmsK02Kg'
        adm = pexpect.spawnu('ald-admin cmd', timeout=3)
        adm.logfile = sys.stdout
        enter = adm.sendline
        matched = adm.expect(['>( |\t)', pexpect.EOF, pexpect.TIMEOUT])
        assert matched == 0
        adm.sendline('user-add %s' % user)
        # Put admin and new user passwords
        adm.expect(self.create_user_dialog['01-padmin'])
        adm.sendline(admin_admin)
        adm.expect(self.create_user_dialog['02-puser'] % user)
        adm.sendline(user_password)
        adm.expect(self.create_user_dialog['03-prepeat'])
        adm.sendline(user_password)
        # Use default values for all other params
        # (Like user just press Enter).
        for key in sorted(self.create_user_dialog.keys())[3:-1]:
            if '%s' in self.create_user_dialog[key]:
                adm.expect(self.create_user_dialog[key] % user)
            else:
                adm.expect(self.create_user_dialog[key])
            enter()
        adm.expect(self.create_user_dialog['18-correct'])
        adm.sendline('y')
        sleep(1)
        # Checks
        userget = "ald-admin user-get {usr} -f --pass-file={pwd}"
        userget = userget.format(usr=user, pwd=passwd)
        sproc = subprocess.Popen(shlex.split(userget),
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        out, err = sproc.communicate()
        assert not err
        user_info = out.decode()
        assert user in user_info
        assert 'Domain Users' in user_info
        assert 'audio, scanner, users, video' in user_info
        assert 'Тип ФС домашнего каталога: по умолчанию' in user_info
        assert 'Тип ФС домашнего каталога: по умолчанию' in user_info
        assert '/ald_home/petrovich' in user_info
        assert '/bin/bash' in user_info
        assert 'petrovich,,,' in user_info
        assert 'default' in user_info
        assert 'заблокирован: Нет' in user_info
