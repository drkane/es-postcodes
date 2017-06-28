from __future__ import print_function
from datetime import datetime
import argparse
import math
from urllib.parse import urlencode

import bottle
from elasticsearch import Elasticsearch

from metadata import AREA_TYPES, KEY_AREA_TYPES, OTHER_CODES
from controllers.postcodes import *
from controllers.areatypes import *
from controllers.areas import *
from controllers.points import *
from controllers.controller import *

app = bottle.default_app()


# @TODO delete
def get_area_search_link(q, p=1, size=100, filetype=None):
    query_vars = {"q": q}
    if p > 1:
        query_vars["page"] = p
    if size != 100:
        query_vars["size"] = size
    return "/areas/search{}?{}".format(set_url_filetype(filetype), urlencode(query_vars))


def return_result(result, status=200, filetype="json", template=None):
    if filetype == "html" and not template:
        bottle.abort(500, "No template provided")

    if status != 200:
        if filetype == "json":
            raise bottle.HTTPError(status=status, body=result)
        elif filetype == "html":
            return bottle.abort(status, result)

    if filetype == "json":
        return result
    elif filetype == "html":
        return bottle.template(template,
                               result=result,
                               included={(i["type"], i["id"]): i for i in result.get("included", [])},
                               key_area_types=KEY_AREA_TYPES,
                               other_codes=OTHER_CODES
                               )


@app.route('/')
@app.route('/index.html')
def index():
    ats = Areatypes(app.config)
    ats.get()
    (status, result) = ats.topJSON()
    return bottle.template('index.html',
                           result=result,
                           key_area_types=KEY_AREA_TYPES
                           )


@app.route('/postcodes/redirect')
def postcode_redirect():
    postcode = bottle.request.query.postcode
    return bottle.redirect('/postcodes/{}.html'.format(postcode))


@app.route('/postcodes/<postcode>')
@app.route('/postcodes/<postcode>.<filetype>')
def postcode(postcode, filetype="json"):
    """ View details about a particular postcode
    """
    pc = Postcode(app.config)
    pc.get_by_id(postcode)
    (status, result) = pc.topJSON()
    return return_result(result, status, filetype, "postcode.html")


@app.route('/areas/search')
@app.route('/areas/search.<filetype>')
def areaname(filetype="json"):
    areas = Areas(app.config)
    areas.search(bottle.request.query.q)
    (status, result) = areas.topJSON()
    return return_result(result, status, filetype, "areasearch.html")


@app.route('/areas/<areacode>.geojson')
def area_geojson(areacode):
    a = Area(app.config)
    a.get_by_id(areacode.strip(), boundary=True)
    return a.geoJSON()


@app.route('/areas/<areacode>')
@app.route('/areas/<areacode>.<filetype>')
def area(areacode, filetype="json"):
    a = Area(app.config)
    a.get_by_id(areacode.strip())
    (status, result) = a.topJSON()
    return return_result(result, status, filetype, "area.html")


@app.route('/areatypes')
@app.route('/areatypes.<filetype>')
def areatypes_all(filetype="json"):
    ats = Areatypes(app.config)
    ats.get()
    (status, result) = ats.topJSON()
    return return_result(result, status, filetype, "areatypes.html")


@app.route('/areatypes/<areatype>')
@app.route('/areatypes/<areatype>.<filetype>')
def areatype(areatype, filetype="json"):
    app.config["stop_recursion"] = False
    at = Areatype(app.config)
    at.get_by_id(areatype)
    (status, result) = at.topJSON()
    return return_result(result, status, filetype, "areatype.html")


@app.route('/points/redirect')
def points_redirect():
    lat = float(bottle.request.query.lat)
    lon = float(bottle.request.query.lon)
    return bottle.redirect('/points/{:,.5f},{:,.5f}.html'.format(lat, lon))


@app.route('/points/<lat:float>,<lon:float>')
@app.route('/points/<lat:float>,<lon:float>.<filetype:re:(html|json)>')
def get_point(lat, lon, filetype="json"):
    po = Point(app.config)
    po.get_by_id(lat, lon)
    (status, result) = po.topJSON()
    return return_result(result, status, filetype, "postcode.html")


@app.route('/static/<filename:path>')
def send_static(filename):
    return bottle.static_file(filename, root='./static')


def main():

    parser = argparse.ArgumentParser(description='')  # @TODO fill in

    # server options
    parser.add_argument('-host', '--host', default="localhost", help='host for the server')
    parser.add_argument('-p', '--port', default=8080, help='port for the server')
    parser.add_argument('--debug', action='store_true', dest="debug", help='Debug mode (autoreloads the server)')

    # elasticsearch options
    parser.add_argument('--es-host', default="localhost", help='host for the elasticsearch instance')
    parser.add_argument('--es-port', default=9200, help='port for the elasticsearch instance')
    parser.add_argument('--es-url-prefix', default='', help='Elasticsearch url prefix')
    parser.add_argument('--es-use-ssl', action='store_true', help='Use ssl to connect to elasticsearch')
    parser.add_argument('--es-index', default='postcode', help='index used to store postcode data')

    args = parser.parse_args()

    app.config["es"] = Elasticsearch(host=args.es_host, port=args.es_port, url_prefix=args.es_url_prefix, use_ssl=args.es_use_ssl)
    app.config["es_index"] = args.es_index

    bottle.debug(args.debug)

    bottle.run(app, host=args.host, port=args.port, reloader=args.debug)

if __name__ == '__main__':
    main()
