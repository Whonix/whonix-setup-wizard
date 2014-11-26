#!/usr/bin/python

from PyQt4 import QtCore, QtGui
from subprocess import call
import os
import yaml
from guimessages.translations import _translations
from guimessages.guimessage import gui_message


class common:
    tr_path ='/usr/lib/python2.7/dist-packages/whonixsetup/whonix_setup.yaml'

    disclaimer_1 = 0
    disclaimer_2 = 1
    whonix_repo_page = 2
    finish_page = 3

    one_shot = True
    is_complete = False
    run_repo = False


class disclaimer_page_1(QtGui.QWizardPage):
    def __init__(self):
        super(disclaimer_page_1, self).__init__()
        self.text = QtGui.QTextBrowser(self)
        self.accept_group = QtGui.QGroupBox(self)
        self.yes_button = QtGui.QRadioButton(self.accept_group)
        self.no_button = QtGui.QRadioButton(self.accept_group)
        self.layout = QtGui.QVBoxLayout()
        self.setupUi()

    def setupUi(self):
        self.text.setLineWidth(-1)
        self.text.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)

        self.accept_group.setMinimumSize(0, 60)
        self.yes_button.setGeometry(QtCore.QRect(30, 10, 300, 21))
        self.no_button.setGeometry(QtCore.QRect(30, 30, 300, 21))
        self.no_button.setChecked(True)

        self.layout.addWidget(self.text)
        self.layout.addWidget(self.accept_group)
        self.setLayout(self.layout)

    def nextId(self):
        if self.yes_button.isChecked():
            return common.disclaimer_2
        elif self.no_button.isChecked():
            return common.finish_page


class disclaimer_page_2(QtGui.QWizardPage):
    def __init__(self):
        super(disclaimer_page_2, self).__init__()
        self.text = QtGui.QTextBrowser(self)
        self.accept_group = QtGui.QGroupBox(self)
        self.yes_button = QtGui.QRadioButton(self.accept_group)
        self.no_button = QtGui.QRadioButton(self.accept_group)
        self.layout = QtGui.QVBoxLayout()
        self.setupUi()

    def setupUi(self):
        self.Enabled = False
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
            if not os.path.exists('/var/lib/whonix/do_once/whonixsetup.done'):
                return common.whonix_repo_page
            else:
                return common.finish_page
        elif self.no_button.isChecked():
            return common.finish_page


class whonix_repository_page(QtGui.QWizardPage):
    def __init__(self):
        super(whonix_repository_page, self).__init__()
        self.text = QtGui.QTextBrowser(self)
        self.layout = QtGui.QGridLayout()
        self.setupUi()

    def setupUi(self):
        self.text.setFrameShape(QtGui.QFrame.NoFrame)
        self.Enabled = False
        self.text.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)

        self.layout.addWidget(self.text)
        self.setLayout(self.layout)

    def nextId(self):
        if common.one_shot:
            common.one_shot = False
            common.run_repo = True
        return common.finish_page


class finish_page(QtGui.QWizardPage):
    def __init__(self):
        super(finish_page, self).__init__()
        self.text = QtGui.QTextBrowser(self)
        self.layout = QtGui.QGridLayout()
        self.setupUi()

    def setupUi(self):
        self.text.setFrameShape(QtGui.QFrame.NoFrame)
        self.Enabled = False
        self.text.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)

        self.layout.addWidget(self.text)
        self.setLayout(self.layout)


class whonix_setup_wizard(QtGui.QWizard):
    def __init__(self):
        super(whonix_setup_wizard, self).__init__()

        translation = _translations(common.tr_path, 'whonixsetup')
        self._ = translation.gettext

        self.setWindowTitle('Whonix Setup Wizard')
        self.resize(760, 750)

        # When run as root, Qt is not granted access to all its Qt4 functionalities (seemingly).
        # Set a transparent (default dialog) background for the widget.
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

        self.disclaimer_1 = disclaimer_page_1()
        self.addPage(self.disclaimer_1)

        self.disclaimer_2 = disclaimer_page_2()
        self.addPage(self.disclaimer_2)

        self.whonix_repo_page = whonix_repository_page()
        self.addPage(self.whonix_repo_page)

        self.finish_page = finish_page()
        self.addPage(self.finish_page)

        self.setupUi()


    def setupUi(self):
        try:
            self.disclaimer_1.text.setText(self._('disclaimer1'))
            self.disclaimer_1.yes_button.setText(self._('accept'))
            self.disclaimer_1.no_button.setText(self._('reject'))

            self.disclaimer_2.text.setText(self._('disclaimer2'))
            self.disclaimer_2.yes_button.setText(self._('accept'))
            self.disclaimer_2.no_button.setText(self._('reject'))

            self.whonix_repo_page.text.setText(self._('whonix_repository_page'))

            self.finish_page.text.setText(self._('finish_page'))

        except (yaml.scanner.ScannerError, yaml.parser.ParserError):
            pass

        self.button(QtGui.QWizard.CancelButton).setVisible(False)

        self.button(QtGui.QWizard.BackButton).clicked.connect(self.BackButton_clicked)
        self.button(QtGui.QWizard.NextButton).clicked.connect(self.NextButton_clicked)

        self.exec_()


    def center(self):
        frame_gm = self.frameGeometry()
        center_point = QtGui.QDesktopWidget().availableGeometry().center()
        frame_gm.moveCenter(center_point)
        self.move(frame_gm.topLeft())


    def NextButton_clicked(self):
        if self.currentId() == common.finish_page:
            common.is_complete = True
            if common.run_repo:
                common.run_repo = False
                command = 'whonix-repository-wizard &'
                call(command, shell=True)
                command = 'mkdir -p /var/lib/whonix/do_once'
                call(command, shell=True)
                whonixsetup_done = open('/var/lib/whonix/do_once/whonixsetup.done', 'w')
                whonixsetup_done.write('')
                whonixsetup_done.close()
            # Disclaimer page 1 not undesrstood -> leave
            if self.disclaimer_1.no_button.isChecked():
                self.hide()
                command = '/sbin/poweroff'
                call(command, shell=True)
            # Disclaimer page 2 not undesrstood -> leave
            if self.disclaimer_2.no_button.isChecked():
                self.hide()
                command = '/sbin/poweroff'
                call(command, shell=True)

        if self.currentId() == common.whonix_repo_page or \
           self.currentId() == common.finish_page:
            self.resize(450, 250)
            self.center()


    def BackButton_clicked(self):
        common.is_complete = False
        if not common.one_shot:
            # re-arm command
            common.one_shot = True

        if self.currentId() == common.disclaimer_2:
            self.resize(760, 750)
            self.center()


def main():
    import sys
    app = QtGui.QApplication(sys.argv)

    # root check.
    if os.getuid() != 0:
        print 'ERROR: This must be run as root!\nUse "kdesudo".'
        not_root = gui_message(common.tr_path, 'not_root')
        sys.exit(1)

    wizard = whonix_setup_wizard()

    # run whonixcheck
    if common.is_complete:
        command = '/usr/lib/whonixsetup_/ft_m_end'
        call(command, shell=True)

    sys.exit()

if __name__ == "__main__":
    main()
