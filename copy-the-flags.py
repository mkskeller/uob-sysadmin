#!/usr/bin/python

import getpass
import email
from imapclient import IMAPClient
import sys
import collections

print 'Usage: %s <username>' % sys.argv[0]

user = sys.argv[1] + '@bristol.ac.uk'

source = IMAPClient('imap.gmail.com', ssl=True)
dest = IMAPClient('outlook.office365.com', ssl=True)

source.login(user, getpass.getpass('Gmail password: '))
dest.login(user, getpass.getpass('Uni password: '))

flags = {}

print 'processing source'
for folder in source.list_folders():
    folder = folder[-1]
    try:
        source.select_folder(folder)
    except:
        continue
    print 'processing ', folder

    batch = 1000
    msgnums = source.search()
    print msgnums
    i = 0
    while msgnums[i:i+batch]:
        msgs = source.fetch(msgnums[i:i+batch], ['FLAGS', 'RFC822.HEADER'])
        for msgnum, data in msgs.iteritems():
            msg = email.message_from_string(data['RFC822.HEADER'])
            mid = msg['message-id']
            print mid, msg['from'], msg['subject']
            flags[mid] = data['FLAGS']
        i += batch

print 'processing dest'
for folder in dest.list_folders():
    folder = folder[-1]
    try:
        dest.select_folder(folder)
    except:
        continue
    print 'processing', folder
    msgnums = dest.search()
    print msgnums
    i = 0
    batch = 1000
    to_set = collections.defaultdict(list)
    while msgnums[i:i+batch]:
        msgs = source.fetch(msgnums[i:i+batch], ['FLAGS', 'RFC822.HEADER'])
        for msgnum, data in msgs.iteritems():
            msg = email.message_from_string(data['RFC822.HEADER'])
            mid = msg['message-id']
            if mid in flags:
                if flags[mid] != data['FLAGS']:
                    print mid, msg['from'], msg['subject'], \
                        flags[mid], data['FLAGS']
                    to_set[tuple(flags[mid])].append(msgnum)
        i += batch
    for f,msgnums in to_set.iteritems():
        print f, msgnums
        dest.set_flags(msgnums, f)

for conn in source, dest:
    conn.close_folder()
    conn.logout()
