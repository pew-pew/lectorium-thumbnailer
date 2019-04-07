from thumbnail_generator import ThumbnailGenerator

from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.response import Response, FileResponse
from pyramid.events import NewRequest
from pyramid.view import view_config

import json
from collections import namedtuple


jsonPrettyDumpKwargs = {
    "ensure_ascii": False,
    "indent": 4,
    "sort_keys": True
}


ThumbnailParams = namedtuple("ThumbnailParams",
    ["videoId", "number", "topic", "fontSize", "templateFilename"]
)
def thumbnailParamsFromDict(dict_):
    # TODO: maybe some validation
    return ThumbnailParams(
        videoId=dict_["videoId"],
        number=dict_["number"],
        topic=dict_["topic"],
        fontSize=int(dict_["fontSize"]),
        templateFilename=dict_["template"]
    )


# https://stackoverflow.com/questions/21107057/pyramid-cors-for-ajax-requests
def add_cors_headers_response_callback(event):
    def cors_headers(request, response):
        response.headers.update({
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST,GET,DELETE,PUT,OPTIONS',
            'Access-Control-Allow-Headers': 'Origin, Content-Type, Accept, Authorization',
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Max-Age': '1728000',
        })
    event.request.add_response_callback(cors_headers)


def loadExports():
    try:
        with open("exports.json", "r", encoding="utf-8") as exportsFile:
            return json.load(exportsFile)
    except FileNotFoundError:
        return {}


@view_config(route_name="getExports", renderer="json")
def getExports(request):
    return loadExports()


@view_config(route_name="setExports", renderer="json", request_method="POST")
def setExports(request):
    exports = loadExports()
    exports.update(request.json_body)

    with open("exports.json", "w", encoding="utf-8") as exportsFile:
        json.dump(exports, exportsFile, **jsonPrettyDumpKwargs)

    return Response()


@view_config(route_name="listTemplates", renderer="json")
def listTemplates(request):
    f = lambda n: request.static_url("images/" + n)
    with open("templates/info.json", "r", encoding="utf-8") as f:
        templates = json.load(f)
    return [
        {
            **templ,
            "name": templ["filename"],
            "thumb": request.static_url("templates/" + templ["filename"] + ".png")
        }
        for templ in templates
    ]


generators = dict()


def genThumb(thumbParams):
    # TODO: implement some smart caching and don't rely on browser cache
    global generators

    thumbPath = "images/" + thumbParams.videoId + "/cover.png" # probably not very secure
    templatePath = "templates/" + thumbParams.templateFilename # too

    if thumbParams.templateFilename not in generators:
        generators[thumbParams.templateFilename] = ThumbnailGenerator(templatePath)

    gen = generators[thumbParams.templateFilename]
    gen.setNumberAndFixRectangle(thumbParams.number)
    gen.setTopic(thumbParams.topic)
    gen.setTopicFontSizeAndAlign(thumbParams.fontSize)
    gen.makeThumbnail(thumbPath)

    return thumbPath


@view_config(route_name="previewThumbnail")
def getThumbnail(request):
    thumbParams = thumbnailParamsFromDict(request.GET)
    thumbPath = genThumb(thumbParams)
    return FileResponse(thumbPath)


@view_config(route_name="uploadThumbnail", request_method="POST", renderer="json")
def uploadThumbnail(request):
    from youtube.google_helpers import buildYoutube
    
    thumbParams = thumbnailParamsFromDict(request.json_body)
    thumbPath = genThumb(thumbParams)

    youtube = buildYoutube()

    print(f"Uploading {thumbPath!r} to {thumbParams.videoId!r} ...")
    try:
        youtube.thumbnails().set(
            media_body=thumbPath,
            videoId=thumbParams.videoId
          ).execute()
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
    
    print("Uploaded!")

    return None


with Configurator() as config:
    config.add_route("getExports", "/exports/get")
    config.add_route("setExports", "/exports/set")
    config.add_route("listTemplates", "/templates/list")
    config.add_route("previewThumbnail", "/thumbnail/preview")
    config.add_route("uploadThumbnail", "/thumbnail/upload")
    config.scan()

    config.add_static_view(name="templates", path="templates")
    config.add_static_view(name="images", path="images")
    
    config.add_subscriber(add_cors_headers_response_callback, NewRequest)
    app = config.make_wsgi_app()

server = make_server("localhost", 8888, app)

try:
    server.serve_forever()
finally:
    for gen in generators.values():
        gen.close()
