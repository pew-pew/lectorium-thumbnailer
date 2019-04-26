import os
import argparse
import shutil
import re

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


def findLayer(layers, name, orNone=False):
    candidates = [layer for layer in layers if layer.Name == name]
    if len(candidates) == 0:
        if orNone:
            return None
        raise ValueError("layer with name %r not found" % name)
    elif len(candidates) > 1:
        raise ValueError("more than one layer with name %r" % name)
    return candidates[0]


# def smt():
#     p = os.path.join(os.path.expanduser("~"), "AppData/Local/Temp/gen_py")
#     print("Removing directory", p)
#     shutil.rmtree(p)


class ThumbnailGenerator:
    def __init__(self, templatePath):
        self.constants = constants # keep reference for use in __del__

        self.opened = True
        # otherwise, if exception is thrown on win32com line
        # __del__ method will throw another exception because there is no attribute `doc`
        self.doc = None

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
        
        self.numberLayer = findLayer(self.doc.Layers, "Number")
        self.subjectLayer = findLayer(self.doc.Layers, "Subject")
        self.topicLayer = findLayer(self.doc.Layers, "Topic")
        self.darknessLayer = findLayer(self.doc.Layers, "Darkness")
        self.maybeRectangleLayer = findLayer(self.doc.Layers, "Rectangle", orNone=True)

        self.bulbLayer = findLayer(self.darknessLayer.Layers, "Lamp")

        self.bottomLayer = findLayer(self.doc.Layers, "Bottom")
        self.nameLayer = findLayer(self.bottomLayer.Layers, "Name")

        color2rgb = lambda c: (c.Red, c.Green, c.Blue)
        self.whiteRGB = (255, 255, 255) #color2rgb(self.topicLayer.TextItem.Color.RGB)
        self.themedRGB = color2rgb(self.subjectLayer.TextItem.Color.RGB)
        print("THEMED:", self.themedRGB)

    def close(self):
        if not self.opened:
            return

        if self.doc is not None:
            self.doc.Close(self.constants.psDoNotSaveChanges)
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
        self.setTextRangeColor(self.topicLayer, 0, len(topic), self.whiteRGB)

        if not topic:
            return

        firstLine = topic.split("\n")[0]
        if firstLine.lower().startswith("семинар"):
            self.setTextRangeColor(self.topicLayer, 0, len(firstLine), self.themedRGB)

    def setTopicFontSizeAndAlign(self, size):
        self.makeActive()

        self.topicLayer.TextItem.Size = size
        
        # topY = max(
        #     Rect.of(self.subjectLayer).y1,
        #     Rect.of(self.maybeRectangleLayer or self.numberLayer).y1
        # )
        topY = Rect.of(self.maybeRectangleLayer or self.numberLayer).y1
        botY = Rect.of(self.bulbLayer).y0
        
        moveCenter(self.topicLayer, y=(topY + botY) / 2)

    def setNumber(self, number):
        self.makeActive()
        
        number = str(number) if self.maybeRectangleLayer is not None else ("#" + str(number))

        self.numberLayer.TextItem.Contents = number
      
        if self.maybeRectangleLayer is None:
            return

        rectangleLayer = self.maybeRectangleLayer

        if 1:
            numberRect = Rect.of(self.numberLayer)
            resize(rectangleLayer, numberRect.width + 45 * 2, numberRect.height + 35 * 2, constants.psTopLeft)
            moveCenter(rectangleLayer, numberRect.midX, numberRect.midY)
        elif len(number) == 1:
            setBounds(rectangleLayer, (1737.0, 20.0, 1883.0, 173.0))
        elif len(number) == 2:
            setBounds(rectangleLayer, (1669.0, 20.0, 1882.0, 173.0))
        else:
            raise ValueError("number has too many digits (only 1 or 2 supported)")

    def makeThumbnail(self, outPath):#, number=None, topic=None):
        self.makeActive()

        # Photoshop treats paths relative to it's own working dir?
        outPath = relativeToCwd(outPath)

        dirname = os.path.dirname(outPath)
        if dirname:
            os.makedirs(dirname, exist_ok=True)

        self.doc.SaveAs(outPath, self.pngSaveOptions, True, 2) # see page 32 in [2]

    def setTextRangeColor(self, textLayer, idxFrom, idxTo, rgb):
        self.makeActive()
        # charID2stringID = lambda s: self.psApp.TypeIDToStringID(app.CharIDToTypeID(s))
        s2id = lambda s: self.psApp.StringIDToTypeID(s)

        self.doc.ActiveLayer = textLayer

        ref = win32com.client.Dispatch("Photoshop.actionReference");  
        ref.PutEnumerated(s2id("layer"), s2id("ordinal"), s2id("targetEnum"))

        layerDesc = self.psApp.ExecuteActionGet(ref)
        
        textRange = layerDesc.GetObjectValue(s2id("textKey")).GetList(s2id("textStyleRange")).GetObjectValue(0);

        textRange.PutInteger(s2id("from"), idxFrom)
        textRange.PutInteger(s2id("to"), idxTo)

        textStyle = textRange.GetObjectValue(s2id("textStyle"))
        col = textStyle.GetObjectValue(s2id("color"))
        col.PutDouble(s2id("red"), rgb[0])
        col.PutDouble(s2id("green"), rgb[1])
        col.PutDouble(s2id("blue"), rgb[2])
        textStyle.PutObject(s2id("color"), s2id("color"), col)

        textRange.PutObject(s2id("textStyle"), s2id("textStyle"), textStyle)

        actionList = win32com.client.Dispatch("Photoshop.actionList");
        actionList.PutObject(s2id('textStyleRange'), textRange);

        textAction = win32com.client.Dispatch("Photoshop.actionDescriptor");
        textAction.PutList(s2id('textStyleRange'), actionList);

        reference = win32com.client.Dispatch("Photoshop.actionReference");
        reference.PutEnumerated(s2id('textLayer'), s2id('ordinal'), s2id('targetEnum'));

        action = win32com.client.Dispatch("Photoshop.actionDescriptor");
        action.PutReference(s2id('null'), reference);
        action.PutObject(s2id('to'), s2id('textLayer'), textAction);

        self.psApp.ExecuteAction(s2id('set'), action, constants.psDisplayNoDialogs);


if __name__ == "__main__":
    gen = ThumbnailGenerator("tmp/sem.psd")
    app = gen.psApp

    # gen.psApp.Preferences.RulerUnits = constants.psPixels
    # gen.psApp.Preferences.TypeUnits = constants.psTypePoints