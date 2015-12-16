import pytest
import shlex
import os
import re
from subprocess import Popen, PIPE, call


__author__ = 'vgol'
__version__ = '0.1.0'


# Test data.
fs_types = [
    'ext2',
    'ext3',
    'ext4',
    'vfat',
    'ntfs',
    'minix',
    'exfat'
]
# FS from this list expected to fail test_mac.
mac_xfail = [
    'vfat',
    'ntfs',
    'minix',
    'exfat'
]
# FS from this list expected to fail test_audit.
audit_xfail = [
    'vfat',
    'minix',
    'exfat'
]
tfile = '/mnt/testfile'


@pytest.fixture(
    scope='function',
    params=fs_types
)
def preparefs(request):
    """Create image with FS. Return path as str."""
    image = os.path.join('/tmp', 'image-' + request.param)
    img_size = 2000000
    with open(image, 'wb') as img, open('/dev/zero', 'rb') as zero:
        img.write(zero.read(img_size))
    if re.match('(ext[2-4]|ntfs)', request.param):
        _create_img_default(request.param, image)
    else:
        _create_img_simple(request.param, image)

    def cleaning():
        call(['umount', image])
        os.remove(image)

    request.addfinalizer(cleaning)
    return image


def _create_img_default(fs, img):
    """Default function for preparing image.

    It works for ext2, ext3, ext4, ntfs.
    """
    mkfs = "/sbin/mkfs.{0} -F {1}".format(fs, img)
    call(shlex.split(mkfs))
    mount = "mount -o loop {img} /mnt".format(img=img)
    call(shlex.split(mount))


def _create_img_simple(fs, img):
    """Create image and make FS without '-F' flag.

    It works for exFAT, FAT32, minix.
    """
    mkfs = "/sbin/mkfs.{0} {1}".format(fs, img)
    call(shlex.split(mkfs))
    mount = "mount -o loop {img} /mnt".format(img=img)
    call(shlex.split(mount))


def _mount_img(image):
    """Mount img to /mnt. Return tuple of bytes."""
    mount_image = "mount -o loop {img} /mnt".format(img=image)
    mnt = Popen(shlex.split(mount_image), stdout=PIPE, stderr=PIPE)
    output = mnt.communicate()
    return output


def _get_label(file):
    """Get MAC label from file. Return str."""
    cmd = "pdp-ls -Mn {}".format(file)
    get_lbl = Popen(shlex.split(cmd), stdout=PIPE, stderr=PIPE)
    output = get_lbl.communicate()
    return output[0].decode()


def _get_aud(file):
    """Get audit flags from file. Return str."""
    cmd = "getfaud {}".format(file)
    get_aud = Popen(shlex.split(cmd), stdout=PIPE, stderr=PIPE)
    output = get_aud.communicate()
    return output[0].decode()


def _fs_from_image(img):
    """Get fs name from image path. Return str."""
    return os.path.split(img)[1][len('image-'):]


def test_read_write(preparefs):
    """Try to read and write into image."""
    # Try to write.
    with open(tfile, 'wb') as tf:
        tf.write(b'this is test')
    assert os.path.exists(tfile)
    # Try to read.
    with open(tfile, 'rb') as tf:
        data = tf.read()
    assert data == b'this is test'


@pytest.fixture(scope='function')
def set_mount_point_label(request):
    """Set label to mount point. And return as was"""
    call(shlex.split("pdpl-file 1:0:0:ccnr /mnt"))

    def lbl_back():
        call(shlex.split("pdpl-file 0:0:0:0 /mnt"))

    request.addfinalizer(lbl_back)


def test_mac(preparefs, set_mount_point_label):
    """Check MAC attributes."""
    # Mark as expected fail for no xattr fs.
    if _fs_from_image(preparefs) in mac_xfail:
        pytest.xfail('xattrs not supported')
    with open(tfile, 'wb') as tf:
        tf.write(b'this is secret')
    assert os.path.exists(tfile)
    call(shlex.split("pdpl-file 1:0:0:0 {}".format(tfile)))
    lbl = _get_label(tfile)
    assert '1:0:0:0' in lbl
    call('sync')
    call(['umount', '/mnt'])
    mount_result = _mount_img(preparefs)
    assert not mount_result[1], mount_result[1].decode()
    lbl = _get_label(tfile)
    assert '1:0:0:0' in lbl
    os.remove(tfile)


def test_audit(preparefs):
    """Check audit flags."""
    # Mark as expected fail for no xattr fs.
    if _fs_from_image(preparefs) in audit_xfail:
        pytest.xfail('xattrs not supported')
    with open(tfile, 'wb') as tf:
        tf.write(b'this is for test')
    assert os.path.exists(tfile)
    call(shlex.split("setfaud -m o:o {}".format(tfile)))
    lbl = _get_aud(tfile)
    assert 'o:o:o' in lbl
    call('sync')
    call(['umount', '/mnt'])
    mount_result = _mount_img(preparefs)
    assert not mount_result[1], mount_result[1].decode()
    lbl = _get_aud(tfile)
    assert 'o:o:o' in lbl
