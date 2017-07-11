#!/usr/bin/python

import getpass
import email
from imapclient import IMAPClient
import sys

print 'Usage: %s <username>' % sys.argv[0]

user = sys.argv[1] + '@bristol.ac.uk'

source = IMAPClient('imap.gmail.com', ssl=True)
dest = IMAPClient('outlook.office365.com', ssl=True)

source.login(user, getpass.getpass('Gmail password: '))
dest.login(user, getpass.getpass('Uni password: '))

for folder in source.list_folders():
    folder = folder[-1]
    try:
        source.select_folder(folder)
        dest.select_folder(folder)
    except:
        continue
    print 'processing ', folder

    full_fetch = ['FLAGS', 'INTERNALDATE', 'RFC822']

    batch = 100
    msgnums = source.search('OR ANSWERED FLAGGED')
    print msgnums
    i = 0
    while msgnums[i:i+batch]:
        msgs = source.fetch(msgnums[i:i+batch], ['FLAGS', 'RFC822.HEADER'])
        for msgnum, data in msgs.iteritems():
            msg = email.message_from_string(data['RFC822.HEADER'])
            mid = msg['message-id']
            print mid, msg['from'], msg['subject']
            dest.set_flags(msgnum, data['FLAGS'])
        i += batch

for conn in source, dest:
    conn.close_folder()
    conn.logout()
