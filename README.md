# 🎨 DamaiTools — Color Mod & Crosshair Overlay

Un outil Windows pour modifier les couleurs de votre écran en temps réel et afficher un crosshair personnalisable.

---

## 📋 Prérequis

- **Windows 10 / 11**
- **Python 3.10 ou plus récent** → [Télécharger Python](https://www.python.org/downloads/)

---

## 🚀 Installation (étape par étape)

### 1. Télécharger le code

**Option A — Avec Git :**
```bash
git clone https://github.com/UnzarTools/DamaiToolsColors.git
cd DamaiToolsColors
```

**Option B — Sans Git :**
1. Cliquez sur le bouton vert **"Code"** en haut de cette page
2. Cliquez sur **"Download ZIP"**
3. Extrayez le ZIP où vous voulez

---

### 2. Installer les dépendances

Ouvrez un terminal (cmd ou PowerShell) dans le dossier du projet et exécutez :

```bash
pip install -r requirements.txt
```

---

### 3. Lancer le logiciel

```bash
python main.py
```

> ⚠️ **Important :** Le logiciel demande les droits **Administrateur** au démarrage (nécessaire pour modifier les couleurs de l'écran). Cliquez **Oui** dans la fenêtre UAC.

---

## 🖥️ Fonctionnalités

| Onglet | Description |
|---|---|
| **COLOR MOD** | Ajuste Saturation, Vibrance, Teinte, Température des couleurs |
| **CROSSHAIR** | Affiche un viseur personnalisable sur l'écran |

- 💾 **Profils** : Sauvegardez vos réglages sous un nom personnalisé
- 🔴 **Tray** : Le logiciel reste dans la barre des tâches quand vous fermez la fenêtre

---

## ❓ Problèmes fréquents

**"pip n'est pas reconnu"**
→ Réinstallez Python en cochant bien **"Add Python to PATH"** lors de l'installation.

**"Le logiciel plante au démarrage"**
→ Assurez-vous de le lancer avec les droits administrateur.

**"Les couleurs ne changent pas"**
→ Votre carte graphique ne supporte peut-être pas l'API utilisée. Les sliders seront grisés dans ce cas.
