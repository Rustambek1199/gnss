from flask import Blueprint, render_template, request, jsonify
from app.services.chang_service import chang_service

chang_bp = Blueprint('chang', __name__)

@chang_bp.route('/chang')
def chang_dashboard():
    return render_template('index.html')

@chang_bp.route('/api/data')
def get_data():
    region = request.args.get('region', 'Navoiy')
    year = request.args.get('year', '')
    month = request.args.get('month', '')
    day = request.args.get('day', '')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    result = chang_service.get_data(
        region=region, year=year, month=month, day=day,
        start_date=start_date, end_date=end_date
    )
    return jsonify(result)

@chang_bp.route('/api/predict', methods=['POST'])
def predict():
    data = request.json or {}
    result = chang_service.predict(data)
    return jsonify(result)

@chang_bp.route('/api/simulate', methods=['GET', 'POST'])
def simulate():
    if request.method == 'POST':
        data = request.json or {}
        barriers = data.get('barriers', [50, 150, 250])
        barrier_height = data.get('barrier_height', 20)
    else:
        barriers = [50, 150, 250]
        barrier_height = 20
        
    img_uri = chang_service.simulate(barriers=barriers, barrier_height=barrier_height)
    return jsonify({'image': img_uri})

@chang_bp.route('/api/barrier_impact', methods=['POST'])
def barrier_impact():
    data = request.json or {}
    barriers = data.get('barriers', [50, 150, 250])
    barrier_height = data.get('barrier_height', 20)
    
    result = chang_service.calculate_barrier_impact(barriers=barriers, barrier_height=barrier_height)
    return jsonify(result)
