from flask import Blueprint, current_app, abort, jsonify, make_response

from .utils import return_result
from findthatpostcode.controllers.areas import Area
from findthatpostcode.db import get_db

bp = Blueprint('areas', __name__, url_prefix='/areas')

@bp.route('/<areacode>')
@bp.route('/<areacode>.<filetype>')
def get_area(areacode, filetype="json"):
    result = Area.get_from_es(areacode, get_db(), boundary=(filetype=='geojson'))

    if filetype == 'geojson':
        status, r = result.geoJSON()
        if status != 200:
            return abort(make_response(jsonify(message=r), status))
        return jsonify(r)

    return return_result(result, filetype, "area.html")
