"""
Meteostat JSON API Server

The code is licensed under the MIT license.
"""

from datetime import datetime
import json
from flask import Response, abort
from meteostat import Hourly
from server import app, utils


"""
Meteostat configuration
"""
Hourly.max_age = 60 * 60 * 3
Daily.autoclean = False

"""
Endpoint configuration
"""
# Query parameters
parameters = [
    ('station', str, None),
    ('start', str, None),
    ('end', str, None),
    ('tz', str, None),
    ('model', bool, True),
    ('freq', str, None),
    ('units', str, None)
]

# Maximum number of days per request
max_days = 30


@app.route('/stations/hourly')
def stations_hourly():
    """
    Return hourly station data in JSON format
    """

    # Get query parameters
    args = utils.get_parameters(parameters)

    # Check if required parameters are set
    if args['station'] and len(args['start']) == 10 and len(args['end']) == 10:

        # Convert start & end date strings to datetime
        start = datetime.strptime(args['start'], '%Y-%m-%d')
        end = datetime.strptime(f'{args["end"]} 23:59:59', '%Y-%m-%d %H:%M:%S')

        # Get number of days between start and end date
        date_diff = (end - start).days

        # Check date range
        if date_diff < 0 or date_diff > max_days:
            # Bad request
            abort(400)

        # Get data
        data = Hourly(args['station'], start, end, timezone=args['tz'], model=args['model'])

        # Check if any data
        if data.count() > 0:

            # Fetch DataFrame
            data = data.fetch()

            # Convert condition code to integer
            data['coco'] = data['coco'].astype('Int64')

            # DateTime Index to String
            data.index = data.index.strftime('%Y-%m-%d %H:%M:%S')
            data = data.reset_index().to_json(orient="records")

        else:

            # No data
            data = '[]'

        # Inject meta data
        meta = {}
        meta['generated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Generate output string
        output = f'''{{"meta":{json.dumps(meta)},"data":{data}}}'''

        # Return
        return Response(output, mimetype='application/json')

    else:

        # Bad request
        abort(400)
