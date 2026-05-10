import requests
from typing import Union
import json
from django.conf import settings
import re
import html
from urllib.parse import quote_plus
from requests.exceptions import RequestException
import logging
import tempfile
import os
from typing import Union
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# Configuration API Djelia - À configurer dans settings.py
DJELIA_API_KEY = getattr(settings, 'DJELIA_API_KEY', 'YOUR_API_KEY')
DJELIA_BASE_URL = getattr(settings, 'DJELIA_BASE_URL', 'https://api.djelia.cloud/v2/')

# Configuration API Maliba AI
MALIBA_ASR_URL = getattr(settings, 'MALIBA_ASR_URL', 'http://34.46.115.9:8080')
MALIBA_TTS_URL = getattr(settings, 'MALIBA_TTS_URL', 'http://34.46.115.9:8081')

# Dictionnaire de traduction simple pour le fallback
BAMARA_FRENCH_DICT = {
    "bana": "maladie",
    "toro": "souffrir",
    "dimi": "douleur",
    "farigan": "fièvre",
    "sokosoko": "toux",
    "kônôboli": "diarrhée",
    "fônô": "vomissement",
    "saingain": "fatigue",
    "koungolo dimi": "mal de tête",
    "kono dimi": "mal de ventre",
    "soumaya": "paludisme",
    "djoli daisai": "anémie",
    "kôkô bana": "hypertension",
    "soukoro bana": "diabète",
    "konomaya": "grossesse",
    "den": "enfant",
    "mogo koroba": "adulte",
    "tchôro ba": "vieux",
    "mousso": "femme",
    "tchai": "homme",
}

# Conseils médicaux de base
MEDICAL_ADVICE = {
    "fièvre": "En cas de fièvre, prenez du paracétamol et consultez un médecin si la fièvre persiste plus de 3 jours.",
    "douleur": "Pour la douleur, prenez des antalgiques et consultez un centre de santé si la douleur est intense.",
    "toux": "Pour la toux, buvez beaucoup d'eau et consultez un médecin si la toux persiste.",
    "diarrhée": "En cas de diarrhée, buvez beaucoup d'eau et prenez des sels de réhydratation.",
    "vomissement": "En cas de vomissement, évitez de manger et consultez un médecin si cela persiste.",
    "fatigue": "Reposez-vous bien et mangez équilibré. Consultez un médecin si la fatigue persiste.",
    "mal de tête": "Reposez-vous dans un endroit calme et prenez du paracétamol si nécessaire.",
    "mal de ventre": "Évitez les aliments gras et consultez un médecin si la douleur persiste.",
    "paludisme": "Consultez immédiatement un centre de santé pour un test de paludisme.",
    "anémie": "Mangez des aliments riches en fer et consultez un médecin.",
    "hypertension": "Réduisez votre consommation de sel et consultez régulièrement un médecin.",
    "diabète": "Surveillez votre glycémie et suivez les conseils de votre médecin.",
    "grossesse": "Consultez régulièrement votre sage-femme ou médecin.",
}

def fallback_translate(text, direction):
    """Traduction de fallback simple"""
    if direction == "bam-fra":
        # Traduction bambara vers français (simplifiée)
        for bam, fra in BAMARA_FRENCH_DICT.items():
            if bam in text.lower():
                return f"Vous avez mentionné '{fra}'. "
        return f"Vous avez dit: {text}. "
    elif direction == "fra-bam":
        # Traduction français vers bambara (simplifiée)
        return f"Conseil médical: {text}"
    return text

def fallback_medical_search(query):
    """Recherche médicale de fallback avec conseils de base"""
    query_lower = query.lower()
    
    # Conseils médicaux de base selon les symptômes
    if any(word in query_lower for word in ['fièvre', 'farigan', 'fever']):
        return "En cas de fièvre : 1) Reposez-vous bien 2) Buvez beaucoup d'eau 3) Prenez du paracétamol si nécessaire 4) Consultez un médecin si la fièvre persiste plus de 3 jours"
    
    elif any(word in query_lower for word in ['toux', 'sokosoko', 'cough']):
        return "Pour la toux : 1) Buvez du miel avec de l'eau chaude 2) Évitez les endroits froids 3) Consultez si la toux persiste plus d'une semaine"
    
    elif any(word in query_lower for word in ['douleur', 'dimi', 'pain']):
        return "Pour la douleur : 1) Reposez la zone douloureuse 2) Appliquez de la glace si c'est une blessure 3) Consultez un médecin pour un diagnostic précis"
    
    elif any(word in query_lower for word in ['diarrhée', 'kônôboli', 'diarrhea']):
        return "En cas de diarrhée : 1) Buvez beaucoup d'eau et de sels de réhydratation 2) Mangez léger (riz, banane) 3) Consultez si cela dure plus de 2 jours"
    
    else:
        return "Pour vos symptômes, je recommande de : 1) Consulter un médecin pour un diagnostic précis 2) Suivre les conseils médicaux 3) Prendre les médicaments prescrits"

def fallback_transcribe(audio_file):
    """Transcription de fallback - retourne un message d'aide"""
    return "Audio reçu. Veuillez décrire vos symptômes en texte pour recevoir des conseils médicaux."

def fallback_synthese(text):
    """Synthèse vocale de fallback - retourne None"""
    return None

def convert_audio_to_mono_16k(input_file, output_file=None):
    """
    Convertit un fichier audio en mono 16kHz WAV
    input_file: chemin du fichier d'entrée ou objet fichier
    output_file: chemin du fichier de sortie (optionnel)
    """
    try:
        # Créer un fichier temporaire si output_file n'est pas spécifié
        if output_file is None:
            temp_dir = tempfile.gettempdir()
            output_file = os.path.join(temp_dir, f"converted_{os.path.basename(str(input_file))}.wav")
        
        # Si c'est un objet fichier, le sauvegarder temporairement
        if hasattr(input_file, 'read'):
            temp_input = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_input.write(input_file.read())
            temp_input.close()
            input_path = temp_input.name
        else:
            input_path = str(input_file)
        
        # Conversion avec ffmpeg
        cmd = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", input_path,
            "-ac", "1",       # 1 canal (mono)
            "-ar", "16000",   # 16 kHz
            "-f", "wav",      # Format WAV
            output_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Nettoyer le fichier temporaire si créé
        if hasattr(input_file, 'read') and os.path.exists(input_path):
            os.unlink(input_path)
        
        if result.returncode == 0:
            logger.info(f"Conversion audio réussie: {output_file}")
            return output_file
        else:
            logger.error(f"Erreur conversion audio: {result.stderr}")
            return None
            
    except Exception as e:
        logger.error(f"Erreur lors de la conversion audio: {str(e)}")
        return None

def load_robotmali_model():
    """
    Charge le modèle RobotMali QuartzNet
    Retourne le modèle ou None si erreur
    """
    try:
        import nemo.collections.asr as nemo_asr
        model = nemo_asr.models.EncDecCTCModel.from_pretrained(
            model_name="RobotsMali/stt-bm-quartznet15x5-V0"
        )
        logger.info("Modèle RobotMali QuartzNet chargé avec succès")
        return model
    except Exception as e:
        logger.error(f"Erreur lors du chargement du modèle RobotMali: {str(e)}")
        return None

# Variable globale pour le modèle
_robotmali_model = None

def get_robotmali_model():
    """Retourne le modèle RobotMali (singleton)"""
    global _robotmali_model
    if _robotmali_model is None:
        _robotmali_model = load_robotmali_model()
    return _robotmali_model

# ASR avec QuartzNet de RobotMali
###


def synthese(text, lang='bam_Latn'):
    """
    Synthèse vocale via l'API Maliba AI
    """
    try:
        url = MALIBA_TTS_URL + '/tts'
        headers = {"Content-Type": "application/json"}
        data = {
            "text": text,
            "voice": "seydou"  # Voix par défaut
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=60)
        
        if response.ok:
            result = response.json()
            audio_b64 = result.get('audio', None)
            if audio_b64:
                import base64
                return base64.b64decode(audio_b64)
            else:
                logger.error("Réponse TTS Maliba sans audio.")
                return fallback_synthese(text)
        else:
            logger.error(f"Erreur API Maliba TTS: {response.status_code} - {response.text}")
            return fallback_synthese(text)
    except Exception as e:
        logger.error(f"Erreur lors de la synthèse vocale Maliba: {str(e)}")
        return fallback_synthese(text)

# Traduction (format JSON clé/valeur)
def traduire(text, direction):
    """
    Traduit un texte entre bambara et français
    TEMPORAIREMENT: Utilise le fallback en attendant la résolution du problème SSL
    """
    # TEMPORAIRE: Utiliser le fallback en attendant la résolution du problème SSL
    logger.warning("API Djelia temporairement indisponible - utilisation du fallback")
    return fallback_translate(text, direction)

# Recherche médicale via DuckDuckGo
def duckduck_medical_search(query):
    """
    Recherche des informations médicales fiables
    query: requête de recherche
    """
    try:
        # Recherche sur des sites médicaux fiables
        medical_sites = "site:who.int OR site:unicef.org OR site:msf.org OR site:vidal.fr"
        search_query = f"{query} {medical_sites}"
        url = f'https://duckduckgo.com/html/?q={quote_plus(search_query)}'
        
        response = requests.get(url, timeout=30)
        
        if response.ok:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.find_all('a', class_='result__a')
            
            if results:
                return results[0].get_text().strip()
        
        # Fallback vers la recherche locale si DuckDuckGo échoue
        return fallback_medical_search(query)
        
    except Exception as e:
        logger.error(f"Erreur lors de la recherche médicale: {str(e)}")
        return fallback_medical_search(query)

def recherche_pipeline(sympt_input, user=None, is_audio=False):
    """
    Pipeline complet de traitement médical:
    1. Transcription si audio (RobotMali QuartzNet)
    2. Traduction en français
    3. Recherche médicale
    4. Traduction des résultats
    5. Synthèse vocale (MALIBA-AI TTS)
    """
    try:
        # Étape 1: Transcription si audio
        if is_audio:
            sympt_bam = transcrire(sympt_input)
            logger.info(f"Transcription audio (RobotMali): {sympt_bam}")
        else:
            sympt_bam = sympt_input
        
        if not sympt_bam or sympt_bam.startswith("Erreur"):
            return {
                "success": False,
                "error": "Impossible de traiter l'audio ou le texte fourni",
                "symptomes_bam": sympt_bam,
                "symptomes_fr": "",
                "reponse_bam": "Veuillez réessayer avec un enregistrement plus clair."
            }
        
        # Étape 2: Traduction en français
        sympt_fr = traduire(sympt_bam, "bam-fra")
        logger.info(f"Traduction en français: {sympt_fr}")
        
        # Étape 3: Recherche médicale
        conseils_fr = duckduck_medical_search(sympt_fr)
        logger.info(f"Recherche médicale: {conseils_fr[:100]}...")
        
        # Étape 4: Traduction des résultats
        reponse_bam = traduire(conseils_fr, "fra-bam")
        logger.info(f"Traduction réponse: {reponse_bam[:100]}...")
        
        # Étape 5: Synthèse vocale (MALIBA-AI)
        audio_bytes = synthese(reponse_bam)
        
        # Sauvegarde en base si utilisateur authentifié
        recherche = None
        if user and user.is_authenticated:
            from .models import Recherche
            from django.core.files.base import ContentFile
            
            recherche = Recherche.objects.create(
                user=user,
                audio=sympt_input if is_audio else None,
                symptomes_bam=sympt_bam,
                symptomes_fr=sympt_fr,
                reponse_bam=reponse_bam
            )
            
            if audio_bytes:
                fname = f"reponses/{reponse_bam[:50]}_{user.id}.wav".replace(" ", "_")
                recherche.reponse_mp3.save(fname, ContentFile(audio_bytes))
                recherche.save()
        
        return {
            "success": True,
            "symptomes_bam": sympt_bam,
            "symptomes_fr": sympt_fr,
            "reponse_bam": reponse_bam,
            "audio_url": recherche.reponse_mp3.url if recherche and audio_bytes else None,
            "recherche_id": recherche.id if recherche else None
        }
    
    except Exception as e:
        logger.error(f"Erreur dans le pipeline de recherche: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "symptomes_bam": "",
            "symptomes_fr": "",
            "reponse_bam": "Une erreur est survenue lors du traitement. Veuillez réessayer."
        }



def transcrire(audio_file, lang='bam_Latn'):
    """
    Transcrit un fichier audio en texte en utilisant le serveur RobotMali sur Colab.
    """
    try:
        # Sauvegarder l'audio temporairement si c'est un fichier en mémoire
        if hasattr(audio_file, 'read'):
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
                tmp.write(audio_file.read())
                tmp_path = tmp.name
        else:
            tmp_path = audio_file

        # Lire le fichier audio et encoder en base64
        with open(tmp_path, 'rb') as f:
            audio_bytes = f.read()
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

        # Construire la requête vers le serveur Colab
        url = getattr(settings, 'ROBOTMALI_ASR_URL', '') + '/transcribe'
        headers = {"Content-Type": "application/json"}
        data = {"audio_data": audio_b64}

        response = requests.post(url, headers=headers, json=data, timeout=60)
        if response.ok:
            result = response.json()
            return result.get('transcription', '')
        else:
            return f"Erreur RobotMali: {response.status_code} - {response.text}"

    except Exception as e:
        return f"Erreur lors de la transcription RobotMali : {str(e)}"

def text_to_speech_bambara(
    text: str,
    server_url: str = "http://34.46.115.9:8081",
    speaker_id: str = "Seydou",
    temperature: float = 0.8,
    top_k: int = 50,
    top_p: float = 1.0,
    max_new_audio_tokens: int = 2048
) -> Union[str, bytes]:
    """
    Convertit du texte bambara en audio (WAV) via l’API MALIBA-AI Bambara TTS.
    """
    endpoint = f"{server_url}/predict"
    payload = {
        "text": text,
        "speaker_id": speaker_id,
        "temperature": temperature,
        "top_k": top_k,
        "top_p": top_p,
        "max_new_audio_tokens": max_new_audio_tokens
    }
    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=180)
        if response.status_code == 200:
            return response.content  # audio WAV
        else:
            try:
                error_detail = response.json().get('detail', 'Unknown error')
                return f"Error: Server returned status code {response.status_code}. Detail: {error_detail}"
            except:
                return f"Error: Server returned status code {response.status_code}. Response: {response.text}"
    except requests.exceptions.Timeout:
        return "Error: Request timed out after 60 seconds"
    except requests.exceptions.ConnectionError:
        return f"Error: Cannot connect to TTS server at {server_url}"
    except requests.exceptions.RequestException as e:
        return f"Request error: {e}"