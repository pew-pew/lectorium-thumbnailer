from thumbnail_generator import ThumbnailGenerator

from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.response import Response, FileResponse
from pyramid.events import NewRequest

import json


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


def getExports(request):
    try:
        with open("exports.json", "r", encoding="utf-8") as exportsFile:
            return json.load(exportsFile)
    except FileNotFoundError:
        return {}


def setExports(request):
    with open("exports.json", "w", encoding="utf-8") as exportsFile:
        json.dump(request.json_body, exportsFile,
                ensure_ascii=False, indent=4, sort_keys=True)
    return Response()


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
def getThumbnail(request):
    # TODO: implement some smart caching and don't rely on browser cache
    
    global generators
    get = request.GET.get
    number = get("number")
    topic = get("topic")
    videoId = get("videoId")
    fontSize = int(get("fontSize"))
    templateFilename = get("template")
    thumbPath = "images/" + videoId + "/cover.png"
    templatePath = "templates/" + templateFilename

    if templateFilename not in generators:
        generators[templateFilename] = ThumbnailGenerator(templatePath)

    gen = generators[templateFilename]
    gen.setNumberAndFixRectangle(number)
    gen.setTopic(topic)
    gen.setTopicFontSizeAndAlign(fontSize)
    gen.makeThumbnail(thumbPath)

    return FileResponse(thumbPath)


with Configurator() as config:
    config.add_route("getExports", "/exports/get")
    config.add_view(getExports, route_name="getExports", renderer="json")

    config.add_route("setExports", "/exports/set")
    config.add_view(setExports, route_name="setExports",
                    request_method="POST")

    config.add_route("listTemplates", "/templates/list")
    config.add_view(listTemplates, route_name="listTemplates", renderer="json")

    config.add_route("thumbnail", "/thumbnail")
    config.add_view(getThumbnail, route_name="thumbnail")

    config.add_subscriber(add_cors_headers_response_callback, NewRequest)

    config.add_static_view(name="templates", path="templates")
    config.add_static_view(name="images", path="images")
    app = config.make_wsgi_app()
server = make_server("localhost", 8888, app)

try:
    server.serve_forever()
finally:
    for gen in generators.values():
        gen.close()
