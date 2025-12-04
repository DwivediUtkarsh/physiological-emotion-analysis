from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import csv

app = Flask(__name__)
CORS(app)

ANNOTATIONS_DIR = 'annotations'
os.makedirs(ANNOTATIONS_DIR, exist_ok=True)

EMOTION_MAP = {
    'Happy': 0,
    'Sad': 1,
    'Angry': 2,
    'Neutral': 3
}
REVERSE_EMOTION_MAP = {v: k for k, v in EMOTION_MAP.items()}

# Helper to get CSV path
def get_csv_path(video_name):
    base = os.path.splitext(video_name)[0]
    return os.path.join(ANNOTATIONS_DIR, f'{base}.csv')

# GET annotations for a video
@app.route('/annotations/<video_name>', methods=['GET'])
def get_annotations(video_name):
    csv_path = get_csv_path(video_name)
    if not os.path.exists(csv_path):
        return jsonify({'annotations': []})
    annotations = []
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        for row in reader:
            if len(row) == 2:
                segment, annotation = row
                annotations.append({
                    'segment': int(segment),
                    'emotion': REVERSE_EMOTION_MAP.get(int(annotation), 'Neutral')
                })
    return jsonify({'annotations': annotations})

# POST: create new annotation CSV for a video
@app.route('/annotations/<video_name>', methods=['POST'])
def create_annotations(video_name):
    data = request.json
    duration = data.get('duration')
    if duration is None:
        return jsonify({'error': 'Missing duration'}), 400
    csv_path = get_csv_path(video_name)
    num_segments = int(duration) // 5
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['segment number', 'annotation'])
        for i in range(num_segments):
            writer.writerow([i, ''])
    return jsonify({'created': True})

# PUT: update annotation CSV for a video
@app.route('/annotations/<video_name>', methods=['PUT'])
def update_annotations(video_name):
    data = request.json
    annotations = data.get('annotations')
    if annotations is None:
        return jsonify({'error': 'Missing annotations'}), 400
    csv_path = get_csv_path(video_name)
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['segment number', 'annotation'])
        for ann in annotations:
            writer.writerow([ann['segment'], EMOTION_MAP.get(ann['emotion'], 3)])
    return jsonify({'updated': True})

if __name__ == '__main__':
    app.run(debug=True)
