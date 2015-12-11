"""Module used by createvm.py.

smptphost - SMTP server host name;
smtpport - SMTP port;
fromaddr - email address from which to send the message;
toaddrs - the list of email addresses to which the message
 will be sent;
download_url - URL for downloading VM images (will be placed
 message);
text_message - the body of message.
"""


__author__ = 'vgol'
__verson__ = '1.0'


smtphost = 'smtp.cct.rbt'
smtpport = 25
fromaddr = 'vgol@cct.rbt'
toaddrs = ['vgol@cct.rbt', 'tyurin@cct.rbt', 'struchkov@cct.rbt',
           'kukolev@cct.rbt', 'anohov@cct.rbt', 'yarik13@cct.rbt']
download_url = "ftp://vgol2.cct.rbt/vm/{}"
text_message = """
Образы виртуальных машин доступны для скачивания: {}

"""
