# EduDrive - Plateforme de Vente de Formations en Ligne

## 📝 Description du Projet

EduDrive est une plateforme de vente de formations en ligne avec un système de parrainage intégré. Les formations sont hébergées sur Google Drive, et l'accès est accordé après paiement et validation de l'inscription via un code de parrainage.

### Objectifs Principaux
- Vente de formations pré-enregistrées
- Système de parrainage à deux niveaux
- Gestion des paiements mobiles
- Interface d'administration simple pour le client
- Intégration avec Google Drive pour l'hébergement des formations
- Canal Telegram premium optionnel

## 🏗️ Architecture du Projet

### Frontend (React + Vite)
- Single Page Application
- Routage avec React Router
- État global géré avec Redux
- Interface utilisateur responsive
- Composants réutilisables

### Backend (Django REST Framework)
- API REST complète
- Authentification JWT
- Gestion des médias avec compression automatique
- Interface d'administration personnalisée
- Système de webhooks pour les paiements

## 💻 Technologies Utilisées

### Frontend
- React 18+
- Vite
- Redux Toolkit
- React Router 6
- Tailwind CSS
- Axios pour les requêtes HTTP

### Backend
- Python 3.8+
- Django 4.2+
- Django REST Framework
- Pillow pour le traitement d'images
- FFmpeg pour la compression vidéo
- JWT pour l'authentification

## 🔧 Configuration et Installation

### Prérequis
- Python 3.8+
- Node.js 16+
- FFmpeg
- Virtualenv

### Installation Backend
```bash
# Créer et activer l'environnement virtuel
python -m venv env
source env/bin/activate  # Unix
env\Scripts\activate     # Windows

# Installer les dépendances
pip install -r requirements.txt

# Configurer la base de données
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser

# Lancer le serveur
python manage.py runserver
```

### Installation Frontend
```bash
# Installer les dépendances
npm install

# Lancer le serveur de développement
npm run dev
```

## 📊 Structure de la Base de Données

### Modèles Principaux

#### User (accounts.models.User)
- Extension de AbstractUser
- Champs personnalisés pour le parrainage et le portefeuille
- Génération automatique du code de parrainage

#### Formation (Edu.models.Formation)
- Gestion des formations avec compression média automatique
- Limite de taille des images (800x500)
- Compression vidéo optimisée

#### Sponsorship (accounts.models.Sponsorship)
- Relations de parrainage
- Calcul des commissions (40% direct, 10% indirect)

#### Payment (Edu.models.Payment)
- Suivi des transactions
- Support multiple types de paiement
- Intégration webhooks

## 🔒 Système de Paiement

### Approches Considérées

#### 1. Approche Frontend (Initiale)
- Paiement initié depuis le frontend
- Réponse de l'API traitée côté client
- Mise à jour du backend via requête client
- **Avantages**: Plus simple à implémenter
- **Inconvénients**: Moins sécurisé

#### 2. Approche Webhook (Adoptée)
- Paiement initié depuis le frontend
- Confirmation via webhook backend
- Sécurité renforcée
- Traitement asynchrone
- **Avantages**: Plus sécurisé, fiable
- **Inconvénients**: Configuration plus complexe

### Flux de Paiement Implémenté
1. Création transaction backend
2. Redirection API paiement
3. Notification webhook
4. Validation et activation accès

## 👥 Système de Parrainage

### Fonctionnalités
- Codes de parrainage uniques
- Commission directe de 40%
- Commission indirecte de 10%
- Portefeuille utilisateur
- Tableau de bord des gains

## 🎯 Statut du Projet

### Complété
- [x] Configuration initiale backend
- [x] Modèles de données
- [x] Interface d'administration
- [x] API REST de base
- [x] Système d'authentification
- [x] Compression média
- [x] Structure frontend

### En Cours
- [ ] Intégration paiement mobile
- [ ] Webhooks
- [ ] Tests unitaires et intégration
- [ ] Documentation API
- [ ] Déploiement

### À Faire
- [ ] Intégration Google Drive
- [ ] Système de notifications
- [ ] Tableau de bord analytics
- [ ] Optimisation performances
- [ ] Sécurité renforcée

## 🔜 Prochaines Étapes

1. Finaliser l'intégration des paiements
2. Mettre en place les tests
3. Documenter l'API
4. Déployer la version bêta
5. Configurer le monitoring

## 🤝 Contribution

1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📝 Notes Techniques

### Points d'Attention
- Sécurité des paiements
- Validation des transactions
- Gestion des erreurs
- Performance média
- Expérience utilisateur
- Maintenance admin

### Décisions Techniques
1. Utilisation des webhooks pour la sécurité
2. Compression média automatique
3. JWT pour l'authentification
4. Architecture modulaire
5. Interface admin personnalisée

## 📄 License

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 📞 Contact

Pour toute question ou suggestion, veuillez ouvrir une issue dans le repository.

---
Dernière mise à jour: 13 janvier 2025