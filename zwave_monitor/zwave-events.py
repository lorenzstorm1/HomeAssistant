#!/usr/bin/env python3
import socket
import requests
from subprocess import Popen, PIPE
import json


# These lines are examples only. They may be useful to compare what your remote sends. To capture the codes that your remote sends, 
# tail the OZW_Log.

## line which as Node015 ZRC-90 command
# scene1
#2017-01-14 23:36:31.244 Detail, Node015,   Received: 0x01, 0x0b, 0x00, 0x04, 0x00, 0x04, 0x05, 0x5b, 0x03, 0x66, 0x00, 0x01, 0xce
#                                Node015,   Received: 0x01, 0x0b, 0x00, 0x04, 0x00, 0x0f, 0x05, 0x5b, 0x03, 0x80, 0x00, 0x01, 0x23
#                                Node015,   Received: 0x01, 0x0b, 0x00, 0x04, 0x00, 0x0f, 0x05, 0x5b, 0x03, 0x7f, 0x03, 0x01, 0xdf
#                                Node015,   Received: 0x01, 0x0b, 0x00, 0x04, 0x00, 0x0f, 0x05, 0x5b, 0x03, 0x9a, 0x02, 0x01, 0x3b
# scene2
#2017-01-14 23:37:10.186 Detail, Node015,   Received: 0x01, 0x0b, 0x00, 0x04, 0x00, 0x04, 0x05, 0x5b, 0x03, 0x67, 0x00, 0x02, 0xcc
#                                Node015,   Received: 0x01, 0x0b, 0x00, 0x04, 0x00, 0x0f, 0x05, 0x5b, 0x03, 0x84, 0x00, 0x02, 0x24
#                                Node015,   Received: 0x01, 0x0b, 0x00, 0x04, 0x00, 0x0f, 0x05, 0x5b, 0x03, 0x83, 0x03, 0x02, 0x20
# scene3
#2017-01-14 23:38:08.028 Detail, Node015,   Received: 0x01, 0x0b, 0x00, 0x04, 0x00, 0x04, 0x05, 0x5b, 0x03, 0x68, 0x00, 0x03, 0xc2
# scene4
#2017-01-14 23:38:37.856 Detail, Node015,   Received: 0x01, 0x0b, 0x00, 0x04, 0x00, 0x04, 0x05, 0x5b, 0x03, 0x69, 0x00, 0x04, 0xc4
# scene5
#2017-01-14 23:39:00.205 Detail, Node015,   Received: 0x01, 0x0b, 0x00, 0x04, 0x00, 0x04, 0x05, 0x5b, 0x03, 0x6a, 0x00, 0x05, 0xc6
# scene6
#2017-01-14 23:40:09.976 Detail, Node015,   Received: 0x01, 0x0b, 0x00, 0x04, 0x00, 0x04, 0x05, 0x5b, 0x03, 0x6b, 0x00, 0x06, 0xc4
# scene7
#2017-01-14 23:41:09.002 Detail, Node015,   Received: 0x01, 0x0b, 0x00, 0x04, 0x00, 0x04, 0x05, 0x5b, 0x03, 0x6c, 0x00, 0x07, 0xc2
# scene8
#2017-01-14 23:41:36.684 Detail, Node015,   Received: 0x01, 0x0b, 0x00, 0x04, 0x00, 0x04, 0x05, 0x5b, 0x03, 0x6e, 0x00, 0x08, 0xcf


# Match Rule (this should match the first portion of your lines)
MATCHER = 'Detail, Node020,   Received: 0x01, 0x0b, 0x00, 0x04, 0x00, 0x14, 0x05, 0x5b, 0x03,'

# These may or may not need to be adjusted based on your remote. You can test by tailing the OPW_Log and
# testing the individual buttons. These values represent the -3rd value (3rd from last) value in a line.
# As an example, the signifier for the following line is: '0x00' (or Single, based on the config below):
# Detail, Node015,   Received: 0x01, 0x0b, 0x00, 0x04, 0x00, 0x04, 0x05, 0x5b, 0x03, 0x66, 0x00, 0x01, 0xce
SINGLECLICK_SIGNIFIER = '0x00'          # Single click signifier;
DOUBLECLICK_SIGNIFIER = '0x03'          # Double click signifier;
LONGPRESS_CURRENT_SIGNIFIER = '0x02'    # This is fired when we are in the midst of a long press
LONGPRESS_END_SIGNIFIER = '0x01'        # This is fired when we come out of a long press

# The values in this dictionary represent the last digit in what we send to HA (script.zrc90_button_<button #>_<ClickNumbers value>)
ClickNumbers = {
    SINGLECLICK_SIGNIFIER: 1,
    DOUBLECLICK_SIGNIFIER: 2,
    LONGPRESS_END_SIGNIFIER: 3
}

# If the click type, which houses the signifier set above, exists in our dictinary: return that value; else: False;
def getClickNumber(clickType):
    for key, value in ClickNumbers.items():
        if(key == clickType):
            return value
    return False

# HA information
URI = 'https://kxsoupeluc2yczbt.myfritz.net/api/services/script/turn_on'
TOKEN = 'Quba7905'      #if your HA install does not use a password, set to False
#TOKEN = False

OZW_LOG = '/home/homeassistant/.homeassistant/OZW_Log.txt'

debug = True

# Open the tail of our OZW_Log and scan for new lines;
log = Popen(('/usr/bin/tail', '-F', '-n', '0', OZW_LOG), stdout=PIPE)
while True:

    # Get most recent line and massage it;
    line = log.stdout.readline()
    if not line:
        break
    line = line.strip().decode('utf-8')

    # Fast match to discard non-info log messages
    if MATCHER not in line:
        continue

    lineSplit = line.split(',')
    if len(lineSplit) < 3:      #If we don't have enough items, discard;
        continue

    clickType = lineSplit[-3].strip()               #This corresponds to the signifiers set above;
    clickNumber = getClickNumber(clickType)         #Let's click number for this click (determing whether its a single click, dbl click, or long press)
    if not clickNumber:
        continue

    button = line.split(',')[-2].replace(' 0x0','') #Get which button;
    event = 'script.zrc90_button_{0}_{1}'.format(button, clickNumber)
    if debug:
        print(event)

    if event:
        data = {'entity_id': event}
        if debug:
            print(data)

        if TOKEN:
            resp = requests.post(URI, data=json.dumps(data), headers={'x-ha-access': TOKEN, 'content-type': 'application/json'})
        else:
            resp = requests.post(URI, data=json.dumps(data), headers={'content-type': 'application/json'})

        if debug:
            print(resp)