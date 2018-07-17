#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

""" WHONIX SETUP WIZARD """
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from PyQt5 import QtCore, QtGui, QtWidgets
from subprocess import call
import os, yaml
import inspect
import sys

from guimessages.translations import _translations
from guimessages.guimessage import gui_message

import shutil

def parse_command_line_parameter():
    '''
    The wizard might be run from terminal.
    '''
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument('option', choices=['setup', 'repository', 'locale_settings'])
    args, unknown_args = parser.parse_known_args()

    return args.option

class Common:
    '''
    Variables and constants used through all the classes
    '''
    translations_path ='/usr/share/translations/whonix_setup.yaml'
    is_complete = False
    first_use_notice = (\
        not os.path.exists('/var/cache/whonix-setup-wizard/status-files/first_use_check.done') and\
        not os.path.exists('/var/cache/whonix-setup-wizard/status-files/first_use_check.skip'))

    if not os.path.exists('/var/cache/whonix-setup-wizard/status-files'):
        os.mkdir('/var/cache/whonix-setup-wizard/status-files')

    argument = parse_command_line_parameter()

    ## Determine environment
    if os.path.isfile('/usr/share/anon-gw-base-files/gateway'):
        environment = 'gateway'
    elif os.path.isfile('/usr/share/anon-ws-base-files/workstation'):
        environment = 'workstation'
    else:
        print("Whonix-Setup-Wizard cannot decide environment: marker file in /usr/share/anon-ws-base-files/workstation is missing.")

    ## For legacy syntax compatibility.
    if argument == 'repository':
        whonix_repository_wizard = shutil.which("whonix-repository-wizard")
        if whonix_repository_wizard == None:
            print('ERROR: whonix_repository_wizard not found! Exiting.')
            sys.exit(1)
        ## Already running under kdesudo as tested in main().
        command = '{}'.format(whonix_repository_wizard)
        call(command, shell=True)
        # run whonixcheck only when setup or repository option is selected.
        # note that the case for setup will be handled at the end, not here.
        command = '/usr/lib/whonixsetup_/ft_m_end'
        call(command, shell=True)

        sys.exit()
    elif argument == 'setup':
        if environment == 'gateway':
            '''
            anon_connection_wizard is only installed in whonix-gw.
            ConnectionPage is only called in whonix-gw, too.
            Therefore, it is reasonable to move the import here to prevent
            missing dependency that happpen when import anon_connection_wizard in whonix-ws.
            '''
            from anon_connection_wizard import anon_connection_wizard
            anon_connection_wizard = anon_connection_wizard.main()
            wizard_steps = []
            if(first_use_notice):
                wizard_steps.append('first_use_notice')
        elif environment == 'workstation':
            wizard_steps = []
    elif argument == 'locale_settings':
        wizard_steps = ['locale_settings',
                        'locale_settings_finish']
    else:
        print("Unexpected command line argument: {}".format(argument))

class LocaleSettings(QtWidgets.QWizardPage):
    def __init__(self):
        super(LocaleSettings, self).__init__()

        self.text = QtWidgets.QLabel(self)

        self.group = QtWidgets.QGroupBox(self)

        self.default_button = QtWidgets.QRadioButton(self.group)
        self.other_button = QtWidgets.QRadioButton(self.group)

        self.lang_checkbox = QtWidgets.QCheckBox(self.group)
        self.kbd_checkbox = QtWidgets.QCheckBox(self.group)

        self.layout = QtWidgets.QVBoxLayout(self)

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


class LocaleSettingsFinish(QtWidgets.QWizardPage):
    def __init__(self):
        super(LocaleSettingsFinish, self).__init__()

        self.text = QtWidgets.QTextBrowser(self)
        self.layout = QtWidgets.QVBoxLayout()

        self.setup_ui()

    def setup_ui(self):
        self.text.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.layout.addWidget(self.text)

        self.setLayout(self.layout)

class ConnectionPage(QtWidgets.QWizardPage):
    def __init__(self):
        super(ConnectionPage, self).__init__()

        translation = _translations(Common.translations_path, 'whonixsetup')
        self._ = translation.gettext

        self.Common = Common()
        self.steps = self.Common.wizard_steps
        self.env = self.Common.environment

        self.text = QtWidgets.QTextBrowser(self)
        self.layout = QtWidgets.QGridLayout()

        self.layout = QtWidgets.QVBoxLayout()

        self.pushButton_acw = QtWidgets.QPushButton(self)
        self.pushButton_acw.setChecked(True)

        self.pushButton_acw.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred,
            QtWidgets.QSizePolicy.Expanding
        )

        self.layout.addWidget(self.text)
        self.layout.addWidget(self.pushButton_acw, 5)

        self.setupUi()

    def setupUi(self):
        self.text.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.text.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)

        self.font_big = QtGui.QFont()
        self.font_big.setPointSize(20)
        self.font_big.setBold(True)
        self.font_big.setWeight(70)

        self.pushButton_acw.setEnabled(True)
        self.pushButton_acw.setText('Launch Anon Connection Wizard')
        self.pushButton_acw.setFont(self.font_big)
        self.pushButton_acw.clicked.connect(self.acw)

        self.setLayout(self.layout)

        # We disable the next button until anon_connection_wizard is run successfully
        # TODO: this is not implemented
        #QtWidgets.QWizard.NextButton.setEnabled(True)

    def acw(self):
        anon_connection_wizard.main()
        self.pushButton_acw.setText('Relaunch Anon Connection Wizard')

            #QtWidgets.QWizard.NextButton.setEnabled(True)

class FinishPage(QtWidgets.QWizardPage):
    def __init__(self):
        super(FinishPage, self).__init__()

        self.icon = QtWidgets.QLabel(self)
        self.text = QtWidgets.QTextBrowser(self)

        self.layout = QtWidgets.QGridLayout()
        self.setupUi()

    def setupUi(self):
        self.icon.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.icon.setMinimumSize(50, 0)

        self.text.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.text.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)

        self.layout.addWidget(self.icon, 0, 0, 1, 1)
        self.layout.addWidget(self.text, 0, 1, 1, 1)
        self.setLayout(self.layout)


class FirstUseNotice(QtWidgets.QWizardPage):
    def __init__(self):
        super(FirstUseNotice, self).__init__()

        self.text = QtWidgets.QTextBrowser(self)

        self.layout = QtWidgets.QVBoxLayout()
        self.setupUi()

    def setupUi(self):
        self.text.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.text.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.text.setOpenExternalLinks(True)

        self.layout.addWidget(self.text)
        self.setLayout(self.layout)


class WhonixSetupWizard(QtWidgets.QWizard):
    def __init__(self):
        super(WhonixSetupWizard, self).__init__()

        translation = _translations(Common.translations_path, 'whonixsetup')
        self._ = translation.gettext

        self.steps = Common.wizard_steps
        self.env = Common.environment

        for step in self.steps:
            if step == 'first_use_notice':
                self.first_use_notice = FirstUseNotice()
                self.addPage(self.first_use_notice)
            elif step == 'locale_settings':
                self.locale_settings = LocaleSettings()
                self.addPage(self.locale_settings)
            elif step == 'locale_settings_finish':
                self.locale_settings_finish = LocaleSettingsFinish()
                self.addPage(self.locale_settings_finish)

        self.setupUi()

    def setupUi(self):
        self.setWindowIcon(QtGui.QIcon("/usr/share/icons/anon-icon-pack/whonix.ico"))
        self.setWindowTitle('Whonix Setup Wizard')

        available_height = QtWidgets.QDesktopWidget().availableGeometry().height() - 60
        self.disclaimer_height = 750
        if available_height < self.disclaimer_height:
            self.disclaimer_height = available_height

        if Common.argument == 'setup':
            self.resize(760, self.disclaimer_height)
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
            if Common.first_use_notice:
                self.first_use_notice.text.setText(self._('first_use_notice'))
        except (yaml.scanner.ScannerError, yaml.parser.ParserError):
            pass

        self.button(QtWidgets.QWizard.CancelButton).setVisible(False)

        self.button(QtWidgets.QWizard.BackButton).clicked.connect(self.back_button_clicked)
        self.button(QtWidgets.QWizard.NextButton).clicked.connect(self.next_button_clicked)

        # Temporary workaround.
        # The pluggable transports are not implemented yet, but we want to
        # be able to display the tooltips for censored and firewall. For this,
        # the options must be enabled, but the slot will disable the Next
        # button if either is checked.
        if Common.argument == 'setup':
            if self.env == 'gateway':
                pass

        if not Common.argument == 'locale_settings':
            self.resize(580, 390)

        self.exec_()

    # called by button toggled signal.
    def set_next_button_state(self, state):
        if state:
            self.button(QtWidgets.QWizard.NextButton).setEnabled(False)
        else:
            self.button(QtWidgets.QWizard.NextButton).setEnabled(True)

    def center(self):
        """ After the window is resized, its origin point becomes the
        previous window top left corner.
        Re-center the window on the screen.
        """
        frame_gm = self.frameGeometry()
        center_point = QtWidgets.QDesktopWidget().availableGeometry().center()
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
                if (self.currentId() == self.steps.index('finish_page')):
                    self.resize(470, 310)
                    self.center()

            if self.env == 'gateway':
                # Set Next button state
                if self.currentId() == self.steps.index('connection_page'):
                    self.resize(580, 390)
                    self.center()

        if Common.argument == 'setup':
            if self.currentId() == self.steps.index('finish_page'):

                # for whonixcheck.
                Common.is_complete = True

                if self.env == 'workstation':
                    self.finish_page.icon.setPixmap(QtGui.QPixmap( \
                    '/usr/share/icons/oxygen/48x48/status/task-complete.png'))
                    self.finish_page.text.setText(self._('finish_page_ok'))

        if Common.argument == 'locale_settings':
            if self.currentId() == self.steps.index('locale_settings_finish'):

                if self.locale_settings.other_button.isChecked():
                    kcmshell = shutil.which("kcmshell4")

                    if self.locale_settings.lang_checkbox.isChecked():
                        command = command = '{} language'.format(kcmshell)
                        call(command, shell=True)

                    if self.locale_settings.kbd_checkbox.isChecked():
                        command = command = '%s kcm_keyboard' % (kcmshell)
                        call(command, shell=True)

                    self.button(QtWidgets.QWizard.BackButton).setEnabled(False)

                self.locale_settings_finish.text.setText(self._('locale_finish'))

    def back_button_clicked(self):
        Common.is_complete = False

def main():
    #import sys
    app = QtWidgets.QApplication(sys.argv)

    # locale settings are implemented for KDE desktop only.
    # skip if other desktop.
    if sys.argv[1] == 'locale_settings':
        kcmshell = shutil.which("kcmshell4")
        if kcmshell == None:
            print('kcmshell4 not found. Exiting')
            sys.exit()

    # root check.
    # locale_settings has to be run as user.
    if sys.argv[1] != 'locale_settings':
        if os.getuid() != 0:
            print('ERROR: This must be run as root!\nUse "kdesudo".')
            not_root = gui_message(Common.translations_path, 'not_root')
            sys.exit(1)

    # when there is no page need showing, we simply do not start GUI to
    # avoid an empty page
    if len(Common.wizard_steps) == 0:
       print('INFO: No page needs showing. Exiting.')
       sys.exit()

    wizard = WhonixSetupWizard()

    if Common.first_use_notice:
        f = open('/var/cache/whonix-setup-wizard/status-files/first_use_check.done', 'w')
        f.close()

    if not os.path.exists('/var/cache/whonix-setup-wizard/status-files/whonixsetup.done'):
        f = open('/var/cache/whonix-setup-wizard/status-files/whonixsetup.done', 'w')
        f.close()

    # run whonixcheck only when setup or repository option is selected.
    # note that the case for repository has been handled before.
    if Common.argument == 'setup':
        command = '/usr/lib/whonixsetup_/ft_m_end'
        call(command, shell=True)

    sys.exit()

if __name__ == "__main__":
    main()
