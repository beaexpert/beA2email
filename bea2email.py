"""
    beA.expert BEA-API / EXPERIMENTAL
    ---------------------------------
    Demo script not intented for production
    Version 1.2 / 28.12.2021
    (c) be next GmbH (Licence: GPL-2.0 & BSD-3-Clause)
    https://opensource.org/licenses/GPL-2.0
    https://opensource.org/licenses/BSD-3-Clause

    Dependency: 
    -------------
    bex_api.py (https://github.com/beA-expert/beA-API-PYTHON)

"""
import imaplib
import configparser
import os
import json
import base64
import xml.etree.ElementTree as ET

from types import SimpleNamespace
from time import time

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

""" 
    ***************************************************
    IMPORT BEA EXPERT API LIB
    bex_api.py (https://github.com/beA-expert/beA-API-PYTHON)
    notice: to use this script you first need to
            subscribe to the beA.expert API
            more info: https://bea.expert/api/
    *************************************************** 
"""
import bex_api

""" 
    ***************************************************
    GET THE CONFIG FROM FILE OR DEFINE CONFIG ARRAY
    ***************************************************
"""
__current_path = os.getcwd()
__config=[]
__config_file=__current_path+'/private.config.ini'
if os.path.exists(__config_file):
    __config = configparser.ConfigParser()
    __config.read(__config_file)    
else :
    __config["IMAP_SERVER"]["HOST"] = "...."
    __config["IMAP_SERVER"]["PORT"] = 993
    __config["IMAP_SERVER"]["EMAIL"] = "...."
    __config["IMAP_SERVER"]["PWD"] = "...."
    __config["SOFTWARETOKEN"]["B64"] = "...."
    __config["SOFTWARETOKEN"]["FILE"] = "...."
    __config["SOFTWARETOKEN"]["PWD"] = "...." 
    __config["PATH"]["LOCKFILES"] = "./lockfiles/" # UNIX-Style

if __config["PATH"]["LOCKFILES"]!="":
    if os.path.exists(__config["PATH"]["LOCKFILES"])==False:
         os.mkdir(__config["PATH"]["LOCKFILES"], mode = 0o777)

""" 
    ***************************************************
    APPEND AN EMAIL TO AN IMAP FOLDER WITHOUT SENDING IT
    ***************************************************
"""
def imapinbox(_from,_subject,_message,_email_att):

    connection = imaplib.IMAP4_SSL(__config["IMAP_SERVER"]["HOST"],__config["IMAP_SERVER"]["PORT"])
    connection.login(__config["IMAP_SERVER"]["EMAIL"],__config["IMAP_SERVER"]["PWD"])

    msg = MIMEMultipart()
    msg["From"] = _from
    msg["Subject"] = _subject

    for file in _email_att:
        if bex_api.__DEBUG__ : print("add file:"+file.file_name)
        part = MIMEBase("application", "octet-stream")        
        part.set_payload(file.file_data)
        encoders.encode_base64(part)            
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {file.file_name}",
        )
        msg.attach(part)

    msg.attach(MIMEText(_message, "plain"))

    connection.append('INBOX', '', imaplib.Time2Internaldate(time()), str(msg).encode('utf-8'))


""" 
    ***************************************************
    BEA2EMAIL MAIN
    ***************************************************
"""
# define the user softwaretoken:
# 1./ either the file name .p12-file __config["SOFTWARETOKEN"]["FILE"]
# 2./ or directly the token in base64 -> __config["SOFTWARETOKEN"]["B64"]

sw_token = "" #__config["SOFTWARETOKEN"]["FILE"]
sw_pin = __config["SOFTWARETOKEN"]["PWD"]
token_b64 = __config["SOFTWARETOKEN"]["B64"]

# login
print("login ...")
token, safeId, sessionKey = bex_api.bea_login(sw_token, sw_pin, token_b64)

if bex_api.__DEBUG__:
    print("token: " + token)
    print("safeId: " + safeId)
    print("sessionKey: " + base64.b64encode(sessionKey).decode('ascii'))

# postboxes
print("get postboxes ...")
token, postboxes = bex_api.bea_get_postboxes(token)

for p in postboxes:
    if bex_api.__DEBUG__: print(p.postboxSafeId)

    for f in p.folder:
        if bex_api.__DEBUG__: print(f.id)

        #get the users inbox
        if(f.type == "INBOX") and (f.postboxSafeId == safeId):
            inboxId = f.id
            break

if bex_api.__DEBUG__: print("inboxId: " + inboxId)

#folderoverview
print("get folderoverview inboxId:"+inboxId+" for safeId:"+safeId+" ...")
token, messages = bex_api.bea_get_folderoverview(token, inboxId, sessionKey)

if bex_api.__DEBUG__: print(messages)

for message_to_consider in messages:

    messageId=message_to_consider.messageId
    lockfile = __config["PATH"]["LOCKFILES"]+messageId+".lock"

    if os.path.exists(lockfile)==False:

        token, message = bex_api.bea_get_message(token, messageId, sessionKey)  

        if bex_api.__DEBUG__: print(message.metaData)

        # get all attachments
        email_att=[]
        for a in message.attachments :
            tmp_att = SimpleNamespace()
            tmp_att.file_name=a.reference
            tmp_att.file_data=a.data
            email_att.append(tmp_att)

        if bex_api.__DEBUG__: print(email_att)

        # clean and prepare some fields for the future email
        email_bea_subject=""
        email_bea_body=""
        email_bea_safeid_receiver=""
        email_bea_safeid_sender=message.metaData.sender.safeId
        email_bea_referenceJustice=message.metaData.referenceJustice
        email_bea_referenceNumber=message.metaData.referenceNumber

        # gather additional informations in "message.decryptedObjects"
        for a in message.decryptedObjects:
            if a.name=="beaMessage.json":

                # extract beA message
                root = ET.fromstring(a.data)
                
                # from beaMessage.json
                beaMessage_json=base64.b64decode(root.findtext('{http://www.osci.de/2002/04/osci}Base64Content'))                
                if bex_api.__DEBUG__: print(beaMessage_json)
                
                # decode beaMessage.json
                beaMessage = json.loads(beaMessage_json)
                if bex_api.__DEBUG__: print(beaMessage)
                
                # get body and subject (since getfolderoverview does NOT always return a subject, we prefer to use this field)
                if email_bea_subject=="" and beaMessage["messageSubject"]!="":
                    email_bea_subject=beaMessage["messageSubject"]
                    if bex_api.__DEBUG__: print(email_bea_subject)
                    
                if email_bea_body=="" and beaMessage["messageBody"]!="":
                    email_bea_body=beaMessage["messageBody"]                
                    if bex_api.__DEBUG__: print(email_bea_body)
                
            elif a.name=="govello_coco" or a.name=="project_coco":

                # extract the SAFE-ID of a court (Gericht) if empty in the beA-message (which is almost always the case!)
                
                root = ET.fromstring(a.data)

                # consider new and old format of "govello_coco" and "project_coco"
                all_base64_contents=root.findall('{http://www.osci.de/2002/04/osci}Content/{http://www.osci.de/2002/04/osci}Base64Content')
                if all_base64_contents is None or len(all_base64_contents)==0:
                    all_base64_contents=root.findall('{http://www.osci.de/2002/04/osci}Base64Content')
                
                for base64_content in all_base64_contents:

                    if base64_content.attrib["Id"]=='additional_infos':
                        coco=base64.b64decode(base64_content.text)
                        if bex_api.__DEBUG__: print(coco)
                        for b in coco.splitlines():
                            coco_list=b.decode("utf-8").split("=")
                            if email_bea_safeid_sender=="":
                                if coco_list[0]=="user_id": # this is the SAFE-ID of a court!
                                    email_bea_safeid_sender=coco_list[1]
                                    if bex_api.__DEBUG__: print(email_bea_safeid_sender)
                                    break

                    elif base64_content.attrib["Id"]=='nachricht.xml':
                        coco=base64.b64decode(base64_content.text)
                        if bex_api.__DEBUG__: print(coco)

                        coco_xml = ET.fromstring(coco)
                        coco_xml_elements = coco_xml.findall("Nachricht")

                        for child in coco_xml:
                            if bex_api.__DEBUG__: print(child.tag, child.attrib)
                            if child.tag=="Aktenzeichen_Absender":
                                if email_bea_referenceJustice=="" and child.text!="":
                                    email_bea_referenceJustice=child.text
                            elif child.tag=="Aktenzeichen_Empfaenger":
                                if email_bea_referenceNumber=="" and child.text!="":
                                    email_bea_referenceNumber=child.text
                            elif child.tag=="Betreff":
                                if email_bea_subject=="" and child.text!="":
                                    email_bea_subject=child.text
                            elif child.tag=="Freitext":
                                if email_bea_body=="" and child.text!="":
                                    email_bea_body=child.text
                            elif child.tag=="Empfaengerkennung":
                                if email_bea_safeid_receiver=="" and child.text!="":
                                    email_bea_safeid_receiver=child.text           

        # format email
        email_from=message.metaData.sender.name.replace(",", "")
        email_subject="[beA] ["+messageId+"] "+email_bea_referenceJustice+" (°ʖ°) "+email_bea_referenceNumber
        email_body="Folgende beA-Nachricht wurde erhalten:\n" \
                "--------------------------------------\n" \
                "Absender: "+message.metaData.sender.name+" ("+email_bea_safeid_sender+")\n"

        for a in message.metaData.addressees:
            email_body+="Empfänger: "+a.name+" ("+a.safeId+")\n" \
            
        email_body+="Empfangen am: "+message.metaData.receptionTime+"\n" \
                "Aktenzeichen Justiz: "+email_bea_referenceJustice+"\n" \
                "Aktenzeichen: "+email_bea_referenceNumber+"\n" \
                "--------------------------------------\n" \
                "beA-Nachricht: "+email_bea_subject+"\n\n" 
        
        if email_bea_body=="" or email_bea_body is None:
            email_body+="Diese Nachricht ist leer!"
        else:
            email_body+=email_bea_body

        email_body+="\n--------------------------------------\n"\
                "Dateien:\n"
        nbre=0
        for a in message.attachments :
            email_body+=a.reference+"\n"
            nbre+=1

        if nbre==0:
            email_body+=" - keine Datei - \n"

        email_body+="--------------------------------------\n"

        # place the email in the INBOX folder of the IMAP account (we do not really send the email using MTA)
        imapinbox(email_from+"<noreply@bea.expert>",email_subject,email_body,email_att)

        # create a new lock file to avoid send the same beA message multiple times
        with open(lockfile, 'w') as fp:
            pass

        print("Email sent, lockfile for messageID:"+messageId+" created.")

    else:

        print("Lockfile for messageID:"+messageId+" found! Do nothing.")

