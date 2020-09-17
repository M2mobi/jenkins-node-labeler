#!/bin/env python3

import re
import jenkins

from os import environ as env
from os import popen as cmd
from lxml import etree

username     = env['JENKINS_USERNAME']
password     = env['JENKINS_APIKEY']
jenkins_host = env['JENKINS_HOST']

def get_macos_version(version_regex):
    os_version_cmd = cmd('sw_vers -productVersion').read().strip()
    if not version_regex.match(os_version_cmd):
        print('Can\'t find macOS version')
        exit(255)
    return version_regex.match(os_version_cmd).group()

def get_xcode_version(version_regex):
    xcode_version_cmd = cmd('xcodebuild -version | head -1 | grep -Eo \'[0-9\.]+\'').read().strip()
    if not version_regex.match(xcode_version_cmd):
        print('Can\'t find Xcode version')
        exit(255)
    return version_regex.match(xcode_version_cmd).group()

def get_hostname():
    hostname = cmd('hostname -s').read().strip()
    if not hostname:
        print('Can\'t find hostname')
        exit(255)
    return hostname

def get_new_config(server, node, labels):
    config_string = server.get_node_config(node)
    config = etree.fromstring(bytes(config_string, encoding='utf8'))
    for child in config:
        if child.tag == 'label':
            child.text = ' '.join(labels)
    return etree.tostring(config).decode("utf-8")

version_regex = re.compile('([0-9]+\.[0-9]+)')
os_version    = get_macos_version(version_regex)
xcode_version = get_xcode_version(version_regex)
xcode_major   = xcode_version.split('.')[0]
hostname      = get_hostname()
labels        = ['iOS', 'xcode-' + xcode_version, 'xcode-' + xcode_major, 'macos-' + os_version, 'node-' + hostname.lower()]
if xcode_major == '11':
	labels.append('iOS13')
	pass

server = jenkins.Jenkins(jenkins_host, username=username, password=password)
if not server.node_exists(hostname):
    print('Not a jenkins node')
    exit(255)

new_config = get_new_config(server, hostname, labels)
print(new_config)
server.reconfig_node(hostname, new_config)
