# Import the dependencies.

from flask import Flask, jsonify
import datetime as dt
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base_db = automap_base()
# reflect the tables
Base_db.prepare(autoload_with=engine)

# Save references to each table
measurement  = Base_db.classes.measurement 

Station = Base_db.classes.station 

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################

# Define the homepage route
@app.route("/")
def home():
    return (
        f"Welcome to the Weather API!<br/><br/>"
        f"Available Routes:<br/>"
        f"<a href='/api/v1.0/precipitation'>/api/v1.0/precipitation</a> - Precipitation data for the last 12 months.<br/>"
        f"<a href='/api/v1.0/stations'>/api/v1.0/stations</a> - List of weather stations.<br/>"
        f"<a href='/api/v1.0/tobs'>/api/v1.0/tobs</a> - Temperature observations for the most active station for the previous year.<br/>"
        f"/api/v1.0/&lt;start&gt; - Temperature statistics (TMIN, TAVG, TMAX) from a specified start date.<br/>"
        f"/api/v1.0/&lt;start&gt;/&lt;end&gt; - Temperature statistics (TMIN, TAVG, TMAX) for a specified date range.<br/>"
    )

# Define the /api/v1.0/precipitation route
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Calculate the date one year ago from the last date in the database
    last_date = session.query(func.max(measurement.date)).scalar()
    last_date = dt.datetime.strptime(last_date, "%Y-%m-%d")
    one_year_ago = last_date - dt.timedelta(days=365)

    # Query precipitation data for the last 12 months
    precipitation_data = (
        session.query(measurement.date, measurement.prcp)
        .filter(measurement.date >= one_year_ago)
        .all()
    )

    # Convert the query results to a dictionary
    precipitation_dict = {date: prcp for date, prcp in precipitation_data}

    return jsonify(precipitation_dict)

# Define the /api/v1.0/stations route
@app.route("/api/v1.0/stations")
def stations():
    # Query the list of stations
    stations_data = session.query(Station.station).all()
    stations_list = [station[0] for station in stations_data]

    return jsonify(stations_list)

# Define the /api/v1.0/tobs route
@app.route("/api/v1.0/tobs")
def temperature_observations():
    # Find the most active station
    most_active_station = (
        session.query(measurement.station)
        .group_by(measurement.station)
        .order_by(func.count().desc())
        .first()[0]
    )

    # Calculate the date one year ago from the last date in the database
    last_date = session.query(func.max(measurement.date)).scalar()
    last_date = dt.datetime.strptime(last_date, "%Y-%m-%d")
    one_year_ago = last_date - dt.timedelta(days=365)

    # Query temperature observations for the most active station for the previous year
    temperature_data = (
        session.query(measurement.date, measurement.tobs)
        .filter(measurement.station == most_active_station)
        .filter(measurement.date >= one_year_ago)
        .all()
    )

    return jsonify(temperature_data)

# Define the /api/v1.0/<start> and /api/v1.0/<start>/<end> routes
@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temperature_stats(start, end=None):
    # Query temperature statistics based on the provided start and end dates
    if end:
        # Calculate TMIN, TAVG, and TMAX for the specified date range
        temperature_stats = (
            session.query(
                func.min(measurement.tobs).label("TMIN"),
                func.avg(measurement.tobs).label("TAVG"),
                func.max(measurement.tobs).label("TMAX"),
            )
            .filter(measurement.date >= start)
            .filter(measurement.date <= end)
            .all()
        )
    else:
        # Calculate TMIN, TAVG, and TMAX for dates greater than or equal to the start date
        temperature_stats = (
            session.query(
                func.min(measurement.tobs).label("TMIN"),
                func.avg(measurement.tobs).label("TAVG"),
                func.max(measurement.tobs).label("TMAX"),
            )
            .filter(measurement.date >= start)
            .all()
        )

    # Convert the query results to a dictionary
    stats_dict = {
        "TMIN": temperature_stats[0][0],
        "TAVG": temperature_stats[0][1],
        "TMAX": temperature_stats[0][2],
    }

    return jsonify(stats_dict)

if __name__ == "__main__":
    app.run(debug=True)
