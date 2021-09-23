# beA2email / beAte

_**Welcome to our demoapp beA2email**_

This demoapp (in python) will fetch the INBOX of a beA-Account and place the messages into the INBOX of an email account. The demoapp uses the beA.expert API (in pyhton) and is a good example how to realise powerful apps using the beA.expert API.

To use this script, you first need to subscribe to a beA.expert API-Account. 
For more information: [bea.expert/api/](https://bea.expert/api/)

__How it works:__

Using a given softwaretoken (attached to a beA-account), the script executes a __login to the beA system__, get the __postboxes of the beA account__, get an __overview of the INBOX-folder__ and finally __fetch all new messages__. Once loaded the messages will be decrypted and converted to emails including all documents attached (PDFs, signatures, xjustiz ...) The emails will then be __placed into the INBOX of an IMAP (email) account__ using the credentials of the email account. A lockfile mechanism on the local storage will take care that a given message is only sent once, even after restarting the script.

__Security considerations:__

* All credicentials and softwaretoken files are stored locally. So be careful to run this script from your own secured environment (local PC or own server).
* The beA messages will be __placed DIRECTLY into the IMAP (email) account using only IMAP functionalities__ via an SSL connection. For security purposes the script does __NOT send any email__ using MTA functionalities but only access directly IMAP account in a securised manner. Therefore, there is no need to encrypt the email itself.
* Of course, the script could also be changed to send the email using SMTP functionalities (this is up to you). In this case, we strongly recommend encrypting the email (PGP or S/MIME) before sending it.
* The script does __NOT create any temp files__, but only works with structures in memory. The content and attachments of the beA messages are not stored in any files.

__Further development:__

We have developed this demoscript to only access the INBOX but there are no difficulties to extend its scope to other folders/directories and/or additional accounts. __There are no limits!__ Since this script is only intended to demonstrate the capability of the beA.expert API, we strongly recommend adding a handling of errors, check the validity of structures (XML/JSON) etc... before using it for production.

_Have fun!_
