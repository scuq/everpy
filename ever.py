#!/usr/bin/python
# coding=utf-8
# -*- coding: <utf-8> -*-
# vim: set fileencoding=<utf-8> :


me="everpy"

import logging
import os
import sys
import json

from xml.dom.minidom import parse, parseString

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(me)
logger.setLevel(logging.INFO)
hdlr = logging.FileHandler(os.path.normpath(os.path.expanduser("~")+"/.everpy/"+os.sep+__name__+".log"))
formatter = logging.Formatter('%(name)s[%(process)d]:%(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)

from optparse import OptionParser

import evernote.edam.userstore.constants as UserStoreConstants
import evernote.edam.type.ttypes as Types
from evernote.api.client import EvernoteClient
import evernote.edam.notestore.NoteStore as NoteStore


def save_config(config,config_file):

	with open(config_file, 'w') as fp:
		json.dump(config, fp)


def getTags(config,client):

	tags={}

	noteStore = client.get_note_store()

        for _tag in  noteStore.listTags(config["oauth_auth_token"]):
                tags[_tag.name]=_tag.guid

	return tags

def getNoteMetaDataList(config,client,note_filter):

	notelist = []

	noteStore = client.get_note_store()

        spec = NoteStore.NotesMetadataResultSpec()
        spec.includeTitle = True

        notelist = noteStore.findNotesMetadata(config["oauth_auth_token"], note_filter, 0, 100, spec)

	return notelist

def actionUncheckRecurring(config, client):

	ok = True

	try:

		noteStore = client.get_note_store()

		tags={}
		tags = getTags(config,client)

		note_filter = NoteStore.NoteFilter()
		note_filter.tagGuids = [tags["recurring"]]

		getNoteMetaDataList(config,client,note_filter)

		recurringNoteList = getNoteMetaDataList(config,client,note_filter)


		for note in recurringNoteList.notes:
			logger.info("Updating Note \"{}\"".format(note.title))
			current_note_content = noteStore.getNoteContent(config["oauth_auth_token"], note.guid)
			dom3 = parseString(current_note_content)
			for ele in dom3.getElementsByTagName("en-todo"):
				ele.setAttribute('checked', 'false')

			nnote = Types.Note()
			nnote.title = note.title
			nnote.guid = note.guid
			nnote.content = dom3.toxml()

	except:
		ok = False
	
	return ok


def main():

        parser = OptionParser()
	parser.add_option("", "--force-oauth-setup", action="store_true", dest="force_oauth_setup", default=False, help="force oauth setup")
	parser.add_option("-p", "--prod", action="store_true", dest="use_prod", default=False, help="user evernote prod env, default is sandbox")
	parser.add_option("", "--uncheck-recurring-todo", action="store_true", dest="action_uncheck_recurring", default=False, help="uncheck all todo boxes of notes tagged with \"recurring\"")
        (options, args) = parser.parse_args()

	config_file = os.path.expanduser("~")+"/.everpy/config_sandbox.json"

	if options.use_prod:
		config_file = os.path.expanduser("~")+"/.everpy/config.json"
	

	config = {}
	
	if os.path.isfile(config_file):
		logger.info("config file loaded")
		_data=open(config_file).read()
		config = json.loads(_data)
	else:
		logger.error("no config file {} found.".format(config_file))
		sys.exit(1)


	if config.keys().count("oauth_setup_done") <= 0:
		config["oauth_setup_done"] = False

	if options.force_oauth_setup == True:
		config["oauth_setup_done"] = False
		

	if not config["oauth_setup_done"]:
		client = EvernoteClient(
			consumer_key=config["consumer_key"],
			consumer_secret=config["consumer_secret"],
			sandbox=True # Default: True
		)
	else:

                client = EvernoteClient(
                        token=config["oauth_auth_token"],
                        sandbox=True # Default: True
                )

		

	if not config["oauth_setup_done"]:
		request_token = client.get_request_token(config["callback_url"])
	
		print "Copy and paste this URL in your browser and login to authorizer ever.py"
		print
		print client.get_authorize_url(request_token)
		print
		print "Paste the URL after login here:"
		oauth_verifier = raw_input()

		config["oauth_verifier"] = oauth_verifier.strip() 
	
		auth_token = client.get_access_token(
       	    		request_token['oauth_token'],
            		request_token['oauth_token_secret'],
            		oauth_verifier
        	)

		config["oauth_auth_token"] = auth_token 
		config["oauth_setup_done"] = True 

		save_config(config,config_file)

#	userStore = client.get_user_store()
#	user = userStore.getUser()

	if options.action_uncheck_recurring:
		if  not actionUncheckRecurring(config, client):
			print "error occured."



if __name__ == '__main__':
        main()
