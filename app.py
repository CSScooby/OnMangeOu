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
                found = get_something(lat, lng, 'restaurant')
                if found:
                    for restaurant in found:
                        # Vérifier si le restaurant est déjà dans la liste
                        if restaurant not in restos:
                            restos.append(restaurant)
                restos.extend(found)
        
        return render_template('results.html', restos=restos)
    
    return render_template('index.html')

GOOGLE_API_KEY = '  # Remplace par ta clé API

def get_route(depart, arrivee):
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={depart}&destination={arrivee}&key={GOOGLE_API_KEY}"
    response = requests.get(url)
    chemin = response.json()
        # Sauvegarder dans un fichier
    with open('route_debug.json', 'w', encoding='utf-8') as f:
        json.dump(chemin, f, ensure_ascii=False, indent=4)
    return chemin


if __name__ == '__main__':
    app.run(debug=True)
