# -*- coding: utf-8 -*-

#    Td
#
#    ----------------------------------------------------------------------
#    Copyright © 2018, 2019  Pellegrino Prevete
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


from getpass import getpass
from ctypes.util import find_library
from ctypes import *
import json
from pprint import pprint
from .color import Color

color = Color()

class Td:
    """ Ugly python class to interact with tdlib JSON.
    
    Three python wrapper functions ("send", "execute" and "receive") constitute the bulk
    of the class.
    - Send
        This function exposes all functions and method from telegram API through python dictionaries.
        For example, if you want to execute the sendMessage function, which accepts
        as mandatory parameters "chat_id" and "input_message_content", respectively
        an integer and an "inputMessageContent" object, you can send the following
        dictionary as legit input for 'send':          

          {'@type':'sendMessage',
           'chat_id': 00000001,
           'input_message_content':{'@type':'inputMessageText',  ( --------> subclass of inputMessageContent)
                                    ... fields necessary
                                        to create the object
                                   }
          }

        In two words, '@type' key instantiate objects and only basic types don't need it
        * References
            https://tinyurl.com/ydyvcn8j - sendMessage Documentation
            https://tinyurl.com/yccno2dl - List of all telegram api functions
    
    - Execute
        I have no clue on how it differentiates from 'send' since I never used it.

    - Receive
        Apparently this function needs to run continuously to not lose events, so it was
        embedded in a while True loop in the tdlib examples messages.
        To being able to work imperatively and avoid 'callbacks' use cycle method. See documentation. 

    Args:
        verbosity_level (int): parameter of tdlib json interface."""
    def __init__(self, tdjson_path, db_key, verbosity_level=2):
        self.db_key = db_key
        self.verbosity_level = verbosity_level
        self.connected = False
        tdjson = CDLL(tdjson_path + "/libtdjson.so")

        self.td_json_client_create = tdjson.td_json_client_create
        self.td_json_client_create.restype = c_void_p
        self.td_json_client_create.argtypes = []

        self.td_json_client_receive = tdjson.td_json_client_receive
        self.td_json_client_receive.restype = c_char_p
        self.td_json_client_receive.argtypes = [c_void_p, c_double]

        self.td_json_client_send = tdjson.td_json_client_send
        self.td_json_client_send.restype = None
        self.td_json_client_send.argtypes = [c_void_p, c_char_p]

        self.td_json_client_execute = tdjson.td_json_client_execute
        self.td_json_client_execute.restype = c_char_p
        self.td_json_client_execute.argtypes = [c_void_p, c_char_p]

        self.destroy = tdjson.td_json_client_destroy
        self.destroy.restype = None
        self.destroy.argtypes = [c_void_p]

        self.td_set_log_file_path = tdjson.td_set_log_file_path
        self.td_set_log_file_path.restype = c_int
        self.td_set_log_file_path.argtypes = [c_char_p]
        self.td_set_log_max_file_size = tdjson.td_set_log_max_file_size
        self.td_set_log_max_file_size.restype = None
        self.td_set_log_max_file_size.argtypes = [c_longlong]

        self.td_set_log_verbosity_level = tdjson.td_set_log_verbosity_level
        self.td_set_log_verbosity_level.restype = None
        self.td_set_log_verbosity_level.argtypes = [c_int]

        self.fatal_error_callback_type = CFUNCTYPE(None, c_char_p)

        self.td_set_log_fatal_error_callback = tdjson.td_set_log_fatal_error_callback
        self.td_set_log_fatal_error_callback.restype = None
        self.td_set_log_fatal_error_callback.argtypes = [self.fatal_error_callback_type]

        self.td_set_log_verbosity_level(self.verbosity_level)
        self.c_on_fatal_error_callback = self.fatal_error_callback_type(self.on_fatal_error_callback)
        self.td_set_log_fatal_error_callback(self.c_on_fatal_error_callback)

        self.td_set_log_verbosity_level(self.verbosity_level)
        self.c_on_fatal_error_callback = self.fatal_error_callback_type(self.on_fatal_error_callback)
        self.td_set_log_fatal_error_callback(self.c_on_fatal_error_callback)

        self.tdlib_parameters = {'@type':"setTdlibParameters", "parameters":{
                                                               "database_directory":"tdlib",
                                                               "use_message_database":True,
                                                               "use_secret_chats":True,
                                                               "api_id":11675,
                                                               "api_hash":"a299ae33d4fb605fb90896c7ccd8c5ff",
                                                               "system_language_code":"en",
                                                               "device_model":"Desktop",
                                                               "system_version":"Linux",
                                                               "application_version":"1.0",
                                                               "enable_storage_optimizer":True}}
        self.client = self.td_json_client_create()

    def on_fatal_error_callback(self, error_message):
        """Fatal error handling"""
        pprint('TDLib fatal error: ', error_message)

    def send(self, query):
        """JSON (dict) requests to tdlib

        See class help.

        Args:
            query (dict): '@type' field corresponds to object type; other fields are object init inputs;
                          you can use the '@extra' key with an unique ID to be able to identify server answer to
                          that specific query.
        Returns:
            nothing; you get returns through 'receive' method.
        """
        query = json.dumps(query).encode('utf-8')
        self.td_json_client_send(self.client, query)

    def receive(self):
        """Receive server events in JSON

        Args:
            nothing
        Returns:
            dictionary; careful, there will be lots of events of many different types.
        """
        result = self.td_json_client_receive(self.client, 1.0)
        if result:
            result = json.loads(result.decode('utf-8'))
        return result

    def execute(self, query):
        """Syncronous requests

        Args:
            query (dict)
        Returns:
            nothing
        """
        query = json.dumps(query).encode('utf-8')
        result = self.td_json_client_execute(self.client, query)
        if result:
            result = json.loads(result.decode('utf-8'))
        return result

    def signin(self, event):
        """Handles signin events; interactively asks for credentials if missing.

        Args:
            event (dict): output of receive method
        Returns:
            str: status of the connection to the service
        """
        if event['@type'] == 'updateAuthorizationState':
            auth_state = event['authorization_state']

            # if client is closed, we need to destroy it and create new client
            if auth_state['@type'] == 'authorizationStateClosed':
                self.destroy(self.client)
                self.connected = False
                return "Log out"

            # send Tdlib parameters
            if auth_state['@type'] == 'authorizationStateWaitTdlibParameters':
                self.send(self.tdlib_parameters)
                self.connected = False
                return "Sending Tdlib parameters"

            # set an encryption key for database to let know tdlib how to open the database
            if auth_state['@type'] == 'authorizationStateWaitEncryptionKey':
                self.send({"@type":"checkDatabaseEncryptionKey", "key":self.db_key})
                self.connected = False
                return "Sent db key"

            # select phone number for login
            if auth_state['@type'] == "authorizationStateWaitPhoneNumber":
                phone_number = input(color.BOLD + color.BLUE + "Please insert your phone number: " + color.END)
                self.send({"@type":"setAuthenticationPhoneNumber", "phone_number":phone_number})
                self.connected = False           
                return "Sended Phone Number"
 
            # insert authentication code
            if auth_state['@type'] == 'authorizationStateWaitCode':
                code = input(color.BOLD + color.RED + "Please insert the authentication code you received: " + color.END)
                self.send({"@type":"checkAuthenticationCode", "code":code})
                self.connected = False
                return "Sent authentication code"

            # insert authentication password if present
            if auth_state['@type'] == "authorizationStateWaitPassword":
                password = getpass(color.BOLD + color.RED + "Please insert your password: " + color.END)
                self.send({"@type":"checkAuthenticationPassword", "password":password})
                self.connected = False
                return "Sent authentication password"

            if auth_state['@type'] == "authorizationStateReady":
                self.connected = True
                if self.verbosity_level >= 2:
                    print("Connesso")
                return "Connected"

    def find_user(first_name=None):
        """Find user through 'updateUser' events when connection is just estabilished.

        Args:
            event (dict): output of receive;
            first_name (str): first name of the contact to be searched
        Returns:
            (dict) tdlib user object serialized as python dictionary
        """
        if event['@type'] == 'updateUser':
            user = event['user']
            if user['first_name'] == first_name:
                return user

    def filter_new_message(self, event, exact_text=None, in_text=None):
        """Catches 'updateNewMessage' events satisfying given constraints

        Args:
            event(dict): event given by receive method;
            exact_text (str): catches messages having the arg as text;
            in_text (str): catches messages having the arg in their text;
            document_name (str): catches messages having attached a file named 'document_name'
            uploaded (bool): option for document_name; catches message if file is completely uploaded
        Returns:
            message (dict): tdlib message object serialized as python dictionary
            False: if received messages do not satisfy the query
            None: if event read is not a message
        """
        if event['@type'] == 'updateNewMessage':
            text = event['message']['content']['text']['text']
            if (exact_text != None) and (exact_text == text):
                return event['message']
            if (in_text != None) and (in_text in text):
                return event['message']

    def downloadFile(self, file_id):
        self.send({'@type':'downloadFile',
                   'file_id':file_id,
                   'priority':1})

    def send_file_message(self, chat_id, file_path, text=''):
        """Send a file to a chat
        
        Args:
            chat_id (int): id of the chat where to send the message
            file_path (str): path of the file to send
        """
        self.send({'@type':'sendMessage',
                   'chat_id':chat_id,
                   'input_message_content':{'@type':'inputMessageDocument',
                                            'document':{'@type':'inputFileLocal',
                                                        'path':file_path} } })

    def send_text_message(self, chat_id, text):
        """Send a text message to a chat
        
        Args:
            chat_id (int): id of the chat where to send the message
            text (str): text of the message
        """
        pass

    def cycle(self, function):
        """execute function, managing connection to telegram network

        It takes the burden of notifying you if something happens between you and
        telegram network.
        
        Args:
            function (fun): function that will be executed in loop inside 'cycle';
                            loop will finish when the function returns True; it must
                            have as arguments:
                            - td, an instance of this class 
                            - event, an event got through 'receive'
        """
        if self.verbosity_level >= 2:
            print("cycling", function.__name__)
        while True:
            event = self.receive()
            # handle an incoming update or an answer to a previously sent request
            
            if self.verbosity_level >= 2 and event != None and event['@type'] != 'updateUser':
                pprint(event)
                #sys.stdout.flush()
                pass

            if event:
                self.signin(event)
                if self.connected:
                    if function(self, event):
                        if self.verbosity_level >= 2:
                            print("finished", function.__name__)
                        break
