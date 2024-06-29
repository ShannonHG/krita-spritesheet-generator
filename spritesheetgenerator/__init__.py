import krita
from .spritesheetgeneratorextension import SpritesheetGeneratorExtension

Scripter.addExtension(SpritesheetGeneratorExtension(krita.Krita.instance()))
