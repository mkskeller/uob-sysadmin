#!/usr/bin/python

import getpass
import email
from imapclient import IMAPClient
import sys
import collections

restrict = set()
#restrict = set(['\\Answered', '$Forwarded'])
ignore = set()
#ignore = set(['Junk', 'NonJunk', '\\Answered', '$Forwarded', '\\Flagged'])
ignore = set(['Junk', 'NonJunk'])

print 'Usage: %s <username>' % sys.argv[0]

user = sys.argv[1] + '@bristol.ac.uk'

source = IMAPClient('imap.gmail.com', ssl=True)
dest = IMAPClient('outlook.office365.com', ssl=True)

source.login(user, getpass.getpass('Gmail password: '))
dest.login(user, getpass.getpass('Uni password: '))

flags = collections.defaultdict(set)
log = open('flags', 'a')

print 'processing source'
for folder in source.list_folders():
    folder = folder[-1]
    try:
        source.select_folder(folder)
    except:
        continue
    print 'processing ', folder

    batch = 100
    msgnums = source.search()
    print msgnums
    i = 0
    while msgnums[i:i+batch]:
        msgs = source.fetch(msgnums[i:i+batch], ['FLAGS', 'RFC822.HEADER'])
        for msgnum, data in msgs.iteritems():
            msg = email.message_from_string(data['RFC822.HEADER'])
            mid = msg['message-id']
            print mid, msg['from'], msg['subject'], data['FLAGS']
            print >>log, mid, data['FLAGS']
            flags[mid] |= set(data['FLAGS'])
            if ignore:
                flags[mid] -= ignore
            if restrict:
                flags[mid] &= restrict
        i += batch
source.logout()

print 'processing dest'
for folder in dest.list_folders():
    folder = folder[-1]
    try:
        dest.select_folder(folder)
    except:
        continue
    print 'processing', folder
    msgnums = dest.search()
    #print msgnums
    i = 0
    batch = 1000
    to_set = collections.defaultdict(list)
    n_processed = 0
    while msgnums[i:i+batch]:
        msgs = dest.fetch(msgnums[i:i+batch], ['FLAGS', 'RFC822.HEADER'])
        for msgnum, data in msgs.iteritems():
            msg = email.message_from_string(data['RFC822.HEADER'])
            mid = msg['message-id']
            dest_flags = set(data['FLAGS'])
            if mid in flags:
                if ignore:
                    dest_flags -= ignore
                if restrict:
                    dest_flags &= restrict
                if flags[mid] != dest_flags:
                    note = 'changed'
                    if flags[mid].issubset(dest_flags):
                        note = 'added'
                    elif dest_flags.issubset(flags[mid]):
                        note = 'removed'
                    print 'flags', note, mid, msg['from'], msg['subject'], \
                        flags[mid], dest_flags
                    to_set[tuple(flags[mid])].append(msgnum)
            # else:
            #     print 'new', mid, msg['from'], msg['subject']
            n_processed += 1
        i += batch
    print n_processed, 'messages'
dest.logout()
