import hashlib
import json
import sys
from datetime import datetime


def pseudonymize_data(data):
    """
    Pseudonymise les données sensibles du dataset utilisateur.
    Applique un hachage cryptographique (SHA-256) avec un sel secret.
    """
    # Sel secret (doit être stocké de manière sécurisée)
    SECRET_SALT = "votre_sel_secret_très_long_et_aléatoire_2025"

    def hash_value(value):
        """Hachage sécurisé d'une valeur avec le sel"""
        if isinstance(value, str):
            return hashlib.sha256((value + SECRET_SALT).encode('utf-8')).hexdigest()
        return value

    def mask_credit_card(number):
        """Masque les chiffres sensibles d'une carte bancaire"""
        cleaned = number.replace('-', '')
        return 'XXXX-XXXX-XXXX-' + cleaned[-4:]

    # Parcours récursif des données
    if isinstance(data, list):
        return [pseudonymize_data(item) for item in data]

    if isinstance(data, dict):
        pseudonymized = {}
        for key, value in data.items():
            if key in ['name', 'email', 'phone']:
                # Pseudonymisation des identifiants
                pseudonymized[key] = hash_value(str(value))
            elif key == 'address' or key == 'shipping_address':
                # On garde le code postal pour l'analyse géographique
                parts = value.split(',')
                if len(parts) >= 2:
                    postal_code = parts[1].strip().split()[0]  # Extrait le code postal
                    country = parts[1].strip().split()[1]
                    pseudonymized[key] = hash_value(parts[0]) + ', ' + postal_code + ' ' + country
                else:
                    pseudonymized[key] = hash_value(value)
            elif key == 'national_id':
                # Remplace par un identifiant anonyme basé sur l'ID national
                pseudonymized[key] = hash_value(str(value))[:16]
            elif key == 'payment_methods':
                # Anonymisation des méthodes de paiement
                masked_methods = []
                for method in value:
                    masked_method = method.copy()
                    if method.get('type') == 'credit_card':
                        masked_method['number'] = mask_credit_card(method['number'])
                        masked_method['cvv'] = 'XXX'
                        if 'billing_address' in masked_method:
                            masked_method['billing_address'] = hash_value(masked_method['billing_address'])
                    elif method.get('type') == 'paypal':
                        masked_method['email'] = hash_value(method['email'])
                    masked_methods.append(masked_method)
                pseudonymized[key] = masked_methods
            elif key == 'number' and 'card' in str(data.get('type', '')):
                # Protection des numéros de carte
                pseudonymized[key] = mask_credit_card(value)
            elif key == 'cvv':
                # Suppression totale des CVV
                pseudonymized[key] = None  # ou ""
            elif key == 'audio_recording_id':
                # Hachage des identifiants audio
                pseudonymized[key] = hash_value(value)
            else:
                # Récursion pour les autres champs
                pseudonymized[key] = pseudonymize_data(value)
        return pseudonymized

    # Pour les valeurs primitives
    return data


def main():
    if len(sys.argv) != 3:
        print("Usage: python pseudonymize.py <input_file.json> <output_file.json>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    try:
        # Lecture du fichier d'entrée
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Pseudonymisation
        print("Pseudonymisation des données en cours...")
        anonymized_data = pseudonymize_data(data)

        # Écriture du fichier de sortie
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(anonymized_data, f, indent=2, ensure_ascii=False)

        print(f"Données pseudonymisées écrites dans '{output_file}'")

    except FileNotFoundError:
        print(f"Erreur : Le fichier '{input_file}' est introuvable.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Erreur : Le fichier n'est pas un JSON valide. {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Erreur inattendue : {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
