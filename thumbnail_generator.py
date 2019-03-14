import os
import argparse

import win32com.client
from win32com.client import constants


"""
Sources:
[1]: http://techarttiki.blogspot.com/2008/08/photoshop-scripting-with-python.html
[2]: https://www.adobe.com/content/dam/acom/en/devnet/photoshop/pdfs/photoshop-cc-scripting-guide-2019.pdf


for units and no messageboxes
https://www.adobe.com/content/dam/acom/en/devnet/photoshop/pdfs/photoshop-cc-vbs-ref-2019.pdf#page=139&zoom=auto,-214,624
"""

# TODO: drop utilities in separate file?

class Rect:
    def __init__(self, bounds):
        self.x0, self.y0, self.x1, self.y1 = bounds

    @property
    def width(self):
        return self.x1 - self.x0

    @property
    def height(self):
        return self.y1 - self.y0

    @property
    def midX(self):
        return (self.x0 + self.x1) / 2

    @property
    def midY(self):
        return (self.y0 + self.y1) / 2

    @staticmethod
    def of(object):
        return Rect(object.Bounds)


def move(obj, x=None, y=None):
    rect = Rect.of(obj)
    if x is None:
        x = rect.x0
    if y is None:
        y = rect.y0
    obj.Translate(x - rect.x0, y - rect.y0)


def moveCenter(obj, x=None, y=None):
    rect = Rect.of(obj)
    if x is None:
        x = rect.midX
    if y is None:
        y = rect.midY
    obj.Translate(x - rect.midX, y - rect.midY)


def resize(obj, width, height, anchor):
    rect = Rect.of(obj)
    obj.Resize(100 * width / rect.width, 100 * height / rect.height, anchor)


def setBounds(obj, coords):
    x0, y0, x1, y1 = coords
    # Since photoshop reports rounded coordinates, we make object larger to improve accuracy of resize and move
    obj.Resize(100 * 100, 100 * 100, constants.psTopLeft)
    move(obj, x0, y0)
    resize(obj, x1 - x0, y1 - y0, constants.psTopLeft)


relativeToCwd = lambda path: os.path.abspath(path)


class ThumbnailGenerator:
    def __init__(self, templatePath):
        print("INIT", flush=True)
        self.constants = constants # keep reference for use in __del__

        self.opened = True

        self.templatePath = relativeToCwd(templatePath)

        # If next line crashes with
        # AttributeError: module 'win32com.gen_py.E891EE9A-D0AE-4CB4-8871-F92C0109F18Ex0x1x0' has no attribute 'CLSIDToClassMap'
        # clear contents of C:\Users\<username>\AppData\Local\Temp\gen_py
        # https://gist.github.com/rdapaz/63590adb94a46039ca4a10994dff9dbe
        self.psApp = win32com.client.gencache.EnsureDispatch("Photoshop.Application")
        self.doc = self.psApp.Open(self.templatePath)

        self.pngSaveOptions = win32com.client.Dispatch("Photoshop.pngSaveOptions")
        self.pngSaveOptions.Compression = 9
        self.pngSaveOptions.Interlaced = False

        def findLayer(layers, name):
            candidates = [layer for layer in layers if layer.Name == name]
            if len(candidates) == 0:
                raise ValueError("layer with name %r not found" % name)
            elif len(candidates) > 1:
                raise ValueError("more than one layer with name %r" % name)
            return candidates[0]

        self.layersDict = {layer.Name: layer for layer in self.doc.Layers}
        
        self.numberLayer = findLayer(self.doc.Layers, "Number")
        self.subjectLayer = findLayer(self.doc.Layers, "Subject")
        self.topicLayer = findLayer(self.doc.Layers, "Topic")
        self.darknessLayer = findLayer(self.doc.Layers, "Darkness")
        self.rectangleLayer = findLayer(self.doc.Layers, "Rectangle")

        self.bulbLayer = findLayer(self.darknessLayer.Layers, "Lamp")


        self.bottomLayer = findLayer(self.doc.Layers, "Bottom")
        self.nameLayer = findLayer(self.bottomLayer.Layers, "Name")
        print("INIT - DONE", flush=True)

    def close(self):
        if not self.opened:
            return

        self.doc.Close(self.constants.psDoNotSaveChanges) #PsSaveOptions.psDoNotSaveChanges)
        self.opened = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __del__(self):
        self.close()

    def makeActive(self):
        self.psApp.ActiveDocument = self.doc

    def setTopic(self, topic):
        self.topicLayer.TextItem.Contents = topic.replace("\n", "\r") # Photoshop is weird

    def setTopicFontSizeAndAlign(self, size):
        self.makeActive()

        self.topicLayer.TextItem.Size = size
        
        topY = max(
            Rect.of(self.subjectLayer).y1,
            Rect.of(self.rectangleLayer).y1
        )
        botY = Rect.of(self.bulbLayer).y0
        
        moveCenter(self.topicLayer, y=(topY + botY) / 2)

    def setNumberAndFixRectangle(self, number):
        self.makeActive()
        number = str(number)
        self.numberLayer.TextItem.Contents = number
      
        if 0:
            numberRect = Rect.of(self.numberLayer)
            resize(self.rectangleLayer, numberRect.width + 45 * 2, numberRect.height + 35 * 2)
            moveCenter(self.rectangleLayer, numberRect.midX, numberRect.midY)
        elif len(number) == 1:
            setBounds(self.rectangleLayer, (1737.0, 20.0, 1883.0, 173.0))
        elif len(number) == 2:
            setBounds(self.rectangleLayer, (1669.0, 20.0, 1882.0, 173.0))
        else:
            raise ValueError("number has too many digits (only 1 or 2 supported)")

        print(self.rectangleLayer.Bounds)

    def makeThumbnail(self, outPath):#, number=None, topic=None):
        self.makeActive()

        # Photoshop treats paths relative to it's own working dir?
        outPath = relativeToCwd(outPath)

        dirname = os.path.dirname(outPath)
        if dirname:
            os.makedirs(dirname, exist_ok=True)

        self.doc.SaveAs(outPath, self.pngSaveOptions, True, 2) # see page 32 in [2]

if __name__ == "__main__":
    gen = ThumbnailGenerator("empty1.psd")

    gen.psApp.Preferences.RulerUnits = constants.psPixels
    gen.psApp.Preferences.TypeUnits = constants.psTypePoints

    topY = max(gen.subjectLayer.Bounds[3], gen.rectangleLayer.Bounds[3])
    botY = gen.bulbLayer.Bounds[1]

    # print([abs(a - b) for a, b in zip(rb, nb)])

    # for i in [70, 90, 110]:
    #     input("Press enter")

    # gen.topicLayer.Translate(10, )