# Form implementation generated from reading ui file 'ui/ImportPleco.ui'
#
# Created by: PyQt6 UI code generator 6.8.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.setEnabled(True)
        Dialog.resize(447, 377)
        self.gridLayout_2 = QtWidgets.QGridLayout(Dialog)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.layout_options = QtWidgets.QGridLayout()
        self.layout_options.setObjectName("layout_options")
        self.label_deck = QtWidgets.QLabel(parent=Dialog)
        self.label_deck.setObjectName("label_deck")
        self.layout_options.addWidget(self.label_deck, 1, 0, 1, 1)
        self.button_file = QtWidgets.QToolButton(parent=Dialog)
        self.button_file.setObjectName("button_file")
        self.layout_options.addWidget(self.button_file, 0, 2, 1, 1)
        self.label_file = QtWidgets.QLabel(parent=Dialog)
        self.label_file.setObjectName("label_file")
        self.layout_options.addWidget(self.label_file, 0, 0, 1, 1)
        self.select_deck = QtWidgets.QComboBox(parent=Dialog)
        self.select_deck.setEditable(True)
        self.select_deck.setObjectName("select_deck")
        self.layout_options.addWidget(self.select_deck, 1, 1, 1, 2)
        self.line_file = QtWidgets.QLineEdit(parent=Dialog)
        self.line_file.setDragEnabled(False)
        self.line_file.setReadOnly(False)
        self.line_file.setClearButtonEnabled(False)
        self.line_file.setObjectName("line_file")
        self.layout_options.addWidget(self.line_file, 0, 1, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.layout_options.addItem(spacerItem, 2, 1, 1, 1)
        self.gridLayout_2.addLayout(self.layout_options, 0, 0, 1, 1)
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.checkbox_new = QtWidgets.QCheckBox(parent=Dialog)
        self.checkbox_new.setEnabled(True)
        self.checkbox_new.setLayoutDirection(QtCore.Qt.LayoutDirection.LeftToRight)
        self.checkbox_new.setChecked(False)
        self.checkbox_new.setObjectName("checkbox_new")
        self.gridLayout.addWidget(self.checkbox_new, 0, 0, 1, 1)
        self.layout_button = QtWidgets.QGridLayout()
        self.layout_button.setObjectName("layout_button")
        self.button_cancel = QtWidgets.QPushButton(parent=Dialog)
        self.button_cancel.setObjectName("button_cancel")
        self.layout_button.addWidget(self.button_cancel, 0, 0, 1, 1)
        self.button_import = QtWidgets.QPushButton(parent=Dialog)
        self.button_import.setCheckable(False)
        self.button_import.setDefault(True)
        self.button_import.setObjectName("button_import")
        self.layout_button.addWidget(self.button_import, 0, 1, 1, 1)
        self.gridLayout.addLayout(self.layout_button, 0, 2, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.gridLayout.addItem(spacerItem1, 0, 1, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 1, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)
        Dialog.setTabOrder(self.line_file, self.button_file)
        Dialog.setTabOrder(self.button_file, self.select_deck)
        Dialog.setTabOrder(self.select_deck, self.checkbox_new)
        Dialog.setTabOrder(self.checkbox_new, self.button_cancel)
        Dialog.setTabOrder(self.button_cancel, self.button_import)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.label_deck.setText(_translate("Dialog", "Import to Deck:"))
        self.button_file.setText(_translate("Dialog", "..."))
        self.label_file.setText(_translate("Dialog", "Pleco File:"))
        self.checkbox_new.setText(_translate("Dialog", "Set duplicates to new"))
        self.button_cancel.setText(_translate("Dialog", "Cancel"))
        self.button_import.setText(_translate("Dialog", "Import"))
