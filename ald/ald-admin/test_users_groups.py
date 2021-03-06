"""Test module for ald-admin user-* and group-* commands."""

import pexpect
import pytest
import subprocess
import os
import sys
import shutil
import shlex
import string
import random


__author__ = 'vgol'
__version__ = '0.2.2'


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


def password_generator(length=8):
    """Create random password. Return str."""
    char_classes = [
        string.ascii_lowercase,
        string.ascii_uppercase,
        string.digits,
        string.punctuation
    ]
    password = ''
    while len(password) < length:
        if len(char_classes) > 0:
            char_class = random.choice(char_classes)
            char_classes.remove(char_class)
        else:
            char_class = string.ascii_letters + string.digits
        char_class_count = random.randint(2, 3)

        while char_class_count > 0:
            password = password + random.choice(char_class)
            char_class_count -= 1

    return password[:length]


@pytest.fixture(scope='module')
def ald_fixture(request):
    """Initialize and destroy ALD databases. Return admin/admin password."""
    admin_admin = password_generator()
    km = password_generator()
    passwd = '/tmp/ald-passwd'
    with open(passwd, 'w') as pwd:
        pwd.write("admin/admin:{a}\nK/M:{k}\n".format(a=admin_admin, k=km))
    os.chmod(passwd, 0o0600)
    init = "ald-init init --force --pass-file={}".format(passwd)
    subprocess.check_output(shlex.split(init))

    def destroyit():
        """This finalizer destroys ALD databases."""
        destroy = "ald-init destroy --force --pass-file={}".format(passwd)
        subprocess.check_output(shlex.split(destroy))
        os.remove(passwd)
        clean_dirs('/ald_export_home')

    request.addfinalizer(destroyit)
    return admin_admin, passwd


def valid_usernames_generator():
    """Generate the list of valid usernames. Return list."""
    # Generate one-character name and a name with all digits '_' and ' '.
    max_length = 31
    names = [
        random.choice(string.ascii_lowercase),
        random.choice(string.ascii_lowercase) + string.digits + '_' + '-',
    ]
    valid_chars = string.ascii_lowercase + string.digits + '_' + '-'
    # Create a name with max length.
    long = random.choice(string.ascii_lowercase)
    while len(long) <= max_length - 1:
        long = long + random.choice(valid_chars)
    names.append(long)
    # Create some valid random names.
    while len(names) < 6:
        length = random.randint(1, max_length - 1)
        # First character must be ASCII lowercase.
        name = random.choice(string.ascii_lowercase)
        while len(name) <= length:
            name = name + random.choice(valid_chars)
        names.append(name)
    return names


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

    @pytest.mark.parametrize('user', valid_usernames_generator())
    def test_default_validname_user(self, ald_fixture, user):
        """Create user with all default settings."""
        user_password = password_generator()
        adm = pexpect.spawnu('ald-admin cmd', timeout=3)
        adm.logfile = sys.stdout
        enter = adm.sendline
        matched = adm.expect(['>( |\t)', pexpect.EOF, pexpect.TIMEOUT])
        assert matched == 0
        adm.sendline('user-add %s' % user)
        # Put admin and new user passwords
        adm.expect(self.create_user_dialog['01-padmin'])
        adm.sendline(ald_fixture[0])
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
        adm.expect('> ')
        adm.sendline('exit')
        adm.wait()
        # Checks
        assert adm.exitstatus == 0
        assert not adm.isalive()
        userget = "ald-admin user-get {usr} -f --pass-file={pwd}"
        userget = userget.format(usr=user, pwd=ald_fixture[1])
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
        assert '/ald_home/%s' % user in user_info
        assert '/bin/bash' in user_info
        assert '%s,,,' % user in user_info
        assert 'default' in user_info
        assert 'заблокирован: Нет' in user_info
