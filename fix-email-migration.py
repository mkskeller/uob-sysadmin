#!/usr/bin/python

import getpass
import email
from imapclient import IMAPClient
import sys

print 'Usage: %s <username> [INBOX,]<folder1>,<folder2>,...' % sys.argv[0]

user = sys.argv[1] + '@bristol.ac.uk'
folders = sys.argv[2].split(',')

source = IMAPClient('imap.gmail.com', ssl=True)
dest = IMAPClient('outlook.office365.com', ssl=True)

source.login(user, getpass.getpass('Gmail password: '))
dest.login(user, getpass.getpass('Uni password: '))

for folder in folders:
    source.select_folder(folder)
    dest.select_folder(folder)

    full_fetch = ['FLAGS', 'INTERNALDATE', 'RFC822']

    batch = 100
    msgnums = dest.search(['HEADER', 'Content-Type', 'multipart/signed;'])
    print msgnums
    i = 0
    while msgnums[i:i+batch]:
        msgs = dest.fetch(msgnums[i:i+batch], full_fetch)
        for msgnum, data in msgs.iteritems():
            msg = email.message_from_string(data['RFC822'])
            mid = msg['message-id']
            print mid, msg['from'], msg['subject']
            source_data = source.fetch(source.search(
                ['HEADER', 'Message-Id', mid]), full_fetch).values()[0]
            dest.delete_messages([msgnum])
            dest.append(folder, source_data['RFC822'], source_data['FLAGS'], \
                        source_data['INTERNALDATE'])
        i += batch

for conn in source, dest:
    conn.close_folder()
    conn.logout()
