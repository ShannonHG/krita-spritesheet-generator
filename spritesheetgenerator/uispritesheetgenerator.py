import krita
import os
from pathlib import Path
from .spritesheetgenerator import SpritesheetGenerator
from PyQt5.QtCore import Qt, QSettings, QUuid
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import (QDialog, QLineEdit, QCheckBox,
                             QPushButton, QVBoxLayout, QHBoxLayout,
                             QLabel, QDialogButtonBox, QFormLayout,
                             QSpinBox, QComboBox, QGroupBox,
                             QFrame, QFileDialog, QWidget, QListWidget, QListWidgetItem)

class UISpritesheetGenerator(object):

    SETTINGS_PREV_OUTPUT_PATH_KEY = "prevOutputPath"

    def __init__(self):
        self.krita = krita.Krita.instance()
        self.activeDocument = self.krita.activeDocument()
        self.spritesheetGenerator = SpritesheetGenerator()
        self.settingsStorage = QSettings("krita-spritesheet-generator", "krita-spritesheet-generator")

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

        # Constant values for spritesheet layout fields
        spriteCustomLayoutFieldWidth = 170
        spriteCustomLayoutFieldMaxValue = 20

        # Constant values for sprite sizing fields
        spritePropertiesFieldWidth = 170
        spritePropertiesMaxValue = 9999

        # UI for selecting the spritesheet type
        self.spritesheetLayoutComboBox = QComboBox()
        self.spritesheetLayoutComboBox.setToolTip("<b>Rows:</b> Consecutive sprites will be placed in the same row. Once the row is full, the process will be repeated for the following rows.<br><br>" + 
                                                  "<b>Columns:</b> Consecutive sprites will be placed in the same column. Once the column is full, the process will be repeated for the following columns.<br><br>" +
                                                  "<b>Horizontal Strip:</b> Sprites will be organized into a single horizontal line.<br><br>"+
                                                  "<b>Vertical Strip:</b> Sprites will be organized into a single vertical line.")
        self.spritesheetLayoutComboBox.setMaximumWidth(spritePropertiesFieldWidth)
        self.spritesheetLayoutComboBox.addItem("Rows")
        self.spritesheetLayoutComboBox.addItem("Columns")
        self.spritesheetLayoutComboBox.addItem("Horizontal Strip")
        self.spritesheetLayoutComboBox.addItem("Vertical Strip")
        self.spritesheetLayoutComboBox.currentIndexChanged.connect(self._onLayoutTypeChanged)
        self.spritesheetLayoutFormLayout = QFormLayout()

        self.spritesheetCustomLayoutPropertiesLayoutWidget = QWidget()
        self.spritesheetCustomLayoutPropertiesLayout = QFormLayout(self.spritesheetCustomLayoutPropertiesLayoutWidget)

        # Toggle to automatically calculate the dimensions of the spritesheet
        self.autoCalculateSize = QCheckBox("Auto calculate size")
        self.autoCalculateSize.setToolTip("If enabled, will automatically determine the number of rows and columns needed in the spritesheet. Otherwise, rows and columns can be manually defined.")
        self.autoCalculateSize.setChecked(True)
        self.autoCalculateSize.stateChanged.connect(self._onAutoCalculateSizeChanged)

        # Widget for controlling the number of rows when in Custom layout mode
        self.spritesheetRowCountField = QSpinBox()
        self.spritesheetRowCountField.setToolTip("The number of rows in the spritesheet.")
        self.spritesheetRowCountField.setMinimum(1)
        self.spritesheetRowCountField.setMaximum(spriteCustomLayoutFieldMaxValue)
        self.spritesheetRowCountField.setMaximumWidth(spriteCustomLayoutFieldWidth)
        self.spritesheetRowCountField.setAlignment(Qt.AlignRight)

        # Widget for controlling the number of columns when in Custom layout mode
        self.spritesheetColumnCountField = QSpinBox()
        self.spritesheetColumnCountField.setToolTip("The number of columns in the spritesheet.")
        self.spritesheetColumnCountField.setMinimum(1)
        self.spritesheetColumnCountField.setMaximum(spriteCustomLayoutFieldMaxValue)
        self.spritesheetColumnCountField.setMaximumWidth(spriteCustomLayoutFieldWidth)
        self.spritesheetColumnCountField.setAlignment(Qt.AlignRight)

        self._onAutoCalculateSizeChanged()

        # Containers for the sprite properties UI
        self.spritePropertiesContainer = QGroupBox("Sprite properties")
        self.spritePropertiesLayout = QFormLayout(self.spritePropertiesContainer)

        # Widget for controlling the padding around sprites
        self.spritePaddingField = QSpinBox()
        self.spritePaddingField.setToolTip("The size of the transparent border added to sprites in the spritesheet. Useful to avoid sprites bleeding into each other.")
        self.spritePaddingField.setMaximum(spritePropertiesMaxValue)
        self.spritePaddingField.setMaximumWidth(spritePropertiesFieldWidth)
        self.spritePaddingField.setAlignment(Qt.AlignRight)

        # Widget for controlling the width of sprites
        self.spriteWidthField = QSpinBox()
        self.spriteWidthField.setToolTip("The desired width of each individual sprite in the spritesheet.")
        self.spriteWidthField.setMaximum(spritePropertiesMaxValue)
        self.spriteWidthField.setMaximumWidth(spritePropertiesFieldWidth)
        self.spriteWidthField.setAlignment(Qt.AlignRight)

        # Widget for controlling the height of sprites
        self.spriteHeightField = QSpinBox()
        self.spriteHeightField.setToolTip("The desired height of each individual sprite in the spritesheet.")
        self.spriteHeightField.setMaximum(spritePropertiesMaxValue)
        self.spriteHeightField.setMaximumWidth(spritePropertiesFieldWidth)
        self.spriteHeightField.setAlignment(Qt.AlignRight)

        if self.activeDocument != None:
            self.spriteWidthField.setValue(self.activeDocument.width())
            self.spriteHeightField.setValue(self.activeDocument.height())
        
        # Widget for controlling the filter method used to resize sprites
        self.filterStrategyComboBox = QComboBox()
        self.filterStrategyComboBox.setToolTip("The algorithm that will be used to resize the sprites (if needed).")
        self.filterStrategyComboBox.setMaximumWidth(spritePropertiesFieldWidth)
        self.filterStrategyComboBox.addItem("Auto")
        self.filterStrategyComboBox.addItems(self.krita.filterStrategies())

        self.layersToExportLabel = QLabel("Layers to export:")
        self.layersToExportLabel.setToolTip("Control which layers will be considered for inclusion in the spritesheet. Hidden layers are not listed.")
        self.layersToExportListWidget = QListWidget()
        if self.activeDocument != None:
            for layer in self.activeDocument.topLevelNodes():
                # Ignore hidden layers since they will be excluded anyway
                if not layer.visible():
                    continue

                item = QListWidgetItem(layer.name())
                item.setIcon(QIcon(QPixmap.fromImage(layer.thumbnail(64, 64))))

                # Store the ID of the layer as metadata in the item
                # so that it can be used later when applying layer exclusions.
                item.setData(Qt.UserRole, layer.uniqueId().toString(QUuid.WithoutBraces))

                item.setCheckState(Qt.Checked)
                self.layersToExportListWidget.insertItem(0, item)
        
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
        if not self.activeDocument or not self.activeDocument.fileName():
            homeDirectory = Path.home()
        else:
            homeDirectory = Path(self.activeDocument.fileName()).parents[0]

        # Attempt to retrieve the saved file path
        savedPath = self.settingsStorage.value(UISpritesheetGenerator.SETTINGS_PREV_OUTPUT_PATH_KEY, None)
        targetFilePath = None

        if savedPath == None:
            targetFilePath = homeDirectory
        else:
            targetFilePath = Path(savedPath)

        if targetFilePath.is_dir():
            targetFilePath = targetFilePath.joinpath("Spritesheet.png")

        self.filePathField.setText(str(targetFilePath))

        # Add file path widgets
        self.filePathLayout.addWidget(self.filePathLabel)
        self.filePathLayout.addWidget(self.filePathField)
        self.filePathLayout.addWidget(self.filePathBrowseButton)
        self.mainLayout.addLayout(self.filePathLayout)

         # Add the widget for selecting the spritesheet type
        self.spritesheetLayoutFormLayout.addRow("Spritesheet layout:", self.spritesheetLayoutComboBox)

        # Add widget for automatically calculating spritesheet size
        self.spritesheetLayoutFormLayout.addRow(self.autoCalculateSize)
       
        # Add widgets for the manually definining spritesheet dimensions
        self.spritesheetCustomLayoutPropertiesLayout.addRow("Rows:", self.spritesheetRowCountField)
        self.spritesheetCustomLayoutPropertiesLayout.addRow("Columns:", self.spritesheetColumnCountField)

        self.spritesheetLayoutFormLayout.addRow(self.spritesheetCustomLayoutPropertiesLayoutWidget)
        self.mainLayout.addLayout(self.spritesheetLayoutFormLayout)

        # Add a divider
        divider = QFrame()
        divider.setFrameStyle(QFrame.HLine | QFrame.Sunken)
        divider.setLineWidth(1)
        self.mainLayout.addWidget(divider)

        # Add sprite properties widgets
        self.spritePropertiesLayout.addRow("Width (px):", self.spriteWidthField)
        self.spritePropertiesLayout.addRow("Height (px):", self.spriteHeightField)
        self.spritePropertiesLayout.addRow("Filter:", self.filterStrategyComboBox)
        self.spritePropertiesLayout.addRow("Padding (px):", self.spritePaddingField)
        self.mainLayout.addWidget(self.spritePropertiesContainer)

        # Add the toggle for including/excluding empty frames
        self.mainLayout.addWidget(self.ignoreEmptyFramesCheckBox)

        self.mainLayout.addWidget(divider)
        self.mainLayout.addWidget(self.layersToExportLabel)
        self.mainLayout.addWidget(self.layersToExportListWidget)

        # Add the "OK" and "Cancel" buttons
        self.mainLayout.addWidget(self.dialogButtonBox)
        
        if self.activeDocument == None:
            self.mainDialog.setEnabled(False)

        # Show the dialog
        self.mainDialog.exec()

    def _onConfirmButtonPressed(self):
        self.mainDialog.setEnabled(False)

        outputPath = Path(self.filePathField.text())

        if outputPath.is_dir():
            # Save the directory so it can be auto-filled the next time the UI is opened.
            self.settingsStorage.setValue(UISpritesheetGenerator.SETTINGS_PREV_OUTPUT_PATH_KEY, os.path.normpath(str(outputPath)))

            # If the path is a directory, then append a very specific file name to avoid
            # accidentally overwriting any of the user's existing files.
            outputPath = outputPath.joinpath("krita-spritesheet-generator.png")
        else:
            if outputPath.suffix != ".png":
                # Ensure the spritesheet is being exported as a PNG
                outputPath = outputPath.with_suffix(".png")

            # Save the file path so it can be auto-filled the next time the UI is opened.
            self.settingsStorage.setValue(UISpritesheetGenerator.SETTINGS_PREV_OUTPUT_PATH_KEY, os.path.normpath(str(outputPath)))

        self.settingsStorage.sync()

        # Gather layers to be excluded from the spritesheet
        layerExclusions = []
        for row in range(self.layersToExportListWidget.count()):
            item = self.layersToExportListWidget.item(row)

            if item.checkState() == Qt.Unchecked:
                layerExclusions.append(item.data(Qt.UserRole))

        self.spritesheetGenerator.configure(
            str(outputPath),
            self.spritesheetLayoutComboBox.currentText(),
            self.autoCalculateSize.isChecked() or self.autoCalculateSize.isHidden(),
            self.spritesheetRowCountField.value(),
            self.spritesheetColumnCountField.value(),
            self.ignoreEmptyFramesCheckBox.isChecked(),
            self.spriteWidthField.value(),
            self.spriteHeightField.value(),
            self.spritePaddingField.value(),
            self.filterStrategyComboBox.currentText(),
            layerExclusions)
        
        self.spritesheetGenerator.export()
        self.mainDialog.close()

    def _onCancelButtonPressed(self):
        self.mainDialog.close()

    def _onBrowseButtonPressed(self):
        fileDialog = QFileDialog()
        fileDialog.setWindowTitle("Exporting Spritesheet")
        fileDialog.setNameFilter("PNG image (*.png)")

        savedPath = self.settingsStorage.value(UISpritesheetGenerator.SETTINGS_PREV_OUTPUT_PATH_KEY)

        if savedPath != None:
            path = Path(savedPath)
            fileDialog.setDirectory(str(path) if path.is_dir() else str(path.parents[0]))

        if fileDialog.exec():
            fileNames = fileDialog.selectedFiles()
            self.filePathField.setText(fileNames[0])

    def _onLayoutTypeChanged(self):
        layoutType = self.spritesheetLayoutComboBox.currentText()

        # Only display the "Auto calculate size" widget when the layout type is "Rows" or "Columns"
        if layoutType == "Rows" or layoutType == "Columns":
            self.autoCalculateSize.show()
        else:
            self.autoCalculateSize.hide()

    def _onAutoCalculateSizeChanged(self):
        if self.autoCalculateSize.isChecked():
            # Hide widgets for manually setting spritesheet dimensions
            self.spritesheetCustomLayoutPropertiesLayoutWidget.hide()
        else:
            # Show widgets for manually setting spritesheet dimensions
            self.spritesheetCustomLayoutPropertiesLayoutWidget.show()