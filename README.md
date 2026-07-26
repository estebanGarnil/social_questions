# Questionly — listes de questions collaboratives

Application full-stack Vue et Django permettant de créer des listes publiques
ou privées, de les remplir à plusieurs et de suivre une progression distincte
pour chaque utilisateur.

## Fonctionnalités

- interface Vue 3 mobile-first, adaptée aux écrans de 320 px et plus ;
- inscription et authentification par JWT ;
- rotation et révocation des refresh tokens ;
- CRUD des listes ;
- CRUD des questions avec image facultative ;
- rôles `contributor` et `administrator` ;
- abonnements aux listes accessibles ;
- suppression logique des listes et questions ;
- parcours et historique propres à chaque utilisateur ;
- tirage aléatoire sans répétition pendant un même parcours ;
- abonnements à sens unique entre utilisateurs ;
- accueil simplifié avec recherche, listes suivies, personnes suivies et
  découverte ;
- recherche globale des listes accessibles et des utilisateurs ;
- profils publics avec compteurs et listes publiques ;
- séries de 20 questions maximum, avec un nouveau départ à chaque retour sur
  la page de jeu ;
- tirage et enregistrement question par question ;
- priorité aux questions jamais vues, puis réutilisation des anciennes
  questions lorsqu'il n'en reste pas assez ;
- interface sombre et violette, navigation tactile fixe et écran de jeu
  immersif sur mobile ;
- documentation OpenAPI regroupée par domaines ;
- environnements Docker de développement et de production ;
- MySQL et reverse proxy Nginx.

## Démarrage avec Docker

### Développement

```bash
docker compose -f docker-compose.dev.yml up --build
```

L'application est ensuite disponible sur :

- frontend : `http://localhost:8080/` ;
- Swagger : `http://localhost:8080/api/docs/` ;
- API directe : `http://localhost:8000/api/` ;
- Vite direct : `http://localhost:5173/`.

Les sources Django et Vue sont montées dans les conteneurs : leurs serveurs se
rechargent automatiquement pendant le développement.

Au premier démarrage, le backend attend automatiquement que MySQL accepte
réellement les connexions réseau avant d'exécuter les migrations.

### Production

Créer le fichier de configuration :

```bash
cp .env.prod.example .env.prod
```

Sous PowerShell :

```powershell
Copy-Item .env.prod.example .env.prod
```

Remplacer impérativement les secrets et noms de domaine dans `.env.prod`, puis :

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

La version de production compile Vue dans une étape Node dédiée, sert les
fichiers avec Nginx et transmet `/api/` au backend Gunicorn.

## Installation locale sans Docker

```bash
python -m venv .venv
```

Sous Linux ou macOS :

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Sous Windows PowerShell :

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Dans un second terminal :

```bash
cd frontend
npm install
npm run dev
```

L'installation locale utilise SQLite par défaut. Les compositions Docker
configurent automatiquement MySQL.

## Pages du frontend

- `/` : recherche, listes suivies, personnes suivies et découverte ;
- `/recherche?q=...` : recherche simultanée de listes et d'utilisateurs ;
- `/utilisateurs/{id}` : profil public et listes publiques d'un utilisateur ;
- `/connexion` et `/inscription` : authentification ;
- `/listes/{id}` : détail d'une liste ;
- `/listes/{id}/jouer` : tirage personnel des questions ;
- `/listes/{id}/editer` : questions et collaborateurs ;
- `/listes/nouvelle` : création ;
- `/profil` : listes personnelles, abonnements et recherche d'utilisateurs.

## Authentification

### Créer un compte

```http
POST /api/auth/register/
Content-Type: application/json

{
  "email": "user@example.com",
  "display_name": "Esteban",
  "password": "A-secure-password-2026!",
  "password_confirm": "A-secure-password-2026!"
}
```

### Obtenir les tokens

```http
POST /api/auth/token/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "A-secure-password-2026!"
}
```

Les routes privées attendent ensuite :

```http
Authorization: Bearer <access_token>
```

## Routes principales

| Méthode | Route | Description |
|---|---|---|
| `POST` | `/api/auth/register/` | Créer un compte |
| `POST` | `/api/auth/token/` | Obtenir access et refresh tokens |
| `POST` | `/api/auth/token/refresh/` | Renouveler les tokens |
| `POST` | `/api/auth/logout/` | Révoquer un refresh token |
| `GET/PATCH/DELETE` | `/api/auth/me/` | Consulter, modifier ou désactiver son compte |
| `GET` | `/api/discovery/home/` | Alimenter les trois sections de l'accueil |
| `GET` | `/api/discovery/search/?q=...` | Rechercher des listes et utilisateurs |
| `GET` | `/api/users/?search=nom` | Rechercher des utilisateurs |
| `GET` | `/api/users/{id}/` | Consulter un profil public |
| `GET` | `/api/users/{id}/lists/` | Lister ses listes publiques |
| `POST/DELETE` | `/api/users/{id}/follow/` | Suivre ou ne plus suivre un utilisateur |
| `GET` | `/api/users/following/` | Lister les utilisateurs suivis |
| `GET/POST` | `/api/lists/` | Lister ou créer des listes |
| `GET/PATCH/DELETE` | `/api/lists/{id}/` | Gérer une liste |
| `GET/POST` | `/api/lists/{id}/questions/` | Lister ou ajouter des questions |
| `GET/PATCH/DELETE` | `/api/lists/{id}/questions/{question_id}/` | Gérer une question |
| `GET/POST` | `/api/lists/{id}/collaborators/` | Lister ou ajouter des collaborateurs |
| `PATCH/DELETE` | `/api/lists/{id}/collaborators/{collaboration_id}/` | Gérer un collaborateur |
| `POST/DELETE` | `/api/lists/{id}/subscribe/` | S'abonner ou se désabonner |
| `POST` | `/api/lists/{id}/pick-random-question/` | Tirer et enregistrer la prochaine question |
| `GET` | `/api/lists/{id}/progress/` | Lire sa progression personnelle |
| `GET` | `/api/history/` | Lister ses parcours |
| `GET` | `/api/history/{id}/` | Consulter un parcours et ses questions |

Le paramètre `scope` de `/api/lists/` accepte `owned`, `collaborating` ou
`subscribed`.

## Organisation de Swagger

La documentation `api/docs/` est répartie dans les groupes suivants :

- Authentification ;
- Découverte ;
- Utilisateurs ;
- Listes ;
- Questions ;
- Collaborateurs ;
- Abonnements ;
- Historique.

La route `api/schema/` expose le schéma OpenAPI brut.

## Règles de permissions

- Le propriétaire peut tout faire sur sa liste.
- Un administrateur peut modifier la liste et toutes ses questions.
- Un contributeur peut ajouter des questions et ne modifier ou supprimer que
  celles dont il est l'auteur.
- Une liste privée est visible par son propriétaire et ses collaborateurs.
- Une liste publique est visible par tous.
- Seul le propriétaire peut supprimer la liste.

## Historique et tirage aléatoire

Chaque utilisateur possède ses propres objets `Exploration` et `QuestionView`.
Deux utilisateurs consultant la même liste ne partagent donc jamais leur
progression.

Une série contient au maximum 20 questions :

1. le frontend appelle `pick-random-question/` pour chaque question affichée ;
2. chaque réponse est immédiatement enregistrée dans l'historique personnel ;
3. le premier appel de la page envoie `restart_session: true` : une série
   interrompue est fermée et une nouvelle série commence ;
4. une même question ne peut pas apparaître deux fois dans la série actuelle ;
5. les questions jamais vues dans le cycle courant sont toujours prioritaires ;
6. s'il n'en reste pas assez pour remplir la série, le tirage réutilise des
   questions déjà vues ;
7. après 20 questions, une nouvelle série continue en donnant de nouveau la
   priorité aux questions restantes ;
8. lorsque toutes les questions ont été vues, le cycle est terminé et les
   séries suivantes peuvent repartir sur l'ensemble de la liste.

Corps du premier appel après l'ouverture de la page :

```json
{
  "restart_session": true
}
```

Les appels suivants utilisent `false`.

Exemple de réponse :

```json
{
  "exploration_id": "3f74c6ad-b023-47ca-8703-d4b191bc41b7",
  "question": {
    "id": "f3da04c4-1df4-4c93-a79b-03920266672f",
    "text": "Quelle est la capitale de la France ?",
    "image": null
  },
  "progress": {
    "viewed_count": 1,
    "total_count": 20,
    "percentage": 5.0
  },
  "list_progress": {
    "viewed_count": 23,
    "total_count": 48,
    "percentage": 47.92
  },
  "session_completed": false,
  "list_completed": false
}
```

## Tests

```bash
python manage.py test
```

Les tests couvrent l'authentification, les permissions, les abonnements, le
suivi d'utilisateurs, les recommandations, le tirage sans répétition et
l'isolation de l'historique entre utilisateurs.

Le frontend se valide avec :

```bash
cd frontend
npm run build
```
