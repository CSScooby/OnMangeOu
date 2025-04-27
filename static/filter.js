document.addEventListener('DOMContentLoaded', () => {
    // Récupérer les éléments du DOM
    const minRatingSelect = document.getElementById('min-rating');
    const typeCheckboxesContainer = document.getElementById('type-filters');
    const resultsList = document.getElementById('results-list');
    const resetButton = document.getElementById('reset-filters');
    const dataScript = document.getElementById('restos-data');
    const mapContainer = document.getElementById('map');
    const filterToggleButton = document.getElementById('filter-toggle-button');
    const filterCloseButton = document.getElementById('filter-close-button');
    const filterControls = document.getElementById('filter-controls'); // C'est maintenant le panneau overlay
    const filterBackdrop = document.getElementById('filter-backdrop');
    const locationButton = document.getElementById('location-button');
    const sortBySelect = document.getElementById('sort-by');
    const distanceSortOption = sortBySelect ? sortBySelect.querySelector('option[value="distance"]') : null;

    // --- Variables pour la localisation ---
    let userLat = null;
    let userLng = null;
    let locationError = false; // Pour savoir si la localisation a échoué
    let userLocationMarker = null; // Référence au marqueur de l'utilisateur

    // --- Fonction Haversine (copiée depuis app.py et adaptée en JS) ---
    function haversine(lat1, lon1, lat2, lon2) {
        const R = 6371; // Rayon de la Terre en km
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        lat1 = lat1 * Math.PI / 180;
        lat2 = lat2 * Math.PI / 180;
        const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                  Math.cos(lat1) * Math.cos(lat2) *
                  Math.sin(dLon / 2) * Math.sin(dLon / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return R * c; // Distance en km
    }
    // --- Fin Fonction Haversine ---

    // --- Gestion Filtre Overlay ---
    function openFilterPanel() {
        if (filterControls && filterBackdrop) {
            filterControls.classList.add('open');
            filterBackdrop.classList.add('visible');
            filterToggleButton.setAttribute('aria-expanded', 'true');
            document.body.style.overflow = 'hidden'; // Empêcher le scroll du body
        }
    }

    function closeFilterPanel() {
        if (filterControls && filterBackdrop) {
            filterControls.classList.remove('open');
            filterBackdrop.classList.remove('visible');
            filterToggleButton.setAttribute('aria-expanded', 'false');
            document.body.style.overflow = ''; // Restaurer le scroll du body
        }
    }

    if (filterToggleButton && filterCloseButton && filterControls && filterBackdrop) {
        filterToggleButton.addEventListener('click', openFilterPanel);
        filterCloseButton.addEventListener('click', closeFilterPanel);
        filterBackdrop.addEventListener('click', closeFilterPanel);

        // Fermer avec la touche Echap
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && filterControls.classList.contains('open')) {
                closeFilterPanel();
            }
        });

    } else {
        console.warn("Éléments pour le panneau de filtres overlay non trouvés.");
    }
    // --- Fin Gestion Filtre Overlay ---

    // Vérifier si les éléments nécessaires existent (y compris le conteneur map)
    if (!minRatingSelect || !typeCheckboxesContainer || !resultsList || !dataScript || !resetButton || !mapContainer) {
        console.error("Certains éléments DOM pour le filtrage ou la carte sont manquants.");
        // S'il manque juste la map, on peut potentiellement continuer sans elle
        if (!mapContainer) {
            console.warn("Conteneur de carte non trouvé. La carte ne sera pas affichée.");
        }
        // Si les éléments de base manquent, on arrête.
        if (!minRatingSelect || !typeCheckboxesContainer || !resultsList || !dataScript || !resetButton) return;
    }

    // --- Vérification initiale des capacités de géolocalisation ---
    if (navigator.geolocation) {
        if(locationButton) locationButton.disabled = false; // Activer le bouton si la géo est dispo
    } else {
        console.warn("La géolocalisation n'est pas supportée par ce navigateur.");
        if(locationButton) locationButton.disabled = true;
        if(distanceSortOption) distanceSortOption.disabled = true;
    }

    // --- Gestion du clic sur le bouton Localisation ---
    if (locationButton) {
        locationButton.addEventListener('click', () => {
            if (!navigator.geolocation) return;

            locationButton.disabled = true; // Désactiver pendant la recherche
            locationButton.querySelector('span').textContent = 'Localisation...';

            navigator.geolocation.getCurrentPosition(
                (position) => {
                    userLat = position.coords.latitude;
                    userLng = position.coords.longitude;
                    locationError = false;
                    console.log(`Localisation obtenue: ${userLat}, ${userLng}`);

                    // --- Ajout/Mise à jour du marqueur utilisateur sur la carte ---
                    if (map) {
                        // Supprimer l'ancien marqueur s'il existe
                        if (userLocationMarker) {
                            userLocationMarker.remove();
                        }
                        // Créer une icône spécifique pour l'utilisateur (ex: un cercle bleu)
                        const userIcon = L.divIcon({
                            className: 'user-location-icon',
                            html: '<div style="background-color: #3B82F6; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 5px rgba(0,0,0,0.5);"></div>',
                            iconSize: [12, 12],
                            iconAnchor: [6, 6] // Centre de l'icône
                        });
                        // Ajouter le nouveau marqueur
                        userLocationMarker = L.marker([userLat, userLng], {
                             icon: userIcon,
                             zIndexOffset: 900 // Légèrement en dessous des marqueurs highlightés
                             })
                             .addTo(map)
                             .bindPopup("Votre position");
                        // map.setView([userLat, userLng], 13);
                    }
                    // --- Fin Ajout/Mise à jour marqueur utilisateur ---

                    // Calculer les distances pour tous les restaurants
                    allRestos.forEach(resto => {
                        if (resto.lat != null && resto.lng != null) {
                            resto.distanceFromUser = haversine(userLat, userLng, resto.lat, resto.lng);
                        } else {
                            resto.distanceFromUser = Infinity; // Mettre une valeur très grande si pas de coords
                        }
                    });

                    // Activer l'option de tri par distance et le bouton
                    if(distanceSortOption) distanceSortOption.disabled = false;
                    locationButton.disabled = false;
                    locationButton.querySelector('span').textContent = 'Distance activée'; // Feedback
                    applyFiltersAndSort(); // Appliquer filtres et tri
                },
                (error) => {
                    console.error(`Erreur de géolocalisation: ${error.message}`);
                    userLat = null;
                    userLng = null;
                    locationError = true;
                    allRestos.forEach(resto => resto.distanceFromUser = undefined); // Nettoyer distances
                    if(distanceSortOption) distanceSortOption.disabled = true; // Désactiver l'option
                    sortBySelect.value = 'default'; // Revenir au tri par défaut si distance était sélectionné
                    locationButton.disabled = false;
                    locationButton.querySelector('span').textContent = 'Erreur localisation';
                    alert("Impossible d'obtenir votre localisation. Assurez-vous d'avoir autorisé l'accès.");

                    // --- Supprimer le marqueur utilisateur en cas d'erreur ---
                    if (userLocationMarker) {
                        userLocationMarker.remove();
                        userLocationMarker = null;
                    }
                    // --- Fin Suppression marqueur utilisateur ---

                    applyFiltersAndSort(); // Réappliquer sans tri distance
                },
                { // Options de géolocalisation
                    enableHighAccuracy: false, // Moins précis mais plus rapide/économe
                    timeout: 10000, // 10 secondes max
                    maximumAge: 60000 // Accepter une position vieille de 1 min max
                }
            );
        });
    }

    // Parser les données des restaurants depuis le JSON intégré
    let allRestos = [];
    let markers = {}; // Stocker les instances de marqueurs par place_id
    try {
        allRestos = JSON.parse(dataScript.textContent);
        // Filtrer les restos sans coordonnées valides pour la carte
        allRestos = allRestos.filter(r => r.lat != null && r.lng != null);
    } catch (e) {
        console.error("Erreur lors du parsing des données JSON des restaurants:", e);
        resultsList.innerHTML = '<li>Erreur lors du chargement des données des restaurants.</li>';
        return;
    }

    // Créer des icônes Leaflet personnalisées
    const defaultIcon = L.icon({
        iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
        shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    });
    const highlightedIcon = L.icon({
        iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
        shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
        iconSize: [35, 57],
        iconAnchor: [17, 57],
        popupAnchor: [1, -48],
        shadowSize: [57, 57]
    });

    // --- Initialisation de la carte Leaflet ---
    let map = null;
    let markersLayer = null; // Pour gérer les marqueurs facilement

    if (mapContainer && allRestos.length > 0) { // Initialiser la carte seulement si le conteneur existe et qu'il y a des restos
        try {
            // Coordonnées initiales (premier restaurant ou une valeur par défaut)
            const initialCoords = [allRestos[0].lat, allRestos[0].lng];
            map = L.map('map').setView(initialCoords, 11); // Zoom initial (ajuster si besoin)

            // Ajouter une couche de tuiles OpenStreetMap (gratuite)
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }).addTo(map);

            // Créer un groupe de couches pour les marqueurs. Ce groupe sera vidé et rempli à chaque filtrage.
            markersLayer = L.layerGroup().addTo(map);

        } catch (e) {
            console.error("Erreur lors de l'initialisation de Leaflet:", e);
            map = null; // Empêcher les tentatives d'utilisation de la carte
            mapContainer.innerHTML = '<p class="message">Impossible de charger la carte.</p>';
        }

    } else if (mapContainer) {
        mapContainer.innerHTML = '<p class="message">Aucun restaurant à afficher sur la carte.</p>';
    }
    // --- Fin Initialisation Carte ---

    // --- Fonctions d'interaction ---
    function highlightListItem(placeId, scroll = false) { // Ajouter un paramètre pour le scroll
        // Retirer le surlignage des autres éléments d'abord
        document.querySelectorAll('#results-list li.highlighted').forEach(el => el.classList.remove('highlighted'));

        const listItem = document.querySelector(`#results-list li[data-place-id="${placeId}"]`);
        if (listItem) {
            listItem.classList.add('highlighted');
            // Faire défiler l'élément dans la vue si demandé
            if (scroll) {
                listItem.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        }
    }

    function unhighlightListItem(placeId) {
        const listItem = document.querySelector(`#results-list li[data-place-id="${placeId}"]`);
        if (listItem) {
            listItem.classList.remove('highlighted');
        }
    }

    function highlightMarker(placeId) {
        // Retirer le surlignage des autres marqueurs d'abord
        Object.values(markers).forEach(m => {
            m.setIcon(defaultIcon);
            m.setZIndexOffset(0);
        });

        const marker = markers[placeId];
        if (marker) {
            marker.setIcon(highlightedIcon);
            marker.setZIndexOffset(1000);
        }
    }

    function unhighlightMarker(placeId) {
        const marker = markers[placeId];
        if (marker) {
            marker.setIcon(defaultIcon);
            marker.setZIndexOffset(0);
        }
    }
    // --- Fin Fonctions d'interaction ---

    // Fonction pour afficher les restaurants (liste ET carte)
    function renderResults(restosToRender) {
        resultsList.innerHTML = ''; // Vider la liste actuelle
        markers = {}; // Vider les anciens marqueurs stockés

        // !! Point Clé : Vider la couche de marqueurs sur la carte !!
        if (map && markersLayer) {
            markersLayer.clearLayers(); // Supprime tous les marqueurs de la carte
        }

        if (restosToRender.length === 0) {
            resultsList.innerHTML = '<li class="message">Aucun restaurant ne correspond à vos filtres.</li>';
            return;
        }

        const bounds = []; // Pour ajuster la vue de la carte

        restosToRender.forEach(resto => {
            const placeId = resto.place_id; // Récupérer l'ID unique

            // --- Rendu de la liste ---
            const li = document.createElement('li');
            li.setAttribute('data-place-id', placeId); // Ajouter l'ID pour l'interaction

            let ratingHtml = '';
            if (resto.rating) {
                ratingHtml = `
                    <span class="rating">
                        <img src="/static/assets/star.svg" alt="Étoile" class="icon">
                        ${resto.rating}
                    </span>`;
                if (resto.user_ratings_total) {
                    ratingHtml += ` <span class="rating-count">(${resto.user_ratings_total} avis)</span>`;
                }
                ratingHtml += '<br>';
            }
            let typesHtml = '';
            if (resto.types && resto.types.length > 0) {
                typesHtml = `<span class="types">${resto.types.join(', ')}</span>`;
            }
            let distanceHtml = '';
            if (resto.distanceFromUser != null && resto.distanceFromUser !== Infinity) {
                distanceHtml = `<span class="distance">📍 ${resto.distanceFromUser.toFixed(1)} km</span>`;
            }

            li.innerHTML = `
                <a href="${resto.maps_url}" target="_blank" class="map-link">
                    <strong>${resto.name}</strong><br>
                    <span class="vicinity">${resto.vicinity}</span>
                </a>
                <div class="details">
                    ${ratingHtml}
                    ${typesHtml}
                    ${distanceHtml}
                </div>
            `;

            li.addEventListener('mouseenter', () => {
                highlightMarker(placeId);
            });
            li.addEventListener('mouseleave', () => {
                unhighlightMarker(placeId);
                unhighlightListItem(placeId);
            });
            li.addEventListener('click', () => {
                const marker = markers[placeId];
                if (map && marker) {
                    map.setView(marker.getLatLng(), 15); // Centre et zoom sur le marqueur
                    highlightMarker(placeId); // Surligne le marqueur
                    highlightListItem(placeId); // Surligne l'item (sans scroll)
                    marker.openPopup(); // Ouvre le popup
                }
            });

            resultsList.appendChild(li);
            // --- Fin Rendu Liste ---

            // --- Ajout du marqueur sur la carte ---
            if (map && markersLayer && resto.lat != null && resto.lng != null) {
                try {
                    const marker = L.marker([resto.lat, resto.lng], { icon: defaultIcon });
                    marker.bindPopup(`<b>${resto.name}</b><br>${resto.vicinity}`);

                    marker.on('mouseover', () => {
                        highlightListItem(placeId);
                    });
                    marker.on('mouseout', () => {
                        unhighlightListItem(placeId);
                    });
                    marker.on('click', () => {
                        highlightListItem(placeId, true);
                        highlightMarker(placeId);
                    });

                    markersLayer.addLayer(marker);
                    markers[placeId] = marker;
                    bounds.push([resto.lat, resto.lng]);
                } catch (e) {
                    console.warn(`Impossible d'ajouter le marqueur pour ${resto.name}:`, e);
                }
            }
            // --- Fin Ajout Marqueur ---
        });

        // Ajuster la vue de la carte pour montrer tous les marqueurs
        if (map && bounds.length > 0) {
            try {
                map.fitBounds(bounds, { padding: [50, 50] });
            } catch (e) {
                console.warn("Impossible d'ajuster les limites de la carte:", e);
            }
        }

        if (map) {
            map.off('click'); // Supprimer l'ancien listener pour éviter les doublons
            map.on('click', () => {
                document.querySelectorAll('#results-list li.highlighted').forEach(el => el.classList.remove('highlighted'));
                Object.values(markers).forEach(m => {
                    m.setIcon(defaultIcon);
                    m.setZIndexOffset(0);
                });
            });
        }
    }

    // Fonction pour appliquer les filtres ET le tri
    function applyFiltersAndSort() {
        // 1. Appliquer les filtres (note, type)
        const minRating = parseFloat(minRatingSelect.value);
        const selectedTypesCheckboxes = typeCheckboxesContainer.querySelectorAll('input[name="type_filter"]:checked');
        const selectedTypes = Array.from(selectedTypesCheckboxes).map(cb => cb.value);

        let filteredRestos = allRestos.filter(resto => {
            const ratingMatch = resto.rating == null || resto.rating >= minRating;
            const typeMatch = selectedTypes.length === 0 || (resto.types && selectedTypes.some(selectedType => resto.types.includes(selectedType)));
            return ratingMatch && typeMatch;
        });

        // 2. Appliquer le tri
        const sortBy = sortBySelect.value;
        if (sortBy === 'distance' && userLat !== null && userLng !== null) {
            // Trier par distance croissante (les Infinity vont à la fin)
            filteredRestos.sort((a, b) => (a.distanceFromUser ?? Infinity) - (b.distanceFromUser ?? Infinity));
        } else if (sortBy === 'rating') {
            // Trier par note décroissante (mettre ceux sans note à la fin)
            filteredRestos.sort((a, b) => (b.rating ?? -1) - (a.rating ?? -1));
        }
        // else 'default': pas de tri spécifique après le filtrage, l'ordre dépend de l'API

        // 3. Afficher les résultats filtrés et triés
        renderResults(filteredRestos);
    }

    // Fonction pour réinitialiser les filtres ET le tri
    function resetFilters() {
        minRatingSelect.value = "0";
        const checkboxes = typeCheckboxesContainer.querySelectorAll('input[name="type_filter"]');
        checkboxes.forEach(checkbox => checkbox.checked = false);
        sortBySelect.value = "default"; // Réinitialiser aussi le tri

        if (userLocationMarker) {
            userLocationMarker.remove();
            userLocationMarker = null;
        }
        if (distanceSortOption) distanceSortOption.disabled = true;
        userLat = null; userLng = null; locationError = false;
        locationButton.querySelector('span').textContent = 'Trier par distance'; // Reset text

        applyFiltersAndSort(); // Appliquer les filtres/tri réinitialisés
    }

    // Ajouter des écouteurs d'événements aux contrôles de filtre ET de tri
    minRatingSelect.addEventListener('change', applyFiltersAndSort);
    sortBySelect.addEventListener('change', applyFiltersAndSort); // Écouteur sur le select de tri
    const checkboxes = typeCheckboxesContainer.querySelectorAll('input[name="type_filter"]');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', applyFiltersAndSort);
    });
    resetButton.addEventListener('click', resetFilters);

    // Afficher les résultats initiaux (filtrés mais non triés par défaut)
    applyFiltersAndSort();
});

