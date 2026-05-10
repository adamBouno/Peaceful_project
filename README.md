#peaceful_project en bambara HAKILILATIKAI 

**HAKILILATIKAI** est une plateforme médicale innovante qui facilite l’accès à l’information de santé grâce à l’intelligence artificielle et au traitement multilingue.

Elle permet aux utilisateurs de décrire leurs symptômes en **bambara ou en français**, et d’obtenir des conseils médicaux fiables, des centres de santé proches et des rappels de médicaments.

---

##  Vision du projet

Rendre l'information médicale accessible à tous, dans la langue de son choix, grâce à la voix et à l'intelligence artificielle.

Nous croyons que la santé ne devrait pas avoir de barrière linguistique et que chaque personne mérite d’avoir accès à des conseils fiables, peu importe sa langue maternelle.

---

##  Fonctionnalités

-  Description des symptômes en bambara ou français
-  Analyse intelligente des symptômes (IA / pipeline)
-  Recherche de centres médicaux proches
-  Gestion des rappels de médicaments
-  Articles et conseils médicaux
-  Gestion des profils utilisateurs
-  (optionnel) Support vocal

---

## Technologies utilisées

- Django (Backend Web)
- Django REST Framework (API)
- Python
- SQLite / PostgreSQL
- JavaScript (frontend)
- IA / NLP (pipeline de traitement des symptômes)

---


---

## ⚠️ Fichiers à ne PAS utiliser en production

Ces fichiers sont uniquement pour tests / expérimentation :

- `GUIDE_EXPOSITION_PUBLIQUE.md`
- `README_COLAB_WORKING.md`
- `colab_robotmali_working.py`

👉 Ils ne doivent pas être utilisés dans le déploiement final.

---

##  Lancer le projet

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
