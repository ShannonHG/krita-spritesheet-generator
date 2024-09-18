import krita
import math
from pathlib import Path
from collections import namedtuple

class SpritesheetGenerator():

    def __init__(self):
        pass

    def configure(self, exportFilePath, spritesheetType, ignoreEmptyFrames, targetSpriteWidth, targetSpriteHeight, spritePadding, filterStrategy):
        self.exportFilePath = exportFilePath
        self.spritesheetType = spritesheetType
        self.ignoreEmptyFrames = ignoreEmptyFrames
        self.targetSpriteWidth = targetSpriteWidth
        self.targetSpriteHeight = targetSpriteHeight
        self.spritePadding = spritePadding
        self.finalSpriteWidth = self.targetSpriteWidth + (self.spritePadding * 2)
        self.finalSpriteHeight = self.targetSpriteHeight + (self.spritePadding * 2)
        self.filterStrategy = filterStrategy
        self.krita = krita.Krita.instance()
        self.activeDocument = self.krita.activeDocument()
        self.animationStartTime = self.activeDocument.fullClipRangeStartTime()
        self.animationEndTime = self.activeDocument.fullClipRangeEndTime()

        print("Spritesheet generator configuration completed")
        print(f"Export file path: {self.exportFilePath}")
        print(f"Spritesheet type: {self.spritesheetType}")
        print(f"Ignore empty frames: {self.ignoreEmptyFrames}")
        print(f"Target width: {self.targetSpriteWidth}")
        print(f"Target height: {self.targetSpriteHeight}")
        print(f"Filter type: {self.filterStrategy}")
        print(f"Animation start time: {self.animationStartTime}")
        print(f"Animation end time: {self.animationEndTime}")

    def export(self):
        # Create a temporary duplicate of the currently active document.
        # All transformations (such as resizing) will be done on this temporary document.
        self._createTemporaryDocument()

        if self._isSpriteResizeRequired():
            print("Sprites will be resized...")
            self._resizeSprites()

        if self.spritePadding > 0:
            print("Adding padding to spritesheet frames...")
            self._applyPaddingToSprites()
        
        self._createSpritesheetDocumentFromFrames()
        self._positionFramesInSpritesheetDocument()
        self._forceCloseDocument(self.temporaryDocument)
        self._exportToFile()
        self._forceCloseDocument(self.spritesheetDocument)
        
    def _createTemporaryDocument(self):
        self.temporaryDocument = self.activeDocument.clone()
        self.temporaryDocument.setBatchmode(True)
        
        print("Temporary document created")

    def _isSpriteResizeRequired(self):
        return self.temporaryDocument.width() != self.targetSpriteWidth or self.temporaryDocument.height() != self.targetSpriteHeight
    
    def _resizeSprites(self):
        self.temporaryDocument.scaleImage(self.targetSpriteWidth, self.targetSpriteHeight, self.targetSpriteWidth, self.targetSpriteHeight, self.filterStrategy)
        self.temporaryDocument.refreshProjection()

        print(f"Sprites resized to {self.temporaryDocument.width()} x {self.temporaryDocument.height()}")

    def _applyPaddingToSprites(self):
        # Remove excess pixels that are beyond the bounds of the visible portion of the document.
        self.temporaryDocument.crop(0, 0, self.temporaryDocument.width(), self.temporaryDocument.height())

        # Adjust document offset and size to apply padding.
        self.temporaryDocument.setXOffset(-self.spritePadding)
        self.temporaryDocument.setYOffset(-self.spritePadding)
        self.temporaryDocument.setWidth(self.temporaryDocument.width() + (self.spritePadding * 2))
        self.temporaryDocument.setHeight(self.temporaryDocument.height() + (self.spritePadding * 2))
        self.temporaryDocument.refreshProjection()

        print(f"Padding applied. New document size is {self.temporaryDocument.width()} x {self.temporaryDocument.height()}")

    def _createSpritesheetDocumentFromFrames(self):
        if not self.ignoreEmptyFrames:
            frameCount = (self.animationEndTime + 1) - self.animationStartTime
            print(f"Adding {frameCount} frames to the spritesheet document")
            
            size = self._getSpritesheetSize(frameCount)
            self._createSpritesheetDocument(size.columns, size.rows)

            # Convert all frames to spritesheet layers
            for time in range(self.animationStartTime, self.animationEndTime + 1, 1):
                self.temporaryDocument.setCurrentTime(time)
                self.temporaryDocument.refreshProjection()
                self._convertCurrentFrameToSpritesheetLayer()
        else:
            # Grab all of the keyframes
            keyframeTimes = set()
            topLevelLayers = self.temporaryDocument.topLevelNodes()
            for layer in topLevelLayers:
                for time in range(self.animationStartTime, self.animationEndTime + 1, 1):
                    if self._hasKeyframeAtTime(layer, time):
                        keyframeTimes.add(time)
                        print(f"Found keyframe at index: {time}")
            
            frameCount = len(keyframeTimes)
            print(f"Adding {frameCount} frames to the spritesheet document")

            size = self._getSpritesheetSize(frameCount)
            self._createSpritesheetDocument(size.columns, size.rows)
            keyframeTimes = sorted(keyframeTimes)

            # Convert keyframes to spritesheet layers
            for time in keyframeTimes:
                self.temporaryDocument.setCurrentTime(time)
                self.temporaryDocument.refreshProjection()
                self._convertCurrentFrameToSpritesheetLayer()

    def _createSpritesheetDocument(self, columns, rows):
        self.spritesheetColumns = columns
        self.spritesheetRows = rows

        self.spritesheetDocument = self.krita.createDocument(
            columns * self.temporaryDocument.width(), 
            rows * self.temporaryDocument.height(), 
            "Spritesheet", 
            self.temporaryDocument.colorModel(), 
            self.temporaryDocument.colorDepth(), 
            self.temporaryDocument.colorProfile(), 
            self.temporaryDocument.resolution())
        
        self.spritesheetDocument.setBatchmode(True)

        # Remove any default layers
        layers = self.spritesheetDocument.topLevelNodes()
        for layer in layers:
            layer.remove()
        
        print(f"Spritesheet document created with {columns} columns and {rows} rows")
        print(f"Spritesheet document width: {self.spritesheetDocument.width()}")
        print(f"Spritesheet document height: {self.spritesheetDocument.height()}")

    def _getSpritesheetSize(self, frameCount):
        Size = namedtuple("Size", ["columns", "rows"])

        if frameCount == 0:
            return Size(1, 1)
        elif self.spritesheetType == "Rows":
            columnCount = math.ceil(math.sqrt(frameCount))
            return Size(columnCount, math.ceil(frameCount / columnCount))
        elif self.spritesheetType == "Columns":
            rowCount = math.ceil(math.sqrt(frameCount))
            return Size(math.ceil(frameCount / rowCount), rowCount)
        elif self.spritesheetType == "Horizontal Strip":
            return Size(frameCount, 1)
        elif self.spritesheetType == "Vertical Strip":
            return Size(1, frameCount)
        else:
            raise Exception(f"Invalid spritesheet type provided: {self.spritesheetType}")

    def _convertCurrentFrameToSpritesheetLayer(self):
        # Ensure that operations on the temporary document have finished
        # before attempting to retrieve its pixel data.
        self.temporaryDocument.waitForDone()

        width = self.temporaryDocument.width()
        height = self.temporaryDocument.height()

        # Copy the pixel data of the current frame displayed on the temporary document
        currentFramePixelData = self.temporaryDocument.pixelData(0, 0, width, height)

        # Convert the pixel data of the current frame into a layer in the spritesheet document.
        newSpritesheetLayer = self.spritesheetDocument.createNode(str(len(self.spritesheetDocument.topLevelNodes())), "paintlayer")
        self.spritesheetDocument.rootNode().addChildNode(newSpritesheetLayer, None)
        newSpritesheetLayer.setPixelData(currentFramePixelData, 0, 0, width, height)

        self.spritesheetDocument.refreshProjection()

    def _hasKeyframeAtTime(self, layer, time):
        if not layer.visible():
            return False

        if layer.hasKeyframeAtTime(time):
            return True
            
        if len(layer.childNodes()) != 0:
            # check if any of the child nodes
            # have a keyframe at the given time
            for child in layer.childNodes():
                if self._hasKeyframeAtTime(child, time):
                    return True
                
        # reaching this point means that the frame
        # is not a keyframe in the parent layer or
        # any of its children.
        return False
    
    def _positionFramesInSpritesheetDocument(self):
        # Based on the selected spritesheet type, move all of the layers into their respective
        # positions in the spritesheet document.
        if self.spritesheetType == "Rows":
            self._positionSpritesheetFramesByRows()
        elif self.spritesheetType == "Columns":
            self._positionSpritesheetFramesByColumns()
        elif self.spritesheetType == "Horizontal Strip":
            self._positionSpritesheetFramesAsHorizontalStrip()
        elif self.spritesheetType == "Vertical Strip":
            self._positionSpritesheetFramesAsVerticalStrip()
        else:
            raise Exception(f"Invalid spritesheet type provided: {self.spritesheetType}")
            
        self.spritesheetDocument.refreshProjection()

    def _positionSpritesheetFramesByRows(self):
         # Place sprites by filling up each row before moving to the next row.
         layers = self.spritesheetDocument.topLevelNodes()
         for index in range(len(layers)):
             layers[index].move(int(index % self.spritesheetColumns) * self.finalSpriteWidth, 
                                int(index / self.spritesheetColumns) * self.finalSpriteHeight)

    def _positionSpritesheetFramesByColumns(self):
         # Place sprites by filling up each column before moving to the next column.
         layers = self.spritesheetDocument.topLevelNodes()
         for index in range(len(layers)):
             layers[index].move(int(index / self.spritesheetRows) * self.finalSpriteWidth, 
                                int(index % self.spritesheetRows) * self.finalSpriteHeight)

    def _positionSpritesheetFramesAsHorizontalStrip(self):
        # Place sprites in a single horizontal line.
        layers = self.spritesheetDocument.topLevelNodes()
        for index in range(len(layers)):
            layers[index].move(index * self.finalSpriteWidth, 0)

    def _positionSpritesheetFramesAsVerticalStrip(self):
        # Place sprites in a single vertical line.
        layers = self.spritesheetDocument.topLevelNodes()
        for index in range(len(layers)):
            layers[index].move(0, index * self.finalSpriteHeight)

    def _forceCloseDocument(self, document):
        # Set "modified" to false to prevent a popup from showing when closing the document
        document.setModified(False)
        document.close()

    def _exportToFile(self):
        # Ensure that operations in the spritesheet document have finished
        # before attempting to retrieve its pixel data.
        self.spritesheetDocument.waitForDone()

        # If needed, append the correct file extension.
        if Path(self.exportFilePath).suffix != ".png":
            self.exportFilePath += ".png"

        # Export the spritesheet
        self.spritesheetDocument.exportImage(self.exportFilePath, krita.InfoObject())