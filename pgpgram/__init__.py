#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#    PGPgram
#
#    ----------------------------------------------------------------------
#    Copyright © 2018, 2019, 2020  Pellegrino Prevete
#
#    All rights reserved
#    ----------------------------------------------------------------------
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

import inspect
import logging
import string
from os.path import abspath, basename, exists, dirname, getsize, isfile, isdir, realpath
from os.path import join as path_join
from os import chdir as cd
from os import listdir as ls
from os import remove as rm
from os import mkdir, symlink, getcwd
from os import walk
from pickle import dump as pickle_dump
from pickle import load as pickle_load
from pprint import pprint
from random import SystemRandom as random
from setproctitle import setproctitle
from subprocess import Popen, PIPE
from subprocess import check_output as sh
from subprocess import getoutput

from argparse import ArgumentParser
from trovotutto import PGPgramDb, Index
from xdg import BaseDirectory

from .td import Td
from .color import Color

name = "pgpgram"
version = "0.1.6"

setproctitle(name)

color = Color()

def save(variable, path):
    """Save variable on given path using Pickle
    
    Args:
        variable: what to save
        path (str): path of the output
    """
    with open(path, 'wb') as f:
        pickle_dump(variable, f)
    f.close()

def load(path):
    """Load variable from Pickle file
    
    Args:
        path (str): path of the file to load

    Returns:
        variable read from path
    """
    with open(path, 'rb') as f:
        variable = pickle_load(f)
    f.close()
    return variable

def random_id(N):
    """ Returns a random alphanumeric (ASCII) string of given length
    
    Args:
        N (int):
       
    Returns:
        (str) random alphanumeric string 
    """
    return ''.join(random().choice(string.ascii_letters + string.digits) for _ in range(N))

class MessageInException(Exception):
    def __init__(self, msg):
        print("{0}".format(msg))
        pass

class Db:
    """The data handling object for pgpgram.

    Args:
        verbose (int): level of
    """

    config_path = BaseDirectory.save_config_path(name)
    data_path = BaseDirectory.save_data_path(name)
    cache_path = BaseDirectory.save_cache_path(name)
    executable_path = dirname(realpath(__file__))

    def __init__(self, verbose=0):
        self.verbose = verbose

        # Load files list from disk into 'files' attribute
        try:
            self.files = load(path_join(self.config_path, "files.pkl"))
        except FileNotFoundError as e:
            if verbose > 0:
                pprint("files pickle not found in path, initializing")
            self.files = []

        # Load configuration from disk into 'config' attribute
        try:
            self.config = load(path_join(self.config_path, "config.pkl"))

        except FileNotFoundError as e:
            # Init configuration
            if verbose > 0:
                pprint("Config file not found in path, initializing")

            self.config = {"db key":random_id(20)}

            # Paths
            index_dir = path_join(self.data_path, "index")
            tdlib_dir = path_join(self.data_path, 'tdlib')
            tdlib_config_symlink = path_join(self.config_path, "tdlib")
            tdlib_documents_dir = path_join(self.cache_path, "documents")
            tdlib_documents_symlink = path_join(tdlib_dir, "documents")

            # Init paths
            if not exists(index_dir):
                mkdir(index_dir)

            if not exists(tdlib_dir):
                mkdir(tdlib_dir)
                mkdir(tdlib_documents_dir)
                symlink(tdlib_dir, tdlib_config_symlink)
                symlink(tdlib_documents_dir, tdlib_documents_symlink)

        # Load index
        try:
            self.index = load(path_join(self.data_path, "index.pkl"))
        except:
            if verbose > 0:
                 print("index still not built")
        self.save()

    def save(self):
        """Save db

            Formats db in a format compatible with trovotutto,
            builds the trovotutto index and then save the following to disk:
            - search index
            - files list
            - configuration
        """
        pgpgram_db = PGPgramDb(self, filetype="any", exclude=[], update=True)
        self.index = Index(pgpgram_db, slb=3, verbose=self.verbose)
        save(self.index, path_join(self.data_path, "index.pkl"))
        save(self.files, path_join(self.config_path, "files.pkl"))
        save(self.config, path_join(self.config_path, "config.pkl"))

    def search(self, query, 
                     path=getcwd(), 
                     filetype="any", 
                     exclude=[], 
                     results_number=10, 
                     verbose=0):

        if filetype != "any" or path != getcwd():
            word_shortest = min([len(w) for w in query.split(" ")])
            pgpgram_db_kwargs = {'path': path,
                                 'filetype': filetype,
                                 'exclude': exclude,
                                 'update': True}
            pgpgram_db = PGPgramDb(self, **pgpgram_db_kwargs)
            self.index = Index(pgpgram_db, slb=word_shortest, verbose=verbose)

        results = self.index.search(query)

        self.display_results(results[:results_number])

        if results != []:
            choice = int(input("Select file to restore (number): "))
            f = [d for d in self.files if d['path'] == results[choice]][-1]["name"]
            restore = Restore(f, download_directory=getcwd(), verbose=verbose) 

    def display_results(self, results):
        for i,f in enumerate(results):
            g = f.split("/")
            title_string = "{}{}. {}{}{}".format(color.GREEN + color.BOLD,
                                                 i,
                                                 color.BLUE,
                                                 g[-1],
                                                 color.END)
            subtitle_string = "{}{}{}\n".format(color.GRAY,
                                                f,
                                                color.END)
            print(title_string)
            print(subtitle_string)


class Backup:
    """Backup file on telegram

    It encrypts, split and then upload files to Telegram clouds.
    Communication with telegram happens through :doc:`Td <./pgpgram.td>` class, which is a poorly written
    wrapper around libtdjson. Backups uniqueness is obtained through sha256sums.

    Args:
        f (str): path of the file to backup;
        ignore_duplicate (bool): create duplicate backup;
        size (int): specify size of the chunks the file will be split; 
        verbose (int): integer indicating level of verbose
            * 1 just pgpgram verbose
            * 2 include tdjson verbose
            * 3 to 5 are specific to tdjson.
    """

    def __init__(self, f, ignore_duplicate=False, size='100', verbose=2):

        try:
            current_path = getcwd()
            f = abspath(f)
            self.verbose = verbose
            self.db = Db(verbose)
            """Database class instance"""
            cd(self.db.config_path)

            # Instantiates telegram client
            td = Td(tdjson_path=self.db.executable_path, db_key=self.db.config["db key"], verbosity_level=verbose)
            td.cycle(self.connected)

            # If not already, select backup chat
            if not "backup chat id" in self.db.config.keys():
                print(color.BOLD + color.BLUE +
                      "\nInstructions: " + color.END +
                      "send the message 'telegram " +
                      "will not allow this' in the chat you want your " +
                      "backups to be stored.")
                td.cycle(self.find_backup_chat)
            chat_id = self.db.config['backup chat id']
            # Process document
            self.document = self.process_file(f, ignore_duplicate=ignore_duplicate, verbose=verbose)
            if not self.document:
                raise MessageInException(f + ': already backed up')
 
            # Encrypt document
            encrypted = path_join(self.db.cache_path, '.'.join([self.document["name"], "gpg"]))
            self.encrypt(f, self.document["passphrase"], output=encrypted)

            # Split document
            if 'format version' in self.document.keys():
                if self.document['format version'] == 2:
                    digits = 6
            else:
                digits = 2
            chunk_prefix = path_join(self.db.cache_path, self.document["id"])
            split = {'args':[encrypted],
                     'kwargs':{'output': chunk_prefix,
                               'size': size,
                               'digits': digits}}
            self.document["pieces"] = self.split(*split['args'], **split['kwargs']) 

            # Send files
            for i in range(self.document["pieces"]):
                self.current_upload = chunk_prefix + str(i).zfill(digits)
                self.uploaded = False
                td.send_file_message(chat_id, self.current_upload)
                td.cycle(self.sent)

            # Cleaning
            rm(encrypted)
            for i in range(self.document["pieces"]):
                rm(chunk_prefix + str(i).zfill(digits))
               
            # Saving 
            self.db.files.append(self.document)
            self.db.save()
    
            # Close client
            td.destroy(td.client)
            cd(current_path)

        except MessageInException as e:
            # Close client
            cd(current_path)

    def process_file(self, f, ignore_duplicate=False, verbose=0):
        """Extract data from the file for insert in the database

        Args:
            f (str): path of the file to be processed
            override (bool): whether to include a file already backed up
            verbose (int): explanation in class declaration
        Returns:
            document (dict):
        """
        document = {}
        document["name"] = f.split("/")[-1]
        document["hash"] = self.hash(f)
        document["path"] = f
        document["id"] = random_id(20)
        document["passphrase"] = random_id(200)
        document["chat id"] = self.db.config["backup chat id"]
        document['messages id'] = []
        document['size'] = getsize(f)
        document['format version'] = 2

        if verbose >= 1:
            for k in document.keys():
                print(color.BOLD + color.BLUE + k + ": " + color.END + str(document[k]))

        if not ignore_duplicate:
            if document["hash"] in (doc["hash"] for doc in self.db.files):
                return False
        return document

    def hash(self, f):
        """Evaluate sha256sum for a file

        Args:
            f (str): path of the file to hash
        Returns:
            (str) sha256sum of the file
        """
        out = sh(['sha256sum', f])
        out = str(out)
        out = out.split(' ')
        return out[0]
 
    def encrypt(self, f, passphrase, output):
        """GPG encrypt file at path f with a passphrase

        Args:
            f (str): path of the file to encrypt
            passphrase (str): secret key with which encrypt the file
        Returns:
            nothing
        """
        return sh(['gpg',
                   '--output',
                   output,
                   '--symmetric',
                   '--batch',
                   '--yes',
                   '--passphrase',
                   passphrase,
                   '--cipher-algo',
                   'AES256', 
                   f])

    def compress(self, f, output=None):
        """Compress file with GNU tar
        
        Args:
            f (str): path of the file
            output (str): name of the resulting file (optional)
        """
        if output == None:
            output = f
        return sh(['nocache',
                   'nice', 
                    '-n', 
                    '20', 
                    'tar', 
                    '-cf', 
                    output+'.tar',
                    f])

    def split(self, f, output, size='100', digits=6):
        """split file using GNU split

        Args:
            f (str): path of the file
            output (str): name of the output files (they will be outputXX with XX numbers)
            size (float): size of the splitted chunks (optional)
        """
        try:
            out = sh(['split',
                             '--bytes',
                             '{}MB'.format(size),
                             '--suffix-length',
                             '{}'.format(digits),
                             '-d',
                             "{}".format(f),
                             "{}".format(output)
                             ])
        except Exception as e:
            print(e)
            print(out)
        return len([piece for piece in ls(self.db.cache_path) if output.split("/")[-1] in piece])

    def find_backup_chat(self, td, event):
        """Extract chat id of the next chat containing the message 'telegram will not allow this'        

        td.cycle argument (see td.py)

        """
        message = td.filter_new_message(event, exact_text='telegram will not allow this')
        if message:
            self.db.config['backup chat id'] = message['chat_id']
            self.db.save()
            return True
        if message == False:
            print("\nMessage not pertaining.")

    def sent(self, td, event):
        """Check if the document argument of this class has been saved on telegram cloud

        td.cycle argument (see td.py)

        """
        if event['@type'] == 'error' and event['message'] == 'Chat not found':
            instructions_string = ("{}\n Instructions: {}"
                                   "send the message 'telegram"
                                   "will not allow this' in the"
                                   "chat you want your backups"
                                   "to be stored.").format(color.BOLD + color.BLUE, color.END)
            print(instructions_string)
            found = self.find_backup_chat(td, event)
            if found:
                 return True
            
        if event['@type'] == 'updateMessageSendSucceeded':
            if self.verbose >= 1:
                pprint(event)
            content = event['message']['content']
            if content['@type'] == 'messageDocument' and content['document']['@type'] == 'document':
                document = content['document']['document']
                if document['@type'] == 'file': 
                    if self.hash(self.current_upload) == self.hash(document['local']['path']):
                        if document['remote']['is_uploading_completed']:
                            if self.verbose > 0:
                                print(color.BOLD + self.current_upload + color.END + ": upload completed")
                            self.document['messages id'].append(event['message']['id'])
                            return True

    def connected(self, td, event):
        """Check if td instance is connected to telegram network"""
        if td.connected:
            return True

class Restore:
    """Restore backed up files according to various criteria"""
    executable_path = dirname(abspath(__file__))

    def __init__(self, filename, download_directory=getcwd(), verbose=2):

        self.verbose = verbose
        current_path = getcwd()
        self.download_directory = download_directory

        # Open 'database'
        self.db = Db(verbose=self.verbose)

        cd(self.db.config_path)

        try:
            # Check if filename exists
            results = [f for f in self.db.files if (f["name"] == filename) or 
                                                   (f["path"] == filename) or
                                                   (f["hash"] == filename)]
            if len(results) > 1:
                print("Multiple results:")
                for i,f in enumerate(results):
                    print(color.BOLD + i+1 + color.END)
                    pprint(f)
                result = results[int(input("Pick one: ")-1)]
       
            if len(results) == 0:
                print("File not found")
                raise FileNotFoundError

            self.document = results[0]

            self.download_paths = []

            # Instantiates telegram client
            td = Td(tdjson_path=self.db.executable_path, db_key=self.db.config["db key"], verbosity_level=verbose)
            td.cycle(self.connected)

            # Download file chunks
            for message_id in self.document['messages id']:
                self.message_id = message_id
                td.send({'@type':'getMessage',
                         'chat_id':self.document["chat id"],
                         'message_id':message_id})
                td.cycle(self.download_file)
                td.cycle(self.downloaded)

            # Concatenate file chunks
            output = path_join(self.download_directory, self.document["name"])
            encrypted = output + ".gpg"
            self.cat(self.download_paths, encrypted)

            # Decrypt file
            self.decrypt(encrypted, self.document['passphrase'], output)

            # Clean
            for path in self.download_paths:
                rm(path)
            rm(encrypted)

            # Come back into current folder
            cd(current_path)

        except FileNotFoundError as e:
           cd(current_path) 

    def cat(self, files, output):
        """concatenate files

        Args:
            files (list): files to join
            output (str): path of the output file
        """
        cat = ['cat'] + files
        dd = ['dd',  "of=" + output]
        if self.verbose < 1:
            dd = dd + ['status=none']
        process_cat = Popen(cat, stdout=PIPE,
                                    shell=False)
        process_dd = Popen(dd, stdin=process_cat.stdout,
                                  shell=False)
        process_cat.stdout.close()
        return process_dd.communicate()[0]

    def decrypt(self, f, passphrase, output):
        """GPG decrypt file at path f with a passphrase

        Args:
            f (str): path of the file to decrypt
            passphrase (str): secret key which decrypts the file
            output (str): name of the file decrypted
        Returns:
            nothing
        """
        dd = ['dd',  "of=" + output]
        gpg = ['gpg']
        dd = ['dd',  "of=" + output]
        if self.verbose < 1:
            dd = dd + ['status=none']
            gpg = gpg + ['--quiet']
        gpg = gpg + ['--decrypt', '--batch', '--passphrase', passphrase, f]

        process_gpg = Popen(gpg, stdout=PIPE,
                                    shell=False)
        process_dd = Popen(dd, stdin=process_gpg.stdout,
                                  shell=False)
        process_gpg.stdout.close()
        return process_dd.communicate()[0]


    def download_file(self, td, event):
        if event['@type'] == 'message':
            if event['id'] == self.message_id:
                self.file_id = event['content']['document']['document']['id']
                td.downloadFile(self.file_id)
                return True

    def connected(self, td, event):
        """Check if td instance is connected to telegram network"""
        if td.connected:
            return True

    def downloaded(self, td, event):
        if event['@type'] == 'updateFile':
            if event['file']['local']['is_downloading_completed']:
                self.download_paths.append(event['file']['local']['path'])
                return True
        if event['@type'] == 'file':
            if self.verbose >= 2:
                pprint(event)
            if event['id'] == self.file_id and event['local']['is_downloading_completed'] and event['local']['path'] != '':
                self.download_paths.append(event['local']['path'])
                return True

# as script

def main():
    help_text="""pgpgram

Encrypted backups on telegram.

SYNTAX:
    pgpgram [command] [option] [argument]

COMMANDS:
    backup, restore

OPTIONS:
    -r
    --recursive: recursively execute [command] on every file in the argument directory
    --test
"""

    parser = ArgumentParser(description="PGP encrypted backups on Telegram Cloud")

    # Parser args
    verbose = {'args': ['--verbose'],
               'kwargs': {'dest': 'verbose',
                          'action': 'store_true',
                          'default': False,
                          'help': 'extended output'}}

    version = {'args': ['--version'],
               'kwargs': {'dest': 'version',
                          'action': 'store_true',
                          'default': False,
                          'help': 'print version'}}

    parser.add_argument(*verbose['args'], **verbose['kwargs'])
    parser.add_argument(*version['args'], **version['kwargs'])

    command = parser.add_subparsers(dest="command")

    backup = command.add_parser('backup', help="backup file")

    # Backup args

    backup_filename = {'args': ['filename'],
                       'kwargs': {'nargs': '+',
                                  'action': 'store',
                                  'help': "exact name of the file to back up; default: same name"}}

    size = {'args': ['--size'],
            'kwargs': {'dest': 'size',
                       'nargs': 1,
                       'action': 'store',
                       'default':[100],
                       'help': "specify size of the chunks the file will be split; default: 100M"}}

    ignore_duplicate = {'args': ['--ignore-duplicate'],
                        'kwargs': {'dest': 'duplicate',
                                   'action': 'store_true',
                                   'default': False,
                                   'help': "backup file even if already present in the database; default: No"}}

    backup.add_argument(*backup_filename['args'], **backup_filename['kwargs'])
    backup.add_argument(*size['args'], **size['kwargs'])
    backup.add_argument(*ignore_duplicate['args'], **ignore_duplicate['kwargs'])

    restore = command.add_parser('restore', help="restore file")

    # Restore args

    restore_filename = {'args': ['filename'],
                        'kwargs': {'nargs': '+',
                                   'action': 'store',
                                   'help': ("exact name, complete path"
                                            "or hash of the file to be restored")}}

    download_directory = {'args': ['--download-directory'],
                          'kwargs': {'dest': 'download_dir',
                                     'nargs': 1,
                                     'action': 'store',
                                     'default': [getcwd()],
                                     'help': "directory in which to save the file; default: current dir"}}

    restore.add_argument(*restore_filename['args'], **restore_filename['kwargs'])
    restore.add_argument(*download_directory['args'], **download_directory['kwargs']) 

    list_command = command.add_parser('list', help="show all backed up files in location")

    # List args

    list_pattern = {'args': ['pattern'],
                    'kwargs': {'nargs': '?',
                               'default': '',
                               'help': "the files start with this pattern"}}

    list_command.add_argument(*list_pattern['args'], **list_pattern['kwargs'])
 
    search = command.add_parser('search', help="search and eventually download a backed up file")

    # Search args

    search_query = {'args': ['query'],
                    'kwargs': {'nargs': '+',
                               'action': 'store',
                               'help': "what to search"}}

    search_path = {'args': ['--path'],
                   'kwargs': {'dest': 'path',
                              'nargs': 1,
                              'action': 'store',
                              'default': [getcwd()],
                              'help': "specify the path in which the results were when backed up; default: current dir"}}

    search_filetype = {'args': ['--filetype'],
                       'kwargs': {'dest': 'filetype',
                                  'nargs': 1,
                                  'action': 'store',
                                  'default': ['any'],
                                  'help': "any, images, documents, code, audio, video"}}

    search_results = {'args': ['--results'],
                      'kwargs': {'dest': 'results',
                                 'action': 'store',
                                 'default': 10,
                                 'help': "how many results to display; default: 10"}}

    search_exclude = {'args': ['--exclude'],
                      'kwargs': {'dest': 'exclude',
                                 'nargs': '+',
                                 'action': 'store',
                                 'default': [],
                                 'help': "exclude from results files with the given extensions"}}

    search.add_argument(*search_query['args'], **search_query['kwargs'])
    search.add_argument(*search_path['args'], **search_path['kwargs'])
    search.add_argument(*search_filetype['args'], **search_filetype['kwargs'])
    search.add_argument(*search_results['args'], **search_results['kwargs'])
    search.add_argument(*search_exclude['args'], **search_exclude['kwargs'])
    args = parser.parse_args()

    if args.version:
        print(version)

    if args.verbose:
        print(args)
        verbose = 2
    else:
        verbose = 0

    if args.command == "backup":
        backup_kwargs = {'ignore_duplicate': args.duplicate,
                         'size': str(args.size[0]),
                         'verbose': verbose}
        for f in args.filename:
            if not isfile(f):
                if isdir(f):
                    for path, directory, files in walk(f):
                        for f2 in files:
                            file_path = path_join(path, f2)
                            backup = Backup(file_path, **backup_kwargs)
            else:
                backup = Backup(f, **backup_kwargs)

    if args.command == "restore":
        for f in args.filename:
            restore = Restore(f, download_directory=args.download_dir[0], verbose=verbose)

    if args.command == "list":
        db = Db()
        docs = [d for d in db.files if d['path'].startswith(getcwd() + "/" + args.pattern)]
        if args.verbose:
            pprint(docs)
        else:
            results = ""
            for d in docs:
                results = results + d['path'] + '\n'
            print(results)

    if args.command == "search":
        query = args.query[0]
        for w in args.query[1:]:
            query = query + " " + w
        db = Db()
        search = db.search(query, filetype=args.filetype[0], path=args.path[0], results_number=int(args.results), verbose=verbose)
