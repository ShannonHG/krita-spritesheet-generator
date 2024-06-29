import krita
from .uispritesheetgenerator import UISpritesheetGenerator

class SpritesheetGeneratorExtension(krita.Extension):

    def __init__(self, parent):
        super(SpritesheetGeneratorExtension, self).__init__(parent)

    def setup(self):
        pass

    def createActions(self, window):
        action = window.createAction("", "Spritesheet Generator")
        action.setToolTip("Export frames in the animation timeline as a spritesheet.")
        action.triggered.connect(self.showUI)

    def showUI(self):
        self.userInterface = UISpritesheetGenerator()
        self.userInterface.show()