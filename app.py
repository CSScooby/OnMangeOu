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

# --- Fonction pour charger les types autorisés depuis JSON ---
def load_allowed_types(filepath='type.json', category='nourriture'):
    """Charge la liste des types autorisés depuis un fichier JSON pour une catégorie donnée."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return set(data.get(category, [])) # Utiliser un set pour des recherches rapides
    except FileNotFoundError:
        print(f"Erreur: Le fichier {filepath} n'a pas été trouvé.")
        return set()
    except json.JSONDecodeError:
        print(f"Erreur: Impossible de décoder le JSON depuis {filepath}.")
        return set()
    except Exception as e:
        print(f"Erreur inattendue lors de la lecture de {filepath}: {e}")
        return set()
# --- Fin fonction load_allowed_types ---

# Fonction pour récupérer les lieux près d'une coordonnée en utilisant des mots-clés
def get_nearby_places(lat, lng, keywords, radius=5000):
    """
    Trouve des lieux près des coordonnées données via l'API Google Places Nearby Search
    en utilisant une recherche par mots-clés.
    """
    # Construire la partie keyword de l'URL, encodée correctement
    keyword_query = urllib.parse.quote_plus(keywords)
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius}&keyword={keyword_query}&key={GOOGLE_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        places_data = response.json()
        return places_data.get('results', [])
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de l'appel à l'API Places Nearby Search (keyword): {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"Erreur lors du décodage de la réponse JSON Places (keyword): {e}")
        return []


@app.route('/', methods=['GET'])
def index():
    """Affiche la page d'accueil avec le formulaire."""
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    """Traite la soumission du formulaire et affiche les résultats."""
    depart = request.form['depart']
    arrivee = request.form['arrivee']

    # Charger les types autorisés pour la catégorie 'nourriture'
    allowed_place_types = load_allowed_types(category='nourriture')
    if not allowed_place_types:
        print("Avertissement: Aucun type de lieu autorisé n'a été chargé depuis type.json. La recherche pourrait ne rien retourner.")

    route_data = get_route(depart, arrivee)

    restos = []
    restos_ids = set()  # Utiliser un set pour vérifier rapidement les doublons par ID
    all_types_found = set()  # Ensemble pour stocker tous les types uniques trouvés

    # Intervalle d'échantillonnage en kilomètres
    sampling_interval_km = 15.0  # Chercher tous les 15 km

    # Définir les mots-clés pour la recherche Places API
    search_keywords = "restaurant OR cafe OR boulangerie OR \"aire autoroute\" OR \"aire de service\" OR \"fast food\" OR \"meal takeaway\""

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
                    # Effectuer la recherche en utilisant les mots-clés définis
                    found_places = get_nearby_places(current_lat, current_lng, search_keywords)  # Utilise le rayon par défaut de 5km

                    if found_places:
                        for place in found_places:
                            place_id = place.get('place_id')
                            types_raw = set(place.get('types', []))  # Utiliser un set pour l'intersection

                            # *** Filtrage basé sur type.json ***
                            # Vérifier s'il y a une intersection entre les types du lieu et les types autorisés
                            if place_id and place_id not in restos_ids and not allowed_place_types.isdisjoint(types_raw):
                                # Le lieu a au moins un type autorisé, on continue le traitement
                                name = place.get('name')
                                vicinity = place.get('vicinity')
                                rating = place.get('rating')  # Récupérer la note
                                user_ratings_total = place.get('user_ratings_total')  # Récupérer le nombre d'avis
                                cleaned_types = [t.replace('_', ' ').capitalize() for t in types_raw if t not in ['point_of_interest', 'establishment', 'food', 'restaurant', 'store']]  # Ajouter 'store' à exclure
                                geometry = place.get('geometry')
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
                                        'place_id': place_id,
                                        'rating': rating,  # Ajouter la note
                                        'user_ratings_total': user_ratings_total,  # Ajouter le nombre d'avis
                                        'types': cleaned_types,  # Utiliser les types nettoyés
                                        'maps_url': maps_url,  # Ajouter l'URL Google Maps
                                        'lat': resto_lat,  # Ajouter la latitude
                                        'lng': resto_lng  # Ajouter la longitude
                                    })
                                    restos_ids.add(place_id)

                    # Réinitialiser le compteur de distance après un échantillon
                    distance_since_last_sample = 0.0

                # Mettre à jour le dernier point
                last_point = (current_lat, current_lng)

        else:
            print("Avertissement: overview_polyline non trouvée dans la réponse de l'API Directions.")

    # Trier les types pour l'affichage
    sorted_types = sorted(list(all_types_found))

    if not restos:
        message = "Aucun lieu pertinent pour manger trouvé le long de cet itinéraire."
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
