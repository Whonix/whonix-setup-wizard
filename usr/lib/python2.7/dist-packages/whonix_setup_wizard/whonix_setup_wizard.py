
#!/usr/bin/python

""" WHONIX SETUP WIZARD """

from PyQt4 import QtCore, QtGui
from subprocess import call
import os
import yaml
from guimessages.translations import _translations
from guimessages.guimessage import gui_message


class common():
    tr_path ='/usr/lib/python2.7/dist-packages/whonix_setup_wizard/whonix_setup.yaml'

    is_complete = False
    run_repo = False

    if os.path.exists('/usr/share/anon-gw-base-files'):
        environment = 'gateway'
        wizard_steps = ['disclaimer_1',
                        'disclaimer_2',
                        'connection_page',
                        'tor_connected_page',
                        'whonix_repo_page',
                        'finish_page']

    elif os.path.exists('/usr/share/anon-ws-base-files'):
        environment = 'workstation'
        wizard_steps = ['disclaimer_1',
                        'disclaimer_2',
                        'whonix_repo_page',
                        'finish_page']


class disclaimer_page_1(QtGui.QWizardPage):
    def __init__(self):
        super(disclaimer_page_1, self).__init__()

        self.common = common()
        self.steps = self.common.wizard_steps

        self.text = QtGui.QTextBrowser(self)
        self.accept_group = QtGui.QGroupBox(self)
        self.yes_button = QtGui.QRadioButton(self.accept_group)
        self.no_button = QtGui.QRadioButton(self.accept_group)

        self.layout = QtGui.QVBoxLayout()

        self.setupUi()

    def setupUi(self):
        self.text.setLineWidth(-1)
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


class disclaimer_page_2(QtGui.QWizardPage):
    def __init__(self):
        super(disclaimer_page_2, self).__init__()

        self.common = common()
        self.steps = self.common.wizard_steps
        self.env = self.common.environment

        self.text = QtGui.QTextBrowser(self)
        self.accept_group = QtGui.QGroupBox(self)
        self.yes_button = QtGui.QRadioButton(self.accept_group)
        self.no_button = QtGui.QRadioButton(self.accept_group)

        self.layout = QtGui.QVBoxLayout()

        self.setupUi()

    def setupUi(self):
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
                common.run_repo = True
                if self.env == 'gateway':
                    return self.steps.index('connection_page')
                elif self.env == 'workstation':
                # run whonix_repository_wizard
                    return self.steps.index('whonix_repo_page')
            else:
                if self.env == 'gateway':
                    return self.steps.index('connection_page')
                elif self.env == 'workstation':
                    return self.steps.index('finish_page')
        # Not understood 
        else:
            return self.steps.index('finish_page')


class connection_page(QtGui.QWizardPage):
    def __init__(self):
        super(connection_page, self).__init__()

        self.common = common()
        self.steps = self.common.wizard_steps
        self.env = self.common.environment

        self.text = QtGui.QTextBrowser(self)
        self.layout = QtGui.QGridLayout()

        self.connection_group = QtGui.QGroupBox(self)
        self.enable = QtGui.QRadioButton(self.connection_group)
        self.disable = QtGui.QRadioButton(self.connection_group)
        self.censored = QtGui.QRadioButton(self.connection_group)
        self.use_proxy = QtGui.QRadioButton(self.connection_group)

        self.layout = QtGui.QVBoxLayout()

        self.setupUi()

    def setupUi(self):
        self.text.setFrameShape(QtGui.QFrame.NoFrame)
        self.text.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)

        self.connection_group.setMinimumSize(0, 100)
        self.enable.setGeometry(QtCore.QRect(30, 10, 400, 21))
        self.disable.setGeometry(QtCore.QRect(30, 30, 400, 21))
        self.censored.setGeometry(QtCore.QRect(30, 50, 400, 21))
        self.use_proxy.setGeometry(QtCore.QRect(30, 70, 400, 21))
        self.enable.setChecked(True)

        self.layout.addWidget(self.text)
        self.layout.addWidget(self.connection_group)
        self.setLayout(self.layout)

    def nextId(self):
        return self.steps.index('tor_connected_page')


class tor_connected_page(QtGui.QWizardPage):
    def __init__(self):
        super(tor_connected_page, self).__init__()

        self.common = common()
        self.steps = self.common.wizard_steps

        self.text = QtGui.QTextBrowser(self)
        self.torrc = QtGui.QPlainTextEdit(self)

        self.layout = QtGui.QVBoxLayout()

        self.setupUi()

    def setupUi(self):
        self.text.setFrameShape(QtGui.QFrame.NoFrame)
        self.text.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.torrc.setMinimumSize(0, 175)
        
        self.torrc.setReadOnly(True)

        self.layout.addWidget(self.text)
        self.layout.addWidget(self.torrc)
        self.setLayout(self.layout)

    def nextId(self):
        if common.run_repo:
            return self.steps.index('whonix_repo_page')
        else:
            return self.steps.index('finish_page')


class whonix_repository_page(QtGui.QWizardPage):
    def __init__(self):
        super(whonix_repository_page, self).__init__()

        self.common = common()
        self.steps = self.common.wizard_steps

        self.text = QtGui.QTextBrowser(self)
        self.layout = QtGui.QGridLayout()
        self.setupUi()

    def setupUi(self):
        self.text.setFrameShape(QtGui.QFrame.NoFrame)
        self.text.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)

        self.layout.addWidget(self.text)
        self.setLayout(self.layout)

    def nextId(self):
        common.run_repo = True
        return self.steps.index('finish_page')


class finish_page(QtGui.QWizardPage):
    def __init__(self):
        super(finish_page, self).__init__()
        self.text = QtGui.QTextBrowser(self)

        self.layout = QtGui.QGridLayout()
        self.setupUi()

    def setupUi(self):
        self.text.setFrameShape(QtGui.QFrame.NoFrame)
        self.text.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)

        self.layout.addWidget(self.text)
        self.setLayout(self.layout)


class whonix_setup_wizard(QtGui.QWizard):
    def __init__(self):
        super(whonix_setup_wizard, self).__init__()

        self.common = common()
        self.steps = self.common.wizard_steps
        self.env = self.common.environment

        translation = _translations(common.tr_path, 'whonixsetup')
        self._ = translation.gettext

        self.setWindowIcon(QtGui.QIcon("/usr/share/icons/anon-icon-pack/whonix.ico"))
        self.setWindowTitle('Whonix Setup Wizard')
        self.resize(760, 750)

        # When run as root, Qt is not granted access to all its Qt4
        # functionalities (seemingly): the wizard background is white,
        # "old style" buttons...
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

        if self.env == 'gateway':
            self.connection_page = connection_page()
            self.addPage(self.connection_page)

            self.tor_connected_page = tor_connected_page()
            self.addPage(self.tor_connected_page)

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

            if self.env == 'gateway':
                self.connection_page.text.setText(self._('connection_text'))
                self.connection_page.enable.setText(self._('enable_tor'))
                self.connection_page.disable.setText(self._('disable_tor'))
                self.connection_page.censored.setText(self._('censored_tor'))
                self.connection_page.use_proxy.setText(self._('use_proxy'))

                self.tor_connected_page.text.setText(self._('tor_connected_1'))
                text = open('/etc/tor/torrc').read()
                self.tor_connected_page.torrc.setPlainText(text)

            self.whonix_repo_page.text.setText(self._('whonix_repository_page'))

            self.finish_page.text.setText(self._('finish_page'))

        except (yaml.scanner.ScannerError, yaml.parser.ParserError):
            pass

        self.setOption(QtGui.QWizard.HaveHelpButton, True)
        self.button(QtGui.QWizard.HelpButton).setVisible(False)
        self.button(QtGui.QWizard.CancelButton).setVisible(False)

        self.button(QtGui.QWizard.BackButton).clicked.connect(self.BackButton_clicked)
        self.button(QtGui.QWizard.NextButton).clicked.connect(self.NextButton_clicked)
        self.button(QtGui.QWizard.HelpButton).clicked.connect(self.HelpButton_clicked)

        self.exec_()

    def center(self):
        """ After the window is resized, its origin point becomes the
        previous window top left corner.
        Re-center the window on the scceen.
        """
        frame_gm = self.frameGeometry()
        center_point = QtGui.QDesktopWidget().availableGeometry().center()
        frame_gm.moveCenter(center_point)
        self.move(frame_gm.topLeft())

    def NextButton_clicked(self):
        """ Next button slot.
        The commands cannot be implemented in the wizard's nextId() function,
        as it is polled by the event handler on the creation of the page.
        Depending on the checkbox states, the commands would be run when the
        page is loaded.
        Those button_clicked functions are called once, when the user clicks
        the corresponding button.
        Options (like button states and window size changes) are set here.
        """
        if self.env == 'gateway':
            # help only on gateway wizard.
            if self.currentId() == self.steps.index('connection_page'):
                self.button(QtGui.QWizard.HelpButton).setVisible(True)
            if self.currentId() == self.steps.index('tor_connected_page'):
                self.button(QtGui.QWizard.HelpButton).setVisible(False)

        if self.currentId() == self.steps.index('whonix_repo_page'):
            self.button(QtGui.QWizard.HelpButton).setVisible(False)

        # A more "mormal" wizard size after the disclaimer pages.
        if (self.currentId() == self.steps.index('whonix_repo_page') or
            self.currentId() == self.steps.index('finish_page')):
                self.resize(450, 350)
                self.center()

        if (self.env == 'gateway' and
            self.currentId() == self.steps.index('connection_page')):
                self.resize(450, 355)
                self.center()

        if self.currentId() == self.steps.index('finish_page'):
            common.is_complete = True

            if common.run_repo:
                common.run_repo = False
                command = 'whonix-repository-wizard &'
                call(command, shell=True)
                # whonixsetup.done. Next time, do not run whonix repository
                command = 'mkdir -p /var/lib/whonix/do_once'
                call(command, shell=True)
                whonixsetup_done = open('/var/lib/whonix/do_once/whonixsetup.done', 'w')
                whonixsetup_done.write('')
                whonixsetup_done.close()
                #  Do not run whonix-repository-wizard twice.
                self.removePage(self.steps.index('whonix_repo_page'))
            self.button(QtGui.QWizard.HelpButton).setVisible(False)

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

    def BackButton_clicked(self):
        common.is_complete = False

        if (self.env == 'gateway' and
            self.currentId() == self.steps.index('connection_page')):
                self.button(QtGui.QWizard.HelpButton).setVisible(True)

        if self.currentId() == self.steps.index('disclaimer_2'):
            # Back to disclaimer size.
            self.resize(760, 750)
            self.center()
            self.button(QtGui.QWizard.HelpButton).setVisible(False)

    def HelpButton_clicked(self):
        if self.env == 'gateway':
            self.setEnabled(False)
            self.help1 = gui_message(common.tr_path, 'help1')
            self.setEnabled(True)


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
