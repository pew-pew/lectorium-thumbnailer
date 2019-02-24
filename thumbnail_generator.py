import win32com.client
import os
import argparse

"""
Sources:
[1]: http://techarttiki.blogspot.com/2008/08/photoshop-scripting-with-python.html
[2]: https://www.adobe.com/content/dam/acom/en/devnet/photoshop/pdfs/photoshop-cc-scripting-guide-2019.pdf
"""

relativeToCwd = lambda path: os.path.join(os.getcwd(), path)

class ThumbnailGenerator:
    def __init__(self, templatePath):
        self.opened = True

        self.templatePath = relativeToCwd(templatePath)

        self.psApp = win32com.client.Dispatch("Photoshop.Application")
        self.doc = self.psApp.Open(self.templatePath)

        self.pngSaveOptions = win32com.client.Dispatch("Photoshop.pngSaveOptions")
        self.pngSaveOptions.compression = 9
        self.pngSaveOptions.interlaced = False

        layersDict = {layer.Name: layer for layer in self.doc.ArtLayers}
        
        try:
            self.numberLayer = layersDict["Номер"]
            self.topicLayer = layersDict["Тема"]
        except KeyError:
            raise ValueError("Template must have root layers with names 'Номер' and 'Тема'")

    def close(self):
        if not self.opened:
            return

        if hasattr(self, "doc"):
            self.doc.Close(2) # close without saving

        # delete COM objects just in case
        for attr in "numberLayer topicLayer doc psApp pngSaveOptions".split():
            if hasattr(self, attr):
                delattr(self, attr)

        self.opened = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __del__(self):
        self.close()

    def makeThumbnail(self, number, topic, outPath):
        self.numberLayer.TextItem.Contents = "#%s" % number
        self.topicLayer.TextItem.Contents = topic.replace("\n", "\r") # Photoshop is weird

        # Photoshop treats paths relative to it's own working dir?
        outPath = relativeToCwd(outPath)

        dirname = os.path.dirname(outPath)
        if dirname:
            os.makedirs(dirname, exist_ok=True)

        self.doc.SaveAs(outPath, self.pngSaveOptions, True, 2) # see page 32 in [2]
        
        """
        TODO?: ability to specify font size?
        see page 149 at
        https://www.adobe.com/content/dam/acom/en/devnet/photoshop/pdfs/photoshop-cc-vbs-ref-2019.pdf
        """