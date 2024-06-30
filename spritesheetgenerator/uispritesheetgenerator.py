import krita
from pathlib import Path

from .spritesheetgenerator import SpritesheetGenerator
from PyQt5.QtCore import (Qt)
from PyQt5.QtWidgets import (QDialog, QLineEdit, QCheckBox,
                             QPushButton, QVBoxLayout, QHBoxLayout,
                             QLabel, QDialogButtonBox, QFormLayout,
                             QSpinBox, QComboBox, QGroupBox,
                             QFrame, QFileDialog)

class UISpritesheetGenerator(object):

    def __init__(self):
        self.krita = krita.Krita.instance()
        self.activeDocument = self.krita.activeDocument()
        self.spritesheetGenerator = SpritesheetGenerator()

        # The primary dialog and vertical layout
        self.mainDialog = QDialog()
        self.mainDialog.setWindowTitle("Spritesheet Generator - Krita")
        self.mainDialog.resize(520, 300)
        self.mainLayout = QVBoxLayout(self.mainDialog)

        # File path selection UI
        self.filePathLayout = QHBoxLayout()
        self.filePathLabel = QLabel("File path:")
        self.filePathField = QLineEdit()
        self.filePathField.setToolTip("The file path that the spritesheet will be exported to.")
        self.filePathBrowseButton = QPushButton("Browse")
        self.filePathBrowseButton.setToolTip("Opens this computer's native file browser to select the spritesheet's file path.")
        self.filePathBrowseButton.clicked.connect(self._onBrowseButtonPressed)

        # Constant values for sprite sizing fields
        spriteDimensionsFieldWidth = 170
        spriteDimensionsMaxValue = 9999

        # UI for selecting the spritesheet type
        self.spritesheetLayoutComboBox = QComboBox()
        self.spritesheetLayoutComboBox.setToolTip("<b>Rows:</b> Consecutive sprites will be placed in the same row. Once the row is full, the process will be repeated for the following rows.<br><br>" + 
                                                  "<b>Columns:</b> Consecutive sprites will be placed in the same column. Once the column is full, the process will be repeated for the following columns.<br><br>" +
                                                  "<b>Horizontal Strip:</b> Sprites will be organized into a single horizontal line.<br><br>"+
                                                  "<b>Vertical Strip:</b> Sprites will be organized into a single vertical line.")
        self.spritesheetLayoutComboBox.setMaximumWidth(spriteDimensionsFieldWidth)
        self.spritesheetLayoutComboBox.addItem("Rows")
        self.spritesheetLayoutComboBox.addItem("Columns")
        self.spritesheetLayoutComboBox.addItem("Horizontal Strip")
        self.spritesheetLayoutComboBox.addItem("Vertical Strip")
        self.spritesheetLayoutFormLayout = QFormLayout()

        # Containers for the sprite dimensions UI
        self.spriteDimensionsContainer = QGroupBox("Sprite dimensions")
        self.spriteDimensionsLayout = QFormLayout(self.spriteDimensionsContainer)

        # Widget for controlling the width of sprites
        self.spriteWidthField = QSpinBox()
        self.spriteWidthField.setToolTip("The desired width of each individual sprite in the spritesheet.")
        self.spriteWidthField.setMaximum(spriteDimensionsMaxValue)
        self.spriteWidthField.setMaximumWidth(spriteDimensionsFieldWidth)
        self.spriteWidthField.setAlignment(Qt.AlignRight)

        # Widget for controlling the height of sprites
        self.spriteHeightField = QSpinBox()
        self.spriteHeightField.setToolTip("The desired height of each individual sprite in the spritesheet.")
        self.spriteHeightField.setMaximum(spriteDimensionsMaxValue)
        self.spriteHeightField.setMaximumWidth(spriteDimensionsFieldWidth)
        self.spriteHeightField.setAlignment(Qt.AlignRight)

        if self.activeDocument != None:
            self.spriteWidthField.setValue(self.activeDocument.width())
            self.spriteHeightField.setValue(self.activeDocument.height())
        
        # Widget for controlling the filter method used to resize sprites
        self.filterStrategyComboBox = QComboBox()
        self.filterStrategyComboBox.setToolTip("The algorithm that will be used to resize the sprites (if needed).")
        self.filterStrategyComboBox.setMaximumWidth(spriteDimensionsFieldWidth)
        self.filterStrategyComboBox.addItem("Auto")
        self.filterStrategyComboBox.addItems(self.krita.filterStrategies())
        
        # Toggle to include/exclude empty frames
        self.ignoreEmptyFramesCheckBox = QCheckBox("Ignore empty frames")
        self.ignoreEmptyFramesCheckBox.setToolTip("If enabled, empty frames in the animation timeline will not be included in the spritesheet.")
        self.ignoreEmptyFramesCheckBox.setChecked(True)

        # "OK" and "Cancel" buttons
        self.dialogButtonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.dialogButtonBox.accepted.connect(self._onConfirmButtonPressed)
        self.dialogButtonBox.rejected.connect(self._onCancelButtonPressed)
        
    def show(self):
        # By default try to use the current document's file path
        # to determine the export directory of the spritesheet.
        # If the document doesn't have a file path set then
        # the user's home directory will be used. 
        targetDirectory = None
        if self.activeDocument != None and self.activeDocument.fileName() != None:
            targetDirectory = Path(self.activeDocument.fileName()).parents[0]
        else:
            targetDirectory = Path.home()

        # Set the file name to "spritesheet.png" by default
        self.filePathField.setText(str(targetDirectory.joinpath("Spritesheet.png")))

        # Add file path widgets
        self.filePathLayout.addWidget(self.filePathLabel)
        self.filePathLayout.addWidget(self.filePathField)
        self.filePathLayout.addWidget(self.filePathBrowseButton)
        self.mainLayout.addLayout(self.filePathLayout)

         # Add the widget for selecting the spritesheet type
        self.spritesheetLayoutFormLayout.addRow("Spritesheet layout:", self.spritesheetLayoutComboBox)
        self.mainLayout.addLayout(self.spritesheetLayoutFormLayout)

        # Add a divider
        divider = QFrame()
        divider.setFrameStyle(QFrame.HLine | QFrame.Sunken)
        divider.setLineWidth(1)
        self.mainLayout.addWidget(divider)

        # Add sprite dimensions widgets
        self.spriteDimensionsLayout.addRow("Width (px):", self.spriteWidthField)
        self.spriteDimensionsLayout.addRow("Height (px):", self.spriteHeightField)
        self.spriteDimensionsLayout.addRow("Filter:", self.filterStrategyComboBox)
        self.mainLayout.addWidget(self.spriteDimensionsContainer)

        # Add the toggle for including/excluding empty frames
        self.mainLayout.addWidget(self.ignoreEmptyFramesCheckBox)

        # Add the "OK" and "Cancel" buttons
        self.mainLayout.addWidget(self.dialogButtonBox)
        
        if self.activeDocument == None:
            self.mainDialog.setEnabled(False)

        # Show the dialog
        self.mainDialog.exec()

    def _onConfirmButtonPressed(self):
        self.mainDialog.setEnabled(False)

        self.spritesheetGenerator.configure(
            self.filePathField.text(),
            self.spritesheetLayoutComboBox.currentText(),
            self.ignoreEmptyFramesCheckBox.isChecked(),
            self.spriteWidthField.value(),
            self.spriteHeightField.value(),
            self.filterStrategyComboBox.currentText())
        
        self.spritesheetGenerator.export()
        self.mainDialog.close()

    def _onCancelButtonPressed(self):
        self.mainDialog.close()

    def _onBrowseButtonPressed(self):
        fileDialog = QFileDialog()
        fileDialog.setWindowTitle("Exporting Spritesheet")
        fileDialog.setNameFilter("Images (*.png)")
        
        if fileDialog.exec():
            fileNames = fileDialog.selectedFiles()
            self.filePathField.setText(fileNames[0])