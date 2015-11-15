#!/usr/bin/python
# -*- coding: utf-8 -*-

""" WHONIX SETUP WIZARD """
from PyQt4.QtGui import *
from PyQt4.QtCore import *

from PyQt4 import QtCore, QtGui
from subprocess import call
import os, yaml
import json
import inspect
import sys
import time
import re
import shutil

import stem
from stem.control import Controller

from guimessages.translations import _translations
from guimessages.guimessage import gui_message

import tor_status

import distutils.spawn

def parse_command_line_parameter():
    '''
    The wizard might be run from terminal.
    '''
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument('option', choices=['setup', 'quick', 'repository', 'locale_settings'])
    args, unknown_args = parser.parse_known_args()

    return args.option


class Common:
    '''
    Variables and constants used through all the classes
    '''
    translations_path ='/usr/share/translations/whonix_setup.yaml'

    first_use_notice = False
    is_complete = False
    disable_repo = False
    exit_after_tor_enabled = False
    use_bridges = False
    use_proxy = False
    bridge_type = ''
    bridges = []
    proxy_type = ''
    tor_status = ''

    if not os.path.exists('/var/cache/whonix-setup-wizard/status-files'):
        os.mkdir('/var/cache/whonix-setup-wizard/status-files')

    run_repo = (not os.path.exists('/var/cache/whonix-setup-wizard/status-files/whonix_repository.done') and
                not os.path.exists('/var/cache/whonix-setup-wizard/status-files/whonix_repository.skip'))

    show_disclaimer = (not os.path.exists('/var/cache/whonix-setup-wizard/status-files/disclaimer.done') and
                       not os.path.exists('/var/cache/whonix-setup-wizard/status-files/disclaimer.skip'))

    argument = parse_command_line_parameter()

    if argument == 'quick':
        exit_after_tor_enabled = True
        argument = "setup"

    if os.path.isfile('/usr/share/anon-gw-base-files/gateway'):
        environment = 'gateway'

    elif os.path.isfile('/usr/share/anon-ws-base-files/workstation'):
        environment = 'workstation'

    run_whonixcheck_only = (argument == 'setup' and environment == 'workstation'
                            and not run_repo and not show_disclaimer)

    if environment == 'gateway':
        first_use_notice = (not os.path.exists('/var/cache/whonix-setup-wizard/status-files/first_use_check.done') and
                            not os.path.exists('/var/cache/whonix-setup-wizard/status-files/first_use_check.skip'))

    if argument == 'setup':
        if environment == 'gateway' and show_disclaimer:
            wizard_steps = ['disclaimer_1',
                            'disclaimer_2',
                            'connection_main_page',
                            'bridge_wizard_page_1',
                            'bridge_wizard_page_2',
                            'proxy_wizard_page_1',
                            'proxy_wizard_page_2',
                            'tor_status_page',
                            'whonix_repo_page',
                            'repository_wizard_page_1',
                            'repository_wizard_page_2',
                            'repository_wizard_finish',
                            'finish_page',
                            'first_use_notice']

        elif environment == 'gateway' and not show_disclaimer:
            wizard_steps = ['connection_main_page',
                            'bridge_wizard_page_1',
                            'bridge_wizard_page_2',
                            'proxy_wizard_page_1',
                            'proxy_wizard_page_2',
                            'tor_status_page',
                            'whonix_repo_page',
                            'repository_wizard_page_1',
                            'repository_wizard_page_2',
                            'repository_wizard_finish',
                            'finish_page',
                            'first_use_notice']

        elif environment == 'workstation'and not run_whonixcheck_only:
            wizard_steps = ['disclaimer_1',
                            'disclaimer_2',
                            'whonix_repo_page',
                            'repository_wizard_page_1',
                            'repository_wizard_page_2',
                            'repository_wizard_finish',
                            'finish_page']

        elif environment == 'workstation'and run_whonixcheck_only:
            wizard_steps = ['finish_page']

    elif argument == 'repository':
        wizard_steps = ['repository_wizard_page_1',
                        'repository_wizard_page_2',
                        'repository_wizard_finish']

    elif argument == 'locale_settings':
        wizard_steps = ['locale_settings',
                        'locale_settings_finish']


class LocaleSettings(QtGui.QWizardPage):
    def __init__(self):
        super(LocaleSettings, self).__init__()

        self.text = QtGui.QLabel(self)

        self.group = QtGui.QGroupBox(self)

        self.default_button = QtGui.QRadioButton(self.group)
        self.other_button = QtGui.QRadioButton(self.group)

        self.lang_checkbox = QtGui.QCheckBox(self.group)
        self.kbd_checkbox = QtGui.QCheckBox(self.group)

        self.layout = QtGui.QVBoxLayout(self)

        self.setup_ui()

    def setup_ui(self):
        self.text.setMaximumSize(QtCore.QSize(400, 24))
        self.text.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.text.setText('Whonix installation language.')

        self.group.setMinimumSize(0, 112)

        self.default_button.setGeometry(QtCore.QRect(20, 16, 483, 21))
        self.default_button.setText('Default (English (US)')
        self.default_button.setChecked(True)

        self.other_button.setGeometry(QtCore.QRect(20, 36, 483, 21))
        self.other_button.setText('Other')
        self.other_button.toggled.connect(self.other_button_toggled)

        self.lang_checkbox.setEnabled(False)
        self.lang_checkbox.setChecked(True)
        self.lang_checkbox.setGeometry(QtCore.QRect(40, 58, 483, 21))
        self.lang_checkbox.setText('Change country and language')
        self.lang_checkbox.toggled.connect(self.lang_checkbox_toggled)

        self.kbd_checkbox.setEnabled(False)
        self.kbd_checkbox.setChecked(True)
        self.kbd_checkbox.setGeometry(QtCore.QRect(40, 78, 483, 21))
        self.kbd_checkbox.setText('Change keyboard layout')
        self.kbd_checkbox.toggled.connect(self.kbd_checkbox_toggled)

        self.layout.addWidget(self.text)
        self.layout.addWidget(self.group)

        self.setLayout(self.layout)

    def other_button_toggled(self, state):
        if state:
            self.lang_checkbox.setEnabled(True)
            self.kbd_checkbox.setEnabled(True)

        else:
            self.lang_checkbox.setEnabled(False)
            self.kbd_checkbox.setEnabled(False)

    def lang_checkbox_toggled(self, state):
        if (not self.lang_checkbox.isChecked() and
            not self.kbd_checkbox.isChecked()):
            self.lang_checkbox.setChecked(True)
            self.kbd_checkbox.setChecked(True)
            self.default_button.setChecked(True)
            self.other_button.setChecked(False)

    def kbd_checkbox_toggled(self, state):
        if (not self.lang_checkbox.isChecked() and
            not self.kbd_checkbox.isChecked()):
            self.lang_checkbox.setChecked(True)
            self.kbd_checkbox.setChecked(True)
            self.default_button.setChecked(True)
            self.other_button.setChecked(False)


class LocaleSettingsFinish(QtGui.QWizardPage):
    def __init__(self):
        super(LocaleSettingsFinish, self).__init__()

        self.text = QtGui.QTextBrowser(self)
        self.layout = QtGui.QVBoxLayout()

        self.setup_ui()

    def setup_ui(self):
        self.text.setFrameShape(QtGui.QFrame.NoFrame)
        self.layout.addWidget(self.text)

        self.setLayout(self.layout)


class DisclaimerPage1(QtGui.QWizardPage):
    def __init__(self):
        super(DisclaimerPage1, self).__init__()

        self.steps = Common.wizard_steps

        self.text = QtGui.QTextBrowser(self)
        self.accept_group = QtGui.QGroupBox(self)
        self.yes_button = QtGui.QRadioButton(self.accept_group)
        self.no_button = QtGui.QRadioButton(self.accept_group)

        self.layout = QtGui.QVBoxLayout()

        self.setupUi()

    def setupUi(self):
        self.text.setFrameShape(QtGui.QFrame.Panel)
        self.text.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)

        self.accept_group.setMinimumSize(0, 60)
        self.yes_button.setGeometry(QtCore.QRect(30, 10, 300, 21))
        self.no_button.setGeometry(QtCore.QRect(30, 30, 300, 21))
        self.no_button.setChecked(True)

        self.layout.addWidget(self.text)
        self.layout.addWidget(self.accept_group)
        self.setLayout(self.layout)

    def nextId(self):
        if self.yes_button.isChecked():
            return self.steps.index('disclaimer_2')
        # Not understood
        elif self.no_button.isChecked():
            return self.steps.index('finish_page')


class DisclaimerPage2(QtGui.QWizardPage):
    def __init__(self):
        super(DisclaimerPage2, self).__init__()

        self.steps = Common.wizard_steps
        self.env = Common.environment

        self.text = QtGui.QTextBrowser(self)
        self.accept_group = QtGui.QGroupBox(self)
        self.yes_button = QtGui.QRadioButton(self.accept_group)
        self.no_button = QtGui.QRadioButton(self.accept_group)

        self.layout = QtGui.QVBoxLayout()

        self.setupUi()

    def setupUi(self):
        self.text.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.text.setFrameShape(QtGui.QFrame.Panel)

        self.accept_group.setMinimumSize(0, 60)
        self.yes_button.setGeometry(QtCore.QRect(30, 10, 300, 21))
        self.no_button.setGeometry(QtCore.QRect(30, 30, 300, 21))
        self.no_button.setChecked(True)

        self.layout.addWidget(self.text)
        self.layout.addWidget(self.accept_group)
        self.setLayout(self.layout)

    def nextId(self):
        if self.yes_button.isChecked():
            if Common.run_repo:
                if self.env == 'gateway':
                    return self.steps.index('connection_main_page')
                elif self.env == 'workstation':
                # run whonix_repository_wizard
                    return self.steps.index('whonix_repo_page')
            else:
                if self.env == 'gateway':
                    return self.steps.index('bridge_wizard_page_1')
                elif self.env == 'workstation':
                    return self.steps.index('finish_page')
        # Not understood
        else:
            return self.steps.index('finish_page')


class ConnectionMainPage(QtGui.QWizardPage):
    def __init__(self):
        super(ConnectionMainPage, self).__init__()

        self.steps = Common.wizard_steps

        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.groupBox = QtGui.QGroupBox(self)
        self.label = QtGui.QLabel(self.groupBox)
        self.label_2 = QtGui.QLabel(self.groupBox)
        self.pushButton_1 = QtGui.QRadioButton(self.groupBox)
        self.label_4 = QtGui.QLabel(self.groupBox)
        self.pushButton_2 = QtGui.QRadioButton(self.groupBox)
        self.label_5 = QtGui.QLabel(self.groupBox)
        self.pushButton_3 = QtGui.QRadioButton(self.groupBox)

        self.pushButton = QtGui.QPushButton(self.groupBox)
        self.show_disable = False

        self.verticalLayout.addWidget(self.groupBox)

        self.setupUi()

    def setupUi(self):
        self.groupBox.setFlat(True)
        self.groupBox.setMinimumSize(QtCore.QSize(500, 320))

        self.label.setGeometry(QtCore.QRect(20, 0, 510, 41))
        self.label.setWordWrap(True)
        self.label.setText('Before you connect to the Tor network, you need to provide information about this computer Internet connection.')

        self.label_2.setGeometry(QtCore.QRect(10, 60, 431, 21))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_2.setFont(font)
        self.label_2.setText('Which of the following best describes your situation?')

        self.label_3 = QtGui.QLabel(self.groupBox)
        self.label_3.setGeometry(QtCore.QRect(10, 85, 321, 41))
        self.label_3.setWordWrap(True)
        self.label_3.setText('I would like to connect directly to the Tor netwotk. This will work in most situations.')

        self.pushButton_1.setGeometry(QtCore.QRect(20, 123, 110, 26))
        self.pushButton_2.setGeometry(QtCore.QRect(20, 203, 110, 26))
        self.pushButton_3.setGeometry(QtCore.QRect(20, 283, 110, 26))
        self.pushButton_1.setFont(font)
        self.pushButton_1.setText('Connect')
        self.pushButton_1.setChecked(True)
        self.pushButton_2.setFont(font)
        self.pushButton_2.setText('Configure')
        self.pushButton_3.setFont(font)
        self.pushButton_3.setText('Disable Tor')
        self.pushButton_3.setVisible(False)

        self.label_4.setGeometry(QtCore.QRect(10, 165, 381, 41))
        self.label_4.setWordWrap(True)
        self.label_4.setText('This computer\'s Internet connection is censored or proxied. I need to configure bridges or local proxy settings.')

        self.label_5.setGeometry(QtCore.QRect(10, 250, 500, 31))
        self.label_5.setWordWrap(True)
        self.label_5.setText('I do not want to connect automatically to the Tor network next time I boot Whonix. This wizard will be started.')
        self.label_5.setVisible(False)

        self.pushButton.setGeometry(QtCore.QRect(453, 285, 80, 25))
        self.pushButton.setText('&Advanced')
        self.pushButton.clicked.connect(self.show_disable_tor)

    def show_disable_tor(self):
        self.show_disable = not self.show_disable
        self.pushButton_3.setVisible(self.show_disable)
        self.label_5.setVisible(self.show_disable)
        if self.show_disable:
            self.pushButton.setText('&Less')
        else:
            self.pushButton.setText('&Advanced')

    def nextId(self):
        if self.pushButton_1.isChecked():
            return self.steps.index('tor_status_page')
        elif self.pushButton_2.isChecked():
            return self.steps.index('bridge_wizard_page_1')


class BridgesWizardPage1(QtGui.QWizardPage):
    def __init__(self):
        super(BridgesWizardPage1, self).__init__()

        translation = _translations(Common.translations_path, 'whonixsetup')
        self._ = translation.gettext

        #self.common = Common()
        #self.common.use_bridges = True
        self.steps = Common.wizard_steps
        self.env = Common.environment

        self.layout = QtGui.QVBoxLayout(self)
        self.label = QtGui.QLabel(self)
        self.layout.addWidget(self.label)

        self.label_2 = QtGui.QLabel(self)
        self.layout.addWidget(self.label_2)

        self.group_box = QtGui.QGroupBox(self)
        self.yes_button = QtGui.QRadioButton(self.group_box)
        self.no_button = QtGui.QRadioButton(self.group_box)
        self.label_3 = QtGui.QLabel(self.group_box)
        self.label_4 = QtGui.QLabel(self.group_box)
        self.layout.addWidget(self.group_box)

        self.setupUi()

    def setupUi(self):
        self.label.setMinimumSize(QtCore.QSize(16777215, 35))
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setText('   Tor Bridges Configuration')

        self.label_2.setMaximumSize(QtCore.QSize(16777215, 50))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.label_2.setFont(font)
        self.label_2.setWordWrap(True)
        self.label_2.setText('Does your Internet Service Provider (ISP) block or otherwise censor connections to the Tor network?')

        self.group_box.setMinimumSize(QtCore.QSize(16777215, 244))
        self.group_box.setFlat(True)
        self.yes_button.setGeometry(QtCore.QRect(25, 0, 350, 21))
        self.yes_button.setText('Yes')
        self.no_button.setGeometry(QtCore.QRect(25, 20, 350, 21))
        self.no_button.setText('No')
        self.no_button.setChecked(True)

        #self.label_3.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.label_3.setGeometry(10, 55, 520, 60)
        self.label_3.setTextFormat(QtCore.Qt.RichText)
        self.label_3.setWordWrap(True)
        self.label_3.setText('If you are not sure how to answer this question, choose No. \
            If you choose Yes, you will be asked to configure Tor bridges, \
            which are unlisted relays that make it more difficult to block connections \
            to the Tor network.')

        self.label_4.setGeometry(0, 220, 500, 15)
        self.label_4.setText('For assistance, contact help@rt.torproject.org')

    def nextId(self):
        if self.yes_button.isChecked():
            Common.use_bridges = True
            return self.steps.index('bridge_wizard_page_2')
        elif self.no_button.isChecked():
            return self.steps.index('proxy_wizard_page_1')


class BridgesWizardPage2(QtGui.QWizardPage):
    def __init__(self):
        super(BridgesWizardPage2, self).__init__()

        self.steps = Common.wizard_steps

        self.bridges = ['flashproxy',
                        'fte',
                        'fte-ipv6',
                        'meek-amazon',
                        'meek-azure',
                        'meek-google',
                        'obfs3 (recommended)',
                        'obfs4',
                        'scramblesuit']

        self.layout = QtGui.QVBoxLayout(self)
        self.label = QtGui.QLabel(self)
        self.layout.addWidget(self.label)

        self.label_2 = QtGui.QLabel(self)
        self.layout.addWidget(self.label_2)

        self.groupBox = QtGui.QGroupBox(self)
        self.default_button = QtGui.QRadioButton(self.groupBox)
        self.custom_button = QtGui.QRadioButton(self.groupBox)
        self.label_3 = QtGui.QLabel(self.groupBox)
        self.comboBox = QtGui.QComboBox(self.groupBox)
        self.label_4 = QtGui.QLabel(self.groupBox)
        self.custom_bridges = QtGui.QTextEdit(self.groupBox)
        self.pushButton = QtGui.QPushButton(self.groupBox)
        self.label_5 = QtGui.QLabel(self.groupBox)

        self.layout.addWidget(self.groupBox)
        self.setupUi()

    def setupUi(self):
        self.label.setMinimumSize(QtCore.QSize(16777215, 35))
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setText('   Tor Bridges Configuration')

        self.label_2.setMaximumSize(QtCore.QSize(16777215, 50))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.label_2.setFont(font)
        self.label_2.setWordWrap(True)
        self.label_2.setText('You may use the provided set of briges or you may obtain and enter a custom set of bridges.')

        self.groupBox.setMinimumSize(QtCore.QSize(16777215, 243))
        self.groupBox.setFlat(True)
        self.default_button.setGeometry(QtCore.QRect(18, 3, 500, 24))
        self.default_button.setChecked(True)
        self.default_button.setText('Connect with provided bridges')

        self.custom_button.setGeometry(QtCore.QRect(18, 60, 500, 25))
        self.custom_button.setText('Enter custom bridges')

        self.label_3.setGeometry(QtCore.QRect(38, 25, 106, 20))
        self.label_3.setText('Transport type:')

        self.comboBox.setGeometry(QtCore.QRect(135, 22, 181, 27))
        for bridge in self.bridges:
            self.comboBox.addItem(bridge)
        for bridge in range(0, 6):
            self.comboBox.model().item(bridge).setEnabled(False)
        self.comboBox.setCurrentIndex(6)

        self.label_4.setEnabled(False)
        self.label_4.setGeometry(QtCore.QRect(38, 83, 300, 20))
        self.label_4.setText('Enter one ore more bridge relay (one per line).')

        self.pushButton.setGeometry(QtCore.QRect(450, 70, 86, 25))
        self.pushButton.setText('&Help')
        self.pushButton.clicked.connect(self.show_help)

        self.custom_bridges.setEnabled(False)
        self.custom_bridges.setGeometry(QtCore.QRect(38, 103, 500, 76))
        self.custom_bridges.setStyleSheet("background-color:white;")

        self.label_5.setGeometry(0, 220, 500, 15)
        self.label_5.setText('For assistance, contact help@rt.torproject.org')

    def nextId(self):
        if self.default_button.isChecked():
            bridge_type = str(self.comboBox.currentText())
            if bridge_type.startswith('obfs3'):
                bridge_type = 'obfs3'
            Common.bridge_type = bridge_type

        elif self.custom_button.isChecked():
            pass

        return self.steps.index('proxy_wizard_page_1')

    def show_help(self):
        reply = QtGui.QMessageBox(QtGui.QMessageBox.NoIcon, 'Bridges Configuration Help',
                                  '''<p><b>  Bridge Relay Help</b></p>

<p>If you are unable to connect to the Tor network, it could be that your Internet Service
Provider (ISP) or another agency is blocking Tor.  Often, you can work around this problem
by using Tor Bridges, which are unlisted relays that are more difficult to block.</p>

<p>You may use the preconfigured, provided set of bridge addresses or you may obtain a
custom set of addresses by using one of these three methods:</p>

<blockquote>1.<b>Through the Web</b><br>
Use a web browser to visit https://bridges.torproject.org</blockquote>

<blockquote>2. <b>Through the Email Autoresponder</b><br>
Send email to bridges@torproject.org with the line 'get bridges' by itself in the body
of the message.  However, to make it harder for an attacker to learn a lot of bridge
addresses, you must send this request from one of the following email providers
(listed in order of preference):<br><br>
https://www.riseup.net, https://mail.google.com, or https://mail.yahoo.com</blockquote>

<blockquote>3. <b>Through the Help Desk</b><br>
As a last resort, you can request bridge addresses by sending a polite email
message to help@rt.torproject.org.  Please note that a person will need to respond
to each request.</blockquote>''', QtGui.QMessageBox.Ok)
        reply.exec_()


class ProxyWizardPage1(QtGui.QWizardPage):
    def __init__(self):
        super(ProxyWizardPage1, self).__init__()

        translation = _translations(Common.translations_path, 'whonixsetup')
        self._ = translation.gettext

        self.Common = Common()
        self.steps = self.Common.wizard_steps
        self.env = self.Common.environment

        self.layout = QtGui.QVBoxLayout(self)
        self.label = QtGui.QLabel(self)
        self.layout.addWidget(self.label)

        self.label_2 = QtGui.QLabel(self)
        self.layout.addWidget(self.label_2)

        self.group_box = QtGui.QGroupBox(self)
        self.yes_button = QtGui.QRadioButton(self.group_box)
        self.no_button = QtGui.QRadioButton(self.group_box)
        self.label_3 = QtGui.QLabel(self.group_box)
        self.label_4 = QtGui.QLabel(self.group_box)
        self.layout.addWidget(self.group_box)

        self.setupUi()

    def setupUi(self):
        self.label.setMinimumSize(QtCore.QSize(16777215, 35))
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setText('   Local Proxy Configuration')

        self.label_2.setMaximumSize(QtCore.QSize(16777215, 50))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.label_2.setFont(font)
        self.label_2.setWordWrap(True)
        self.label_2.setText('Does this computer need tot use a local proxy to access the Internet?')

        self.group_box.setMinimumSize(QtCore.QSize(16777215, 250))
        self.group_box.setFlat(True)
        self.yes_button.setGeometry(QtCore.QRect(25, 0, 350, 21))
        self.yes_button.setText('Yes')
        self.no_button.setGeometry(QtCore.QRect(25, 20, 350, 21))
        self.no_button.setText('No')
        self.no_button.setChecked(True)

        #self.label_3.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.label_3.setGeometry(10, 45, 520, 60)
        self.label_3.setTextFormat(QtCore.Qt.RichText)
        self.label_3.setWordWrap(True)
        self.label_3.setText('If you are not sure how to answer this question, look at the Internet \
                              settings in your host browser to see wether it is configured to use \
                              a local proxy')

        self.label_4.setGeometry(0, 235, 500, 15)
        self.label_4.setText('For assistance, contact help@rt.torproject.org')

    def nextId(self):
        if self.yes_button.isChecked():
            return self.steps.index('proxy_wizard_page_2')
        elif self.no_button.isChecked():
            #if Common.run_repo:
            return self.steps.index('tor_status_page')
            #else:
                #return self.steps.index('finish_page')


class ProxyWizardPage2(QtGui.QWizardPage):
    def __init__(self):
        super(ProxyWizardPage2, self).__init__()

        Common.use_proxy = True
        translation = _translations(Common.translations_path, 'whonixsetup')
        self._ = translation.gettext

        self.Common = Common()
        self.steps = self.Common.wizard_steps
        self.env = self.Common.environment

        #self.verticalLayout = QtGui.QVBoxLayout(self)
        self.layout = QtGui.QVBoxLayout(self)
        self.label = QtGui.QLabel(self)
        self.layout.addWidget(self.label)

        self.groupBox = QtGui.QGroupBox(self)
        self.label_3 = QtGui.QLabel(self.groupBox)
        self.comboBox = QtGui.QComboBox(self.groupBox)
        self.label_2 = QtGui.QLabel(self.groupBox)
        self.label_5 = QtGui.QLabel(self.groupBox)
        self.label_6 = QtGui.QLabel(self.groupBox)
        self.lineEdit = QtGui.QLineEdit(self.groupBox)
        self.label_7 = QtGui.QLabel(self.groupBox)
        self.lineEdit_2 = QtGui.QLineEdit(self.groupBox)
        self.lineEdit_3 = QtGui.QLineEdit(self.groupBox)
        self.lineEdit_4 = QtGui.QLineEdit(self.groupBox)
        self.label_8 = QtGui.QLabel(self.groupBox)
        self.label_4 = QtGui.QLabel(self.groupBox)
        self.layout.addWidget(self.groupBox)

        self.setupUi()

    def setupUi(self):
        self.label.setMinimumSize(QtCore.QSize(16777215, 35))
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setText('   Local Proxy Configuration')

        self.groupBox.setMinimumSize(QtCore.QSize(16777215, 300))
        self.groupBox.setFlat(True)

        self.label_3.setGeometry(QtCore.QRect(10, 40, 106, 20))
        self.label_3.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_3.setText("Proxy type:")

        self.comboBox.setGeometry(QtCore.QRect(118, 38, 111, 27))

        self.label_2.setGeometry(QtCore.QRect(4, 10, 201, 16))
        self.label_2.setText("Enter the proxy settings.")

        self.label_5.setGeometry(QtCore.QRect(10, 71, 106, 20))
        self.label_5.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_5.setText("Address:")

        self.label_6.setGeometry(QtCore.QRect(10, 101, 106, 20))
        self.label_6.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_6.setText("Username:")

        self.label_7.setGeometry(QtCore.QRect(394, 71, 41, 20))
        self.label_7.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_7.setText("Port:")

        self.label_8.setGeometry(QtCore.QRect(280, 101, 70, 20))
        self.label_8.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_8.setText("Password:")

        self.lineEdit.setGeometry(QtCore.QRect(118, 68, 260, 25))
        self.lineEdit.setStyleSheet("background-color:white;")
        self.lineEdit.setPlaceholderText('IP address or hostname')
        self.lineEdit_2.setGeometry(QtCore.QRect(437, 68, 60, 25))
        self.lineEdit_2.setStyleSheet("background-color:white;")
        self.lineEdit_3.setGeometry(QtCore.QRect(118, 98, 150, 25))
        self.lineEdit_3.setStyleSheet("background-color:white;")
        self.lineEdit_3.setPlaceholderText('Optional')
        self.lineEdit_4.setGeometry(QtCore.QRect(352, 98, 145, 25))
        self.lineEdit_4.setStyleSheet("background-color:white;")
        self.lineEdit_4.setPlaceholderText('Optional')

        self.label_4.setGeometry(QtCore.QRect(0, 255, 391, 16))
        self.label_4.setText("For assistance, contact help@rt.torproject.org'")


class TorStatusPage(QtGui.QWizardPage):
    def __init__(self):
        super(TorStatusPage, self).__init__()

        self.steps = Common.wizard_steps

        self.icon = QtGui.QLabel(self)
        self.bootstrap_text = QtGui.QLabel(self)
        self.text = QtGui.QTextBrowser(self)
        self.torrc = QtGui.QPlainTextEdit(self)
        self.bootstrap_progress = QtGui.QProgressBar(self)

        self.layout = QtGui.QGridLayout()
        self.setupUi()

    def setupUi(self):
        self.icon.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.icon.setMinimumSize(50, 0)
        self.icon.setVisible(False)

        #self.bootstrap_text.setText('<b>Bootstrapping Tor...</b>')
        self.text.setFrameShape(QtGui.QFrame.NoFrame)
        self.text.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)

        self.torrc.setMinimumSize(0, 205)
        self.torrc.setReadOnly(True)
        self.torrc.setVisible(False)

        self.bootstrap_progress.setMinimumSize(400, 0)
        self.bootstrap_progress.setMinimum(0)
        self.bootstrap_progress.setMaximum(100)
        self.bootstrap_progress.setVisible(False)

        self.layout.addWidget(self.icon, 0, 0, 1, 1)
        #self.layout.addWidget(self.bootstrap_text, 0, 1, 1, 3)
        self.layout.addWidget(self.text, 0, 1, 1, 2)
        self.layout.addWidget(self.bootstrap_progress, 1, 1, 1, 1)
        self.layout.addWidget(self.torrc, 1, 1, 1, 1)
        self.setLayout(self.layout)

    def nextId(self):
        if Common.run_repo:
            return self.steps.index('whonix_repo_page')
        else:
            return self.steps.index('finish_page')


class WhonixRepositoryPage(QtGui.QWizardPage):
    def __init__(self):
        super(WhonixRepositoryPage, self).__init__()

        self.steps = Common.wizard_steps

        self.text = QtGui.QTextBrowser(self)
        self.layout = QtGui.QGridLayout()

        self.setupUi()

    def setupUi(self):
        self.text.setFrameShape(QtGui.QFrame.NoFrame)
        self.text.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)

        self.layout.addWidget(self.text)
        self.setLayout(self.layout)

    def nextId(self):
        Common.run_repo = True
        return self.steps.index('repository_wizard_page_1')


class RepositoryWizardPage1(QtGui.QWizardPage):
    def __init__(self):
        super(RepositoryWizardPage1, self).__init__()

        self.steps = Common.wizard_steps

        self.text = QtGui.QTextBrowser(self)

        self.enable_group = QtGui.QGroupBox(self)
        self.enable_repo = QtGui.QRadioButton(self.enable_group)
        self.disable_repo = QtGui.QRadioButton(self.enable_group)

        self.layout = QtGui.QVBoxLayout()

        self.setupUi()

    def setupUi(self):
        self.text.setFrameShape(QtGui.QFrame.NoFrame)
        self.text.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.text.setOpenExternalLinks(True)

        self.enable_group.setMinimumSize(0, 60)
        self.enable_repo.setGeometry(QtCore.QRect(30, 10, 400, 21))
        self.disable_repo.setGeometry(QtCore.QRect(30, 30, 400, 21))

        self.enable_repo.setChecked(True)

        self.layout.addWidget(self.text)
        self.layout.addWidget(self.enable_group)
        self.setLayout(self.layout)

    def nextId(self):
        if self.enable_repo.isChecked():
            return self.steps.index('repository_wizard_page_2')

        elif self.disable_repo.isChecked():
            Common.disable_repo = True
            return self.steps.index('repository_wizard_finish')


class RepositoryWizardPage2(QtGui.QWizardPage):
    def __init__(self):
        super(RepositoryWizardPage2, self).__init__()

        self.text = QtGui.QTextBrowser(self)

        self.repo_group = QtGui.QGroupBox(self)
        self.stable_repo = QtGui.QRadioButton(self.repo_group)
        self.testers_repo = QtGui.QRadioButton(self.repo_group)
        self.devs_repo = QtGui.QRadioButton(self.repo_group)

        self.layout = QtGui.QVBoxLayout()

        self.setupUi()

    def setupUi(self):
        self.text.setFrameShape(QtGui.QFrame.NoFrame)
        self.text.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)

        self.repo_group.setMinimumSize(0, 80)
        self.stable_repo.setGeometry(QtCore.QRect(30, 10, 400, 21))
        self.testers_repo.setGeometry(QtCore.QRect(30, 30, 400, 21))
        self.devs_repo.setGeometry(QtCore.QRect(30, 50, 400, 21))

        self.stable_repo.setText("Whonix Stable Repository")
        self.testers_repo.setText("Whonix Testers Repository")
        self.devs_repo.setText("Whonix Developers Repository")

        self.stable_repo.setChecked(True)

        self.layout.addWidget(self.text)
        self.layout.addWidget(self.repo_group)
        self.setLayout(self.layout)


class RepositoryWizardfinish(QtGui.QWizardPage):
    def __init__(self):
        super(RepositoryWizardfinish, self).__init__()

        self.text = QtGui.QTextBrowser(self)
        self.layout = QtGui.QVBoxLayout()

        self.setupUi()

    def setupUi(self):
        self.text.setFrameShape(QtGui.QFrame.NoFrame)
        self.text.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)

        self.layout.addWidget(self.text)
        self.setLayout(self.layout)


class FinishPage(QtGui.QWizardPage):
    def __init__(self):
        super(FinishPage, self).__init__()

        self.icon = QtGui.QLabel(self)
        self.text = QtGui.QTextBrowser(self)

        self.layout = QtGui.QGridLayout()
        self.setupUi()

    def setupUi(self):
        self.icon.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.icon.setMinimumSize(50, 0)

        self.text.setFrameShape(QtGui.QFrame.NoFrame)
        self.text.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)

        self.layout.addWidget(self.icon, 0, 0, 1, 1)
        self.layout.addWidget(self.text, 0, 1, 1, 1)
        self.setLayout(self.layout)


class FirstUseNotice(QtGui.QWizardPage):
    def __init__(self):
        super(FirstUseNotice, self).__init__()

        self.text = QtGui.QTextBrowser(self)

        self.layout = QtGui.QVBoxLayout()
        self.setupUi()

    def setupUi(self):
        self.text.setFrameShape(QtGui.QFrame.NoFrame)
        self.text.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.text.setOpenExternalLinks(True)

        self.layout.addWidget(self.text)
        self.setLayout(self.layout)


class WhonixSetupWizard(QtGui.QWizard):
    def __init__(self):
        super(WhonixSetupWizard, self).__init__()

        translation = _translations(Common.translations_path, 'whonixsetup')
        self._ = translation.gettext

        self.steps = Common.wizard_steps
        self.env = Common.environment

        if Common.argument == 'repository':
            self.repository_wizard_page_1 = RepositoryWizardPage1()
            self.addPage(self.repository_wizard_page_1)

            self.repository_wizard_page_2 = RepositoryWizardPage2()
            self.addPage(self.repository_wizard_page_2)

            self.repository_wizard_finish = RepositoryWizardfinish()
            self.addPage(self.repository_wizard_finish)

        if Common.argument == 'setup':
            if Common.show_disclaimer:
                self.disclaimer_1 = DisclaimerPage1()
                self.addPage(self.disclaimer_1)

                self.disclaimer_2 = DisclaimerPage2()
                self.addPage(self.disclaimer_2)

            if Common.run_whonixcheck_only:
                self.finish_page = FinishPage()
                self.addPage(self.finish_page)

            else:
                if self.env == 'gateway':
                    self.connection_main_page = ConnectionMainPage()
                    self.addPage(self.connection_main_page)

                    self.bridge_wizard_page_1 = BridgesWizardPage1()
                    self.addPage(self.bridge_wizard_page_1)

                    self.bridge_wizard_page_2 = BridgesWizardPage2()
                    self.addPage(self.bridge_wizard_page_2)

                    self.proxy_wizard_page_1 = ProxyWizardPage1()
                    self.addPage(self.proxy_wizard_page_1)

                    self.proxy_wizard_page_2 = ProxyWizardPage2()
                    self.addPage(self.proxy_wizard_page_2)

                    self.tor_status_page = TorStatusPage()
                    self.addPage(self.tor_status_page)

                self.whonix_repo_page = WhonixRepositoryPage()
                self.addPage(self.whonix_repo_page)

                self.repository_wizard_page_1 = RepositoryWizardPage1()
                self.addPage(self.repository_wizard_page_1)

                self.repository_wizard_page_2 = RepositoryWizardPage2()
                self.addPage(self.repository_wizard_page_2)

                self.repository_wizard_finish = RepositoryWizardfinish()
                self.addPage(self.repository_wizard_finish)

                self.finish_page = FinishPage()
                self.addPage(self.finish_page)

                if self.env == 'gateway'and Common.first_use_notice:
                    self.first_use_notice = FirstUseNotice()
                    self.addPage(self.first_use_notice)

        if Common.argument == 'locale_settings':
            self.locale_settings = LocaleSettings()
            self.addPage(self.locale_settings)

            self.locale_settings_finish = LocaleSettingsFinish()
            self.addPage(self.locale_settings_finish)

        self.setupUi()

    def setupUi(self):
        self.setWindowIcon(QtGui.QIcon("/usr/share/icons/anon-icon-pack/whonix.ico"))
        self.setWindowTitle('Whonix Setup Wizard')

        available_height = QtGui.QDesktopWidget().availableGeometry().height() - 60
        self.disclaimer_height = 750
        if available_height < self.disclaimer_height:
            self.disclaimer_height = available_height

        if Common.argument == 'setup' and not Common.run_whonixcheck_only:
            self.resize(760, self.disclaimer_height)
        elif Common.argument == 'repository':
            self.resize(580, 400)
        elif Common.argument == 'locale_settings':
            self.resize(440, 168)

        # We use QTextBrowser with a white background.
        # Set a default (transparent) background.
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(244, 244, 244))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Base, brush)
        self.setPalette(palette)

        try:
            if Common.run_whonixcheck_only:
                self.finish_page.icon.setPixmap(QtGui.QPixmap( \
                '/usr/share/icons/oxygen/48x48/status/task-complete.png'))
                self.finish_page.text.setText(self._('finish_page_ok'))
                Common.is_complete = True

            else:
                if Common.argument == 'setup' and Common.show_disclaimer:
                    self.disclaimer_1.text.setText(self._('disclaimer_1'))
                    self.disclaimer_1.yes_button.setText(self._('accept'))
                    self.disclaimer_1.no_button.setText(self._('reject'))

                    self.disclaimer_2.text.setText(self._('disclaimer_2'))
                    self.disclaimer_2.yes_button.setText(self._('accept'))
                    self.disclaimer_2.no_button.setText(self._('reject'))

                #if Common.argument == 'setup'and self.env == 'gateway':
                    #self.bridge_wizard_page_1.text.setText(self._('connection_text'))
                    #self.bridge_wizard_page_1.enable.setText(self._('enable_tor'))
                    #self.bridge_wizard_page_1.disable.setText(self._('disable_tor'))
                    #self.bridge_wizard_page_1.censored.setText(self._('censored_tor'))
                    #self.bridge_wizard_page_1.use_proxy.setText(self._('use_proxy'))

                    if Common.first_use_notice:
                        self.first_use_notice.text.setText(self._('first_use_notice'))


                if ((Common.argument == 'setup' or Common.argument == 'repository')
                    and not Common.run_whonixcheck_only):
                    self.repository_wizard_page_1.text.setText(self._('repo_page_1'))
                    self.repository_wizard_page_1.enable_repo.setText(self._('repo_enable'))
                    self.repository_wizard_page_1.disable_repo.setText(self._('repo_disable'))

                    self.repository_wizard_page_2.text.setText(self._('repo_page_2'))

        except (yaml.scanner.ScannerError, yaml.parser.ParserError):
            pass

        #self.button(QtGui.QWizard.CancelButton).setVisible(False)
        self.button(QtGui.QWizard.NextButton).hide()#setEnabled(False)
        self.button(QtGui.QWizard.BackButton).setVisible(False)
        self.button(QtGui.QWizard.CancelButton).setVisible(False)

        self.button(QtGui.QWizard.BackButton).clicked.connect(self.back_button_clicked)
        self.button(QtGui.QWizard.NextButton).clicked.connect(self.next_button_clicked)

        # Temporary workaround.
        # The pluggable transports are not implemented yet, but we want to
        # be able to display the tooltips for censored and firewall. For this,
        # the options must be enabled, but the slot will disable the Next
        # button if either is checked.
        #if Common.argument == 'setup':
            #if self.env == 'gateway':
                #self.bridge_wizard_page_1.censored.toggled.connect(self.set_next_button_state)
                #self.bridge_wizard_page_1.use_proxy.toggled.connect(self.set_next_button_state)

        if not Common.show_disclaimer and not Common.argument == 'locale_settings':
            self.setMaximumSize(580, 400)
            self.setMinimumSize(580, 400)

        self.exec_()

    # called by button toggled signal.
    def set_next_button_state(self, state):
        if state:
            self.button(QtGui.QWizard.NextButton).setEnabled(False)
        else:
            self.button(QtGui.QWizard.NextButton).setEnabled(True)

    def center(self):
        """ After the window is resized, its origin point becomes the
        previous window top left corner.
        Re-center the window on the screen.
        """
        frame_gm = self.frameGeometry()
        center_point = QtGui.QDesktopWidget().availableGeometry().center()
        frame_gm.moveCenter(center_point)
        self.move(frame_gm.topLeft())

    def next_button_clicked(self):
        """ Next button slot.
        The commands cannot be implemented in the wizard's nextId() function,
        as it is polled by the event handler on the creation of the page.
        Depending on the checkbox states, the commands would be run when the
        page is loaded.
        Those button_clicked functions are called once, when the user clicks
        the corresponding button.
        Options (like button states, window size changes...) are set here.
        """
        if Common.argument == 'setup':
            if self.env == 'workstation':
                if (self.currentId() == self.steps.index('whonix_repo_page') or
                    self.currentId() == self.steps.index('finish_page')):
                    self.resize(470, 310)
                    self.center()

            if self.env == 'gateway':
                # Set Next button state
                if self.currentId() == self.steps.index('connection_main_page'):
                    self.resize(580, 400)
                    self.center()

                if self.currentId() == self.steps.index('tor_status_page'):
                    ## Get a fresh torrc
                    shutil.copy('/etc/tor/torrc', '/etc/tor/torrc.orig')
                    shutil.copy('/etc/tor/torrc.anondist', '/etc/tor/torrc')

                    if Common.use_bridges:
                        bridges = json.loads(open('/etc/bridges/default.json').read())
                        with open('/etc/tor/torrc', 'a') as f:
                            f.write('UseBridges 1\n')

                            if Common.bridge_type == 'obfs3':
                                f.write('ClientTransportPlugin obfs2,obfs3 exec /usr/bin/obfsproxy managed\n')
                            elif Common.bridge_type == 'scramblesuit':
                                f.write('ClientTransportPlugin obfs2,obfs3,scramblesuit exec /usr/bin/obfsproxy managed\n')
                            elif Common.bridge_type == 'obfs4':
                                f.write('ClientTransportPlugin obfs4 exec /usr/bin/obfs4proxy managed\n')

                            for bridge in bridges['bridges'][Common.bridge_type]:
                                f.write('Bridge %s\n' % bridge)

                    if Common.use_proxy:
                        pass

                    QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
                    Common.tor_status = tor_status.set_enabled()

                    if Common.tor_status == 'tor_enabled' or Common.tor_status == 'tor_already_enabled':
                        if Common.exit_after_tor_enabled:
                            sys.exit(0)
                        c = Controller.from_port(address = '127.0.0.1', port = 9051)
                        c.authenticate()
                        bootstrap_status = c.get_info("status/bootstrap-phase")
                        bootstrap_percent = int(re.match('.* PROGRESS=([0-9]+).*', bootstrap_status).group(1))
                        if bootstrap_percent < 100:
                            bootstrap_timeout = False
                            bootstrap_start_time = time.time()
                            print bootstrap_start_time
                            bootstrap_phase = re.search(r'SUMMARY=(.*)', bootstrap_status).group(1)
                            self.tor_status_page.text.setText('<p><b>Bootstrapping Tor...</b></p>Bootstrap phase: %s' % bootstrap_phase)
                            self.tor_status_page.bootstrap_progress.setVisible(True)
                            self.tor_status_page.bootstrap_progress.setValue(bootstrap_percent)
                            while True:#bootstrap_percent < 100:
                                time.sleep(0.1)
                                bootstrap_status = c.get_info("status/bootstrap-phase")
                                bootstrap_phase = re.search(r'SUMMARY=(.*)', bootstrap_status).group(1)
                                bootstrap_percent = int(re.match('.* PROGRESS=([0-9]+).*', bootstrap_status).group(1))
                                self.tor_status_page.text.setText('<p><b>Bootstrapping Tor...</b></p>Bootstrap phase: %s' % bootstrap_phase)
                                self.tor_status_page.bootstrap_progress.setValue(bootstrap_percent)
                                if bootstrap_percent == 100:
                                    break
                                elapsed_time = time.time() - bootstrap_start_time
                                if elapsed_time >= 120:
                                    bootstrap_timeout = True
                                    break

                        QApplication.restoreOverrideCursor()

                        self.tor_status_page.icon.setVisible(True)
                        self.tor_status_page.bootstrap_progress.setVisible(False)

                        torrc_text = open('/etc/tor/torrc').read()
                        if not bootstrap_timeout:
                            self.tor_status_page.text.setText(self._('tor_enabled'))
                            self.tor_status_page.icon.setPixmap(QtGui.QPixmap( \
                                '/usr/share/icons/oxygen/48x48/status/task-complete.png'))
                        else:
                            self.tor_status_page.text.setText('Tor bootstrap result:<br><b>Whonix Connection Wizard \
                                gave up after %d seconds.</b><br>Possible issues:<blockquote>- Is the host internet connection working? \
                                <br>- Do you live in a censored area?</blockquote><p>If you are using a pluggable transport, \
                                please check "Bridge" lines in <i>/etc/tor/torrc:</i></p>' % elapsed_time)
                            self.tor_status_page.torrc.setMinimumSize(0, 175)
                            self.tor_status_page.icon.setPixmap(QtGui.QPixmap( \
                                '/usr/share/icons/oxygen/48x48/status/task-reject.png'))
                        self.tor_status_page.torrc.setVisible(True)
                        self.tor_status_page.torrc.setPlainText(torrc_text)

                    else:
                        QApplication.restoreOverrideCursor()
                        #self.tor_status_page.torrc.setFrameShape(QtGui.QFrame.NoFrame)
                        self.tor_status_page.text.setText(self._('something_wrong'))
                        self.tor_status_page.icon.setPixmap(QtGui.QPixmap( \
                            '/usr/share/icons/oxygen/48x48/status/task-reject.png'))
                        torrc_text = open('/etc/tor/torrc').read()
                        self.tor_status_page.torrc.setVisible(True)
                        self.tor_status_page.torrc.setPlainText(torrc_text)

                    #elif self.bridge_wizard_page_1.disable.isChecked():

                        #QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
                        #Common.tor_status = tor_status.set_disabled()
                        #QApplication.restoreOverrideCursor()

                        #if Common.tor_status == 'tor_disabled':
                            #self.bridge_wizard_page_2.text.setText(self._('tor_disabled'))
                            #torrc_text = open('/etc/tor/torrc').read()
                            #self.bridge_wizard_page_2.torrc.setPlainText(torrc_text)
                            #self.bridge_wizard_page_2.icon.setPixmap(QtGui.QPixmap( \
                                #'/usr/share/icons/oxygen/48x48/status/task-attention.png'))

                        #elif Common.tor_status == 'tor_already_disabled':
                            #self.bridge_wizard_page_2.text.setText(self._('tor_already_disabled'))
                            #torrc_text = open('/etc/tor/torrc').read()
                            #self.bridge_wizard_page_2.torrc.setPlainText(torrc_text)
                            #self.bridge_wizard_page_2.icon.setPixmap(QtGui.QPixmap( \
                                #'/usr/share/icons/oxygen/48x48/status/task-attention.png'))

                        #else:
                            #self.bridge_wizard_page_2.torrc.setFrameShape(QtGui.QFrame.NoFrame)
                            #self.bridge_wizard_page_2.text.setText(self._('something_wrong'))
                            #self.bridge_wizard_page_2.icon.setPixmap(QtGui.QPixmap( \
                                #'/usr/share/icons/oxygen/48x48/status/task-reject.png'))

            if self.currentId() == self.steps.index('whonix_repo_page'):
                self.whonix_repo_page.text.setText(self._('whonix_repository_page'))

        if Common.argument == 'setup' or Common.argument == 'repository':
            if self.currentId() == self.steps.index('repository_wizard_finish'):
                if Common.disable_repo:
                    command = 'whonix_repository --disable'

                    QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
                    exit_code = call(command, shell=True)
                    QApplication.restoreOverrideCursor()

                    mypath = inspect.getfile(inspect.currentframe())

                    if exit_code == 0:
                        self.repository_wizard_finish.text.setText(self._('repo_finish_disabled'))
                        message = 'INFO %s: Ok, exit code of "%s" was %s.' % ( mypath, command, exit_code )

                    else:
                        error = '<p>ERROR %s: exit code of \"%s\" was %s.</p>' % ( mypath, command, exit_code )
                        finish_text_failed =  error + self.finish_text_failed
                        self.repository_wizard_finish.text.setText(self._('repo_finish_failed'))
                        message = error

                    command = 'echo ' + message
                    call(command, shell=True)
                    self.one_shot = False

                else:
                    if self.repository_wizard_page_2.stable_repo.isChecked():
                        codename = ' --repository stable'

                    elif self.repository_wizard_page_2.testers_repo.isChecked():
                        codename = ' --repository testers'

                    elif self.repository_wizard_page_2.devs_repo.isChecked():
                        codename = ' --repository developers'

                    command = 'whonix_repository --enable' + codename

                    QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
                    exit_code = call(command, shell=True)
                    QApplication.restoreOverrideCursor()

                    mypath = inspect.getfile(inspect.currentframe())

                    if exit_code == 0:
                        self.repository_wizard_finish.text.setText(self._('repo_finish_enabled'))
                        message = 'INFO %s: Ok, exit code of "%s" was %s.' % ( mypath, command, exit_code )

                    else:
                        error = '<p>ERROR %s: exit code of \"%s\" was %s.</p>' % ( mypath, command, exit_code )
                        finish_text_failed =  error + self.finish_text_failed
                        self.repository_wizard_finish.text.setText(self._('repo_finish_failed'))
                        message = error

                    command = 'echo ' + message
                    call(command, shell=True)
                    self.one_shot = False

        if Common.argument == 'setup':
            if self.currentId() == self.steps.index('finish_page'):

                # for whonixcheck.
                Common.is_complete = True

                if self.env == 'gateway':
                    if (Common.tor_status == 'tor_enabled' or
                        Common.tor_status == 'tor_already_enabled'):
                            self.finish_page.icon.setPixmap(QtGui.QPixmap( \
                                '/usr/share/icons/oxygen/48x48/status/task-complete.png'))
                            self.finish_page.text.setText(self._('finish_page_ok'))

                    else:
                        Common.is_complete = False

                        if (Common.tor_status == 'tor_disabled' or
                            Common.tor_status == 'tor_already_disabled'):
                            self.finish_page.icon.setPixmap(QtGui.QPixmap( \
                                '/usr/share/icons/oxygen/48x48/status/task-attention.png'))
                            self.finish_page.text.setText(self._('finish_disabled'))

                        # ERROR pages.
                        elif Common.tor_status == 'no_torrc':
                            self.finish_page.icon.setPixmap(QtGui.QPixmap( \
                                '/usr/share/icons/oxygen/48x48/status/task-reject.png'))
                            self.button(QtGui.QWizard.BackButton).setEnabled(False)
                            self.finish_page.text.setText(self._('no_torrc'))

                        elif Common.tor_status == 'bad_torrc':
                            self.finish_page.icon.setPixmap(QtGui.QPixmap( \
                                '/usr/share/icons/oxygen/48x48/status/task-reject.png'))
                            self.button(QtGui.QWizard.BackButton).setEnabled(False)
                            self.finish_page.text.setText(self._('bad_torrc'))

                        elif Common.tor_status == 'cannot_connect':
                            # #DisableNetwork 0 was uncommented. re-comment.
                            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
                            Common.tor_status = tor_status.set_disabled()
                            QApplication.restoreOverrideCursor()

                            self.finish_page.icon.setPixmap(QtGui.QPixmap( \
                                '/usr/share/icons/oxygen/48x48/status/task-reject.png'))
                            self.button(QtGui.QWizard.BackButton).setEnabled(False)
                            self.finish_page.text.setText(self._('cannot_connect'))

                if Common.show_disclaimer:
                    # Disclaimer page 1 not understood -> leave
                    if self.disclaimer_1.no_button.isChecked():
                        self.hide()
                        command = '/sbin/poweroff'
                        call(command, shell=True)

                    # Disclaimer page 2 not understood -> leave
                    if self.disclaimer_2.no_button.isChecked():
                        self.hide()
                        command = '/sbin/poweroff'
                        call(command, shell=True)

                if self.env == 'workstation':
                    self.finish_page.icon.setPixmap(QtGui.QPixmap( \
                    '/usr/share/icons/oxygen/48x48/status/task-complete.png'))
                    self.finish_page.text.setText(self._('finish_page_ok'))

        if Common.argument == 'locale_settings':
            if self.currentId() == self.steps.index('locale_settings_finish'):

                if self.locale_settings.other_button.isChecked():
                    kcmshell = distutils.spawn.find_executable("kcmshell4")

                    if self.locale_settings.lang_checkbox.isChecked():
                        command = command = '%s language' % (kcmshell)
                        call(command, shell=True)

                    if self.locale_settings.kbd_checkbox.isChecked():
                        command = command = '%s kcm_keyboard' % (kcmshell)
                        call(command, shell=True)

                    self.button(QtGui.QWizard.BackButton).setEnabled(False)

                self.locale_settings_finish.text.setText(self._('locale_finish'))

    def back_button_clicked(self):
        Common.is_complete = False

        if Common.argument == 'setup' and Common.show_disclaimer:
            if self.currentId() == self.steps.index('disclaimer_2'):
                # Back to disclaimer size.
                self.resize(760, self.disclaimer_height)
                self.center()

        if self.currentId() == self.steps.index('bridge_wizard_page_1'):
            Common.use_bridges = False
            #self.setOption(self.HaveHelpButton, True)
            #self.button(QtGui.QWizard.CancelButton).setVisible(False)
        #else:
            #self.setOption(self.HaveHelpButton, False)
            #self.button(QtGui.QWizard.CancelButton).setVisible(False)


def main():
    #import sys
    app = QtGui.QApplication(sys.argv)
    QtGui.QApplication.setStyle('cleanlooks')

    # locale settings are implemented for KDE desktop only.
    # skip if other desktop.
    if sys.argv[1] == 'locale_settings':
        kcmshell = distutils.spawn.find_executable("kcmshell4")
        if kcmshell == None:
            print 'kcmshell4 not found. Exiting'
            sys.exit()

    # root check.
    # locale_settings has to be run as user.
    #if sys.argv[1] != 'locale_settings':
        #if os.getuid() != 0:
            #print 'ERROR: This must be run as root!\nUse "kdesudo".'
            #not_root = gui_message(Common.translations_path, 'not_root')
            #sys.exit(1)

    wizard = WhonixSetupWizard()

    if Common.run_repo:
        f = open('/var/cache/whonix-setup-wizard/status-files/whonix_repository.done', 'w')
        f.close()

    if Common.show_disclaimer:
        f = open('/var/cache/whonix-setup-wizard/status-files/disclaimer.done', 'w')
        f.close()

    if Common.first_use_notice:
        f = open('/var/cache/whonix-setup-wizard/status-files/first_use_check.done', 'w')
        f.close()

    if Common.is_complete:
        if not os.path.exists('/var/cache/whonix-setup-wizard/status-files/whonixsetup.done'):
            f = open('/var/cache/whonix-setup-wizard/status-files/whonixsetup.done', 'w')
            f.close()
        # run whonixcheck
        command = '/usr/lib/whonixsetup_/ft_m_end'
        call(command, shell=True)

    sys.exit()

if __name__ == "__main__":
    main()
