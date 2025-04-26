from flask import Flask, render_template, request
import requests

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        depart = request.form['depart']
        arrivee = request.form['arrivee']
        
        route = get_route(depart, arrivee)
        
        restos = []
        
        for leg in route['routes'][0]['legs']:
            for step in leg['steps']:
                lat = step['end_location']['lat']
                lng = step['end_location']['lng']
                found = get_restaurants(lat, lng)
                restos.extend(found)
        
        return render_template('results.html', restos=restos)
    
    return render_template('index.html')

GOOGLE_API_KEY = 'AIzaSyCRgWwxYG9iw8wEVzPZLv_0D2heYfLxqws'  # Remplace par ta clé API

def get_route(depart, arrivee):
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={depart}&destination={arrivee}&key={GOOGLE_API_KEY}"
    response = requests.get(url)
    data = response.json()
    return data

def get_restaurants(lat, lng):
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=2000&type=restaurant&key={GOOGLE_API_KEY}"
    response = requests.get(url)
    data = response.json()
    return data['results']

if __name__ == '__main__':
    app.run(debug=True)
