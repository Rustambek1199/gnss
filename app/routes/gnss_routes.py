from flask import Blueprint, render_template, request, jsonify, redirect
from app.services.gnss_service import gnss_service

gnss_bp = Blueprint('gnss', __name__)

@gnss_bp.route('/')
def root():
    return redirect('/gnss')

@gnss_bp.route('/gnss')
def index():
    return render_template('gnss.html')

@gnss_bp.route('/api/gnss_data')
def get_data():
    st = request.args.get('station', default='TASH', type=str)
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    day = request.args.get('day', type=int)
    hour = request.args.get('hour', type=int)
    
    result = gnss_service.get_data(st_query=st, year=year, month=month, day=day, hour=hour)
    return jsonify(result)

@gnss_bp.route('/api/gnss_hourly')
def get_hourly():
    st = request.args.get('station', default='TASH', type=str)
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    day = request.args.get('day', type=int)
    hour = request.args.get('hour', type=int)
    
    result = gnss_service.get_hourly(st_query=st, year=year, month=month, day=day, hour=hour)
    return jsonify(result)
