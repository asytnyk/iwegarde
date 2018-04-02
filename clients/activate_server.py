#!/usr/bin/env python3

import simplejson as json
import argparse
import os.path
import requests
import sys
import time
import urllib3
import subprocess
from pyfiglet import Figlet

def check_file(parser, path):
    if not os.path.isfile(path):
        parser.error("The file %s does not exist!" % path)
    else:
        with open(path, 'r') as json_file:
            try:
                json.load(json_file)
            except:
                parser.error("The file %s does not seem to be a valid json file!" % path)

# Check https://stackoverflow.com/questions/14393339/convert-this-curl-cmd-to-python-3 for https
def request_activation_pin(installation_key, facter):
    url = installation_key['request_activation_url']
    key = installation_key['installation_key']
    headers = {'installation_key': key, 'Content-Type': 'application/json'}
    try:
        r = requests.post(url, headers=headers, data=json.dumps(facter))
    except (urllib3.exceptions.NewConnectionError, requests.exceptions.ConnectionError):
        print ('Connection error!')
        return None
    if r.status_code == 200:
        return r.json()
    else:
        return None

def try_download_client_conf(activation_pin_json, installation_key_json):
    headers = {'installation_key': installation_key_json['installation_key']}
    try:
        r = requests.get(activation_pin_json['download_keys_url'], headers=headers)
    except (urllib3.exceptions.NewConnectionError, requests.exceptions.ConnectionError):
        print ('Connection error! Check the connection to the Internet')
        return None

    if r.status_code == 200:
        return r.json()
    else:
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('installationkey', help='path to installation-key json file')
    parser.add_argument('facter', help='path to facter json file')

    args = parser.parse_args()

    check_file(parser, args.installationkey)
    check_file(parser, args.facter)

    with open(args.installationkey, 'r') as json_file:
        installation_key_json = json.load(json_file)

    with open(args.facter, 'r') as json_file:
        facter = json.load(json_file)

    activation_pin_json = None
    sleep_secs = 15
    while not activation_pin_json:
        print('.', end='', flush=True)
        activation_pin_json = request_activation_pin(installation_key_json, facter)
        if not activation_pin_json:
            print ('Error getting the activation pin. Check if the installation key is valid and if the server is connected to the Internet.')
            time.sleep(sleep_secs)
    print('')

    if 'error' in activation_pin_json:
        print (activation_pin_json['error'])
        sys.exit()

    client_conf_json = None
    f = Figlet('big')
    print('Waiting your authorization for pin {}'.format(
        str(activation_pin_json['activation_pin'])))
    print(f.renderText('Pin {}'.format(activation_pin_json['activation_pin'])))
    print('You can activate it at {}'.format(
        activation_pin_json['activate_pin_url']))

    while not client_conf_json:
        print('.', end='', flush=True)
        client_conf_json = try_download_client_conf(activation_pin_json, installation_key_json)
        if not client_conf_json:
            time.sleep(sleep_secs)
    print('')
    if 'error' in client_conf_json:
        print (client_conf_json['error'])
        sys.exit()

    print (client_conf_json)

if __name__ == "__main__":
    main()
