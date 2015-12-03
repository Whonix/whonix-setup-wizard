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

from stem.connection import connect

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

    is_complete = False
    disable_repo = False

    if not os.path.exists('/var/cache/whonix-setup-wizard/status-files'):
        os.mkdir('/var/cache/whonix-setup-wizard/status-files')

    run_whonixsetup = not os.path.exists('/var/cache/whonix-setup-wizard/status-files/whonixsetup.done')

    argument = parse_command_line_parameter()
    if argument == 'setup':
        wizard_steps = ['disclaimer_1',
                        'disclaimer_2',
                        'first_use_notice',
                        'whonix_repo_page',
                        'repository_wizard_page_1',
                        'repository_wizard_page_2',
                        'repository_wizard_finish',
                        'finish_page']

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
            return self.steps.index('first_use_notice')
        # Not understood
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

        if Common.argument == 'repository':
            self.repository_wizard_page_1 = RepositoryWizardPage1()
            self.addPage(self.repository_wizard_page_1)

            self.repository_wizard_page_2 = RepositoryWizardPage2()
            self.addPage(self.repository_wizard_page_2)

            self.repository_wizard_finish = RepositoryWizardfinish()
            self.addPage(self.repository_wizard_finish)

        if Common.argument == 'setup':
            if Common.run_whonixsetup:
                self.disclaimer_1 = DisclaimerPage1()
                self.addPage(self.disclaimer_1)

                self.disclaimer_2 = DisclaimerPage2()
                self.addPage(self.disclaimer_2)

                self.first_use_notice = FirstUseNotice()
                self.addPage(self.first_use_notice)

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

            else:
                self.finish_page = FinishPage()
                self.addPage(self.finish_page)

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

        if Common.argument == 'setup' and Common.run_whonixsetup:
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
            if Common.argument == 'setup':
                self.finish_page.icon.setPixmap(QtGui.QPixmap( \
                '/usr/share/icons/oxygen/48x48/status/task-complete.png'))
                self.finish_page.text.setText(self._('finish_page_ok'))
                Common.is_complete = True

                if Common.run_whonixsetup:
                    self.disclaimer_1.text.setText(self._('disclaimer_1'))
                    self.disclaimer_1.yes_button.setText(self._('accept'))
                    self.disclaimer_1.no_button.setText(self._('reject'))

                    self.disclaimer_2.text.setText(self._('disclaimer_2'))
                    self.disclaimer_2.yes_button.setText(self._('accept'))
                    self.disclaimer_2.no_button.setText(self._('reject'))

                    self.first_use_notice.text.setText(self._('first_use_notice'))

                    self.repository_wizard_page_1.text.setText(self._('repo_page_1'))
                    self.repository_wizard_page_1.enable_repo.setText(self._('repo_enable'))
                    self.repository_wizard_page_1.disable_repo.setText(self._('repo_disable'))
                    self.repository_wizard_page_2.text.setText(self._('repo_page_2'))

            elif Common.argument == 'repository':
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

        self.exec_()

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
            #if self.env == 'workstation':
            if self.currentId() == self.steps.index('first_use_notice'):
                self.resize(580, 430)
                self.center()

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

        if Common.argument == 'setup':
            if self.currentId() == self.steps.index('disclaimer_2'):
                # Back to disclaimer size.
                self.resize(760, self.disclaimer_height)
                self.center()


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
    if sys.argv[1] != 'locale_settings':
        if os.getuid() != 0:
            print 'ERROR: This must be run as root!\nUse "kdesudo".'
            not_root = gui_message(Common.translations_path, 'not_root')
            sys.exit(1)

    wizard = WhonixSetupWizard()

    if Common.run_whonixsetup:
        f = open('/var/cache/whonix-setup-wizard/status-files/whonixsetup.done', 'w')
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
