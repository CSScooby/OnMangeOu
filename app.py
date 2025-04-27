from flask import Flask, render_template, request
import requests
import json
from config import GOOGLE_API_KEY  # Importer la clé API depuis config.py
import urllib.parse  # Importer pour l'encodage d'URL
import polyline  # Importer la bibliothèque polyline
import math  # Importer pour les calculs trigonométriques et de distance

app = Flask(__name__)

# --- Fonction de calcul de distance Haversine ---
def haversine(lat1, lon1, lat2, lon2):
    """Calcule la distance en kilomètres entre deux points GPS."""
    R = 6371  # Rayon de la Terre en km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)
    a = math.sin(dLat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dLon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance
# --- Fin fonction Haversine ---

# Fonction pour récupérer les lieux (ex: restaurants) près d'une coordonnée
# Augmentation du rayon par défaut à 5000m (5km)
def get_nearby_places(lat, lng, place_type, radius=5000):
    """
    Trouve des lieux d'un certain type près des coordonnées données via l'API Google Places Nearby Search.
    """
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius}&type={place_type}&key={GOOGLE_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Vérifie les erreurs HTTP
        places_data = response.json()
        return places_data.get('results', [])  # Retourne la liste des résultats ou une liste vide
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de l'appel à l'API Places Nearby Search: {e}")
        return []  # Retourne une liste vide en cas d'erreur réseau/API
    except json.JSONDecodeError as e:
        print(f"Erreur lors du décodage de la réponse JSON Places: {e}")
        return []  # Retourne une liste vide si la réponse n'est pas du JSON valide


@app.route('/', methods=['GET'])
def index():
    """Affiche la page d'accueil avec le formulaire."""
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    """Traite la soumission du formulaire et affiche les résultats."""
    depart = request.form['depart']
    arrivee = request.form['arrivee']

    route_data = get_route(depart, arrivee)

    restos = []
    restos_ids = set()  # Utiliser un set pour vérifier rapidement les doublons par ID
    all_types_found = set()  # Ensemble pour stocker tous les types uniques trouvés

    # Intervalle d'échantillonnage en kilomètres
    sampling_interval_km = 15.0  # Chercher tous les 15 km

    if route_data and 'routes' in route_data and route_data['routes']:
        # Récupérer la polyline encodée de l'itinéraire global
        overview_polyline_encoded = route_data['routes'][0].get('overview_polyline', {}).get('points')

        if overview_polyline_encoded:
            # Décoder la polyline en une liste de coordonnées (latitude, longitude)
            decoded_points = polyline.decode(overview_polyline_encoded)

            distance_since_last_sample = 0.0
            last_point = None

            # Parcourir les points décodés de l'itinéraire
            for i, point in enumerate(decoded_points):
                current_lat, current_lng = point

                # Calculer la distance depuis le dernier point
                if last_point:
                    distance_increment = haversine(last_point[0], last_point[1], current_lat, current_lng)
                    distance_since_last_sample += distance_increment

                # Si c'est le premier point ou si on a dépassé l'intervalle d'échantillonnage
                if i == 0 or distance_since_last_sample >= sampling_interval_km:
                    print(f"Sampling point at ~{distance_since_last_sample:.1f} km: ({current_lat}, {current_lng})")  # Log
                    # Effectuer la recherche de restaurants autour de ce point
                    found_restaurants = get_nearby_places(current_lat, current_lng, 'restaurant')  # Utilise le rayon par défaut de 5km

                    if found_restaurants:
                        for restaurant in found_restaurants:
                            resto_id = restaurant.get('place_id')
                            if resto_id and resto_id not in restos_ids:
                                name = restaurant.get('name')
                                vicinity = restaurant.get('vicinity')
                                rating = restaurant.get('rating')  # Récupérer la note
                                user_ratings_total = restaurant.get('user_ratings_total')  # Récupérer le nombre d'avis
                                types_raw = restaurant.get('types', [])  # Récupérer les types (liste)
                                cleaned_types = [t.replace('_', ' ').capitalize() for t in types_raw if t not in ['point_of_interest', 'establishment', 'food', 'restaurant']]
                                geometry = restaurant.get('geometry')
                                location = geometry.get('location') if geometry else None
                                resto_lat = location.get('lat') if location else None
                                resto_lng = location.get('lng') if location else None

                                if name and vicinity and resto_lat is not None and resto_lng is not None:
                                    all_types_found.update(cleaned_types)
                                    query = urllib.parse.quote_plus(f"{name}, {vicinity}")
                                    maps_url = f"https://www.google.com/maps/search/?api=1&query={query}"

                                    restos.append({
                                        'name': name,
                                        'vicinity': vicinity,
                                        'place_id': resto_id,
                                        'rating': rating,  # Ajouter la note
                                        'user_ratings_total': user_ratings_total,  # Ajouter le nombre d'avis
                                        'types': cleaned_types,  # Utiliser les types nettoyés
                                        'maps_url': maps_url,  # Ajouter l'URL Google Maps
                                        'lat': resto_lat,  # Ajouter la latitude
                                        'lng': resto_lng  # Ajouter la longitude
                                    })
                                    restos_ids.add(resto_id)

                    # Réinitialiser le compteur de distance après un échantillon
                    distance_since_last_sample = 0.0

                # Mettre à jour le dernier point
                last_point = (current_lat, current_lng)

        else:
            print("Avertissement: overview_polyline non trouvée dans la réponse de l'API Directions.")

    # Trier les types pour l'affichage
    sorted_types = sorted(list(all_types_found))

    if not restos:
        message = "Aucun restaurant trouvé le long de cet itinéraire."
        return render_template('results.html', restos=restos, message=message, available_types=[])
    else:
        return render_template('results.html', restos=restos, available_types=sorted_types)


def get_route(depart, arrivee):
    """
    Obtient l'itinéraire entre deux points via l'API Google Directions.
    """
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={depart}&destination={arrivee}&key={GOOGLE_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Vérifie les erreurs HTTP
        chemin = response.json()
        try:
            with open('route_debug.json', 'w', encoding='utf-8') as f:
                json.dump(chemin, f, ensure_ascii=False, indent=4)
        except IOError as e:
            print(f"Erreur lors de l'écriture du fichier de débogage route: {e}")
        return chemin
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de l'appel à l'API Directions: {e}")
        return None  # Retourner None en cas d'erreur réseau/API
    except json.JSONDecodeError as e:
        print(f"Erreur lors du décodage de la réponse JSON Directions: {e}")
        return None  # Retourner None si la réponse n'est pas du JSON valide


if __name__ == '__main__':
    app.run(debug=True)
