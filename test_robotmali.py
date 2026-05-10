#!/usr/bin/env python3
"""
Test simple du modèle RobotMali QuartzNet
"""

import nemo.collections.asr as nemo_asr
import os

def test_robotmali_model():
    """Test du chargement et de l'utilisation du modèle RobotMali"""
    
    print("🔄 Chargement du modèle RobotMali...")
    
    try:
        # Charger le modèle RobotMali
        asr_model = nemo_asr.models.EncDecCTCModel.from_pretrained(
            model_name="RobotsMali/stt-bm-quartznet15x5-V0"
        )
        print("✅ Modèle RobotMali chargé avec succès !")
        
        # Test avec un fichier audio (si disponible)
        test_audio_path = "test_audio.wav"  # Remplace par le chemin de ton fichier audio
        
        if os.path.exists(test_audio_path):
            print(f"🎵 Test de transcription avec {test_audio_path}...")
            result = asr_model.transcribe([test_audio_path])
            print(f"📝 Transcription : {result}")
        else:
            print("⚠️  Aucun fichier audio de test trouvé.")
            print("   Place un fichier audio nommé 'test_audio.wav' dans ce dossier pour tester.")
            
    except Exception as e:
        print(f"❌ Erreur lors du chargement du modèle : {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("🧪 Test du modèle RobotMali QuartzNet")
    print("=" * 50)
    
    success = test_robotmali_model()
    
    if success:
        print("\n✅ Test réussi ! Le modèle fonctionne.")
    else:
        print("\n❌ Test échoué. Vérifie les erreurs ci-dessus.") 