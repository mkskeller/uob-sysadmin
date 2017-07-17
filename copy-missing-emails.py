#!/usr/bin/python

import getpass
import email
from imapclient import IMAPClient
import sys
import collections
import traceback

print 'Usage: %s <username>' % sys.argv[0]

user = sys.argv[1] + '@bristol.ac.uk'

source = IMAPClient('imap.gmail.com', ssl=True)
dest = IMAPClient('outlook.office365.com', ssl=True)

source.login(user, getpass.getpass('Gmail password: '))
dest.login(user, getpass.getpass('Uni password: '))

folders = collections.defaultdict(lambda: [None, None])
id_fetch = 'BODY[HEADER.FIELDS (MESSAGE-ID SUBJECT FROM)]'

for j, conn in reversed(list(enumerate((source, dest)))):
    for folder in conn.list_folders():
        folder_name = folder[-1]
        print 'processing ', folder_name
        try:
            conn.select_folder(folder_name)
        except:
            continue

        batch = 1000
        msgnums = conn.search()
        i = 0
        while msgnums[i:i+batch]:
            print msgnums[i:i+batch]
            msgs = conn.fetch(msgnums[i:i+batch], [id_fetch])
            for msgnum, data in msgs.iteritems():
                try:
                    msg = email.message_from_string(data[id_fetch])
                except:
                    print data
                    raise
                mid = msg['message-id']
                print mid, msg['from'], msg['subject']
                if folders[mid][j] is None or '[' in folders[mid][j]:
                    folders[mid][j] = folder_name
            i += batch

full_fetch = ['FLAGS', 'INTERNALDATE', 'RFC822']

failed = {}

for uid in folders:
    if folders[uid][1] is None:
        print 'missing', uid, folders[uid][0]
        source.select_folder(folders[uid][0])
        dest_folder = 'recovered/' + folders[uid][0]
        if dest_folder not in (x[-1] for x in dest.list_folders()):
            dest.create_folder(dest_folder)
        try:
            source_data = source.fetch(source.search(
                '(HEADER Message-Id "%s")' % uid.strip()), \
                                       full_fetch).values()[0]
            dest.append(dest_folder, source_data['RFC822'], \
                        source_data['FLAGS'], \
                        source_data['INTERNALDATE'])
        except:
            failed[uid] = traceback.format_exc()

print 'failed', failed

for conn in source, dest:
    conn.close_folder()
    conn.logout()
