# On Mange Où ?

Trouvez des restaurants le long de votre itinéraire ! Cette application web utilise Flask et l'API Google Maps pour vous aider à planifier vos pauses sur la route.

## Fonctionnalités

*   Recherche d'itinéraire entre deux adresses.
*   Découverte de restaurants à proximité de l'itinéraire.
*   Filtrage des résultats par note minimale et type de cuisine.
*   Tri des résultats par pertinence, note ou distance (si la localisation est activée).
*   Visualisation des restaurants sur une carte interactive (Leaflet).
*   Interaction entre la liste des résultats et la carte.
*   Interface responsive adaptée aux mobiles.

## Installation

Suivez ces étapes pour installer et lancer l'application localement.

1.  **Cloner le dépôt :**
    ```bash
    git clone https://github.com/CSScooby/OnMangeOu.git
    cd OnMangeOu 
    ```

2.  **Créer un environnement virtuel (recommandé) :**
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate

    # macOS / Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Installer les dépendances :**
    Assurez-vous d'avoir `pip` à jour (`pip install --upgrade pip`).
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configurer la clé API Google Maps :**
    *   Créez un fichier nommé `.env` à la racine du projet.
    *   Ajoutez votre clé API Google Maps dans ce fichier comme suit :
        ```
        GOOGLE_API_KEY = "VOTRE_CLE_API_GOOGLE_MAPS_ICI"
        ```
    *   **Important :** Assurez-vous que les APIs suivantes sont activées pour votre clé dans la Google Cloud Console :
        *   Directions API
        *   Places API
        *   Geocoding API (implicitement utilisée par Directions/Places)

5.  **Lancer l'application Flask :**
    ```bash
    flask run
    # Ou si debug est activé dans app.py :
    # python app.py
    ```

6.  **Accéder à l'application :**
    Ouvrez votre navigateur et allez à l'adresse `http://127.0.0.1:5000` (ou l'adresse indiquée par Flask).

## Utilisation

1.  Entrez votre adresse de départ et d'arrivée dans le formulaire.
2.  Cliquez sur "Trouver des restaurants sur la route".
3.  Explorez les résultats affichés dans la liste et sur la carte.
4.  Utilisez le bouton "Filtres" pour affiner votre recherche par note ou type de cuisine.
5.  Utilisez le bouton "Localisation" (icône cible) pour activer le tri par distance par rapport à votre position actuelle (nécessite l'autorisation du navigateur).
6.  Cliquez sur un restaurant dans la liste ou sur son marqueur sur la carte pour le mettre en évidence et faire défiler/zoomer.
7.  Cliquez sur le nom d'un restaurant pour ouvrir sa fiche sur Google Maps dans un nouvel onglet.

## Fichiers Clés

*   `app.py`: Logique principale de l'application Flask, gestion des routes et appels API.
*   `config.py`: Stockage de la clé API Google (à créer).
*   `requirements.txt`: Liste des dépendances Python.
*   `templates/`: Contient les fichiers HTML (index.html, results.html).
*   `static/`: Contient les fichiers CSS, JavaScript et les assets (icônes).
    *   `style_index.css`, `style_results.css`: Styles CSS.
    *   `filter.js`: Logique JavaScript pour les filtres, la carte et les interactions.
    *   `assets/`: Icônes SVG.