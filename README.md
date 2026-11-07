# REMI pour Home Assistant — fork de Mins95

> Intégration **non officielle** du réveil connecté [UrbanHello Remi](https://www.urbanhello.com/) dans Home Assistant.

[![Ouvrir dans Marketplace](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=Mins95&repository=ha-remi&category=integration)

Ce fork est maintenu par [Mins95](https://github.com/Mins95), à partir de
[timoa/ha-remi](https://github.com/timoa/ha-remi). Il conserve le domaine de
l’intégration et les identifiants uniques des entités d’origine, ainsi que la
licence MIT et les crédits des auteurs.

La version maintenue se trouve sur `main`. Utilisez les versions publiées pour
les mises à jour. La branche `fix/remi-state-and-alarm-reliability` reste séparée
pour la [proposition de contribution au projet d’origine](https://github.com/timoa/ha-remi/pull/40).

Cette intégration communautaire n’est **ni affiliée à UrbanHello ni approuvée par UrbanHello**.

---

## Fonctionnalités

- **Capteurs** : température de la pièce, puissance du signal Wi-Fi, version du firmware, adresse IP, visage affiché
- **Capteurs binaires** : connexion, activité de l’appareil, disponibilité d’une mise à jour du firmware
- **Sélecteurs** : visage du réveil (éteint, éveillé, endormi, à moitié réveillé, souriant), format de l’heure (12 h ou 24 h), mode de lecture musicale
- **Curseurs** : volume, seuil d’alerte sonore, luminosité, luminosité du visage la nuit
- **Interrupteurs** : activation ou désactivation de chaque alarme
- **Horaires** : modification de l’heure et des minutes de chaque alarme dans Home Assistant
- **Lumière RGB** : couleur de fond de l’application
- **Gestion des alarmes** : création, modification et suppression via les services Home Assistant

---

## Prérequis

- Home Assistant 2024.1 ou une version plus récente
- Un compte UrbanHello, avec l’identifiant et le mot de passe utilisés dans l’application Remi

---

## Installation

### Home Assistant 2026.11 et versions suivantes : Marketplace

1. Ouvrez **Paramètres → Marketplace → Ajouter à partir d’un lien**.
2. Saisissez `https://github.com/Mins95/ha-remi`, puis sélectionnez **Ajouter**.
3. Connectez votre compte GitHub si Marketplace le demande : cette connexion est nécessaire pour les dépôts personnalisés.
4. Ouvrez **Remi (Mins95)** et installez la version publiée.
5. Redémarrez Home Assistant après la mise à jour d’une intégration déjà chargée.

Marketplace est intégré à Home Assistant depuis la version 2026.11 et remplace
HACS. Consultez la [documentation de Marketplace](https://www.home-assistant.io/integrations/marketplace/#custom-repositories).

### Anciennes versions de Home Assistant avec HACS

Ajoutez `https://github.com/Mins95/ha-remi` dans les **Dépôts personnalisés**, avec
le type **Intégration**, puis téléchargez la version publiée et redémarrez Home Assistant.

### Installations REMI existantes

Ce fork et le dépôt d’origine utilisent tous deux le domaine
`urbanhello_remi_unofficial`. Marketplace refuse l’installation simultanée de
deux dépôts fournissant le même domaine. Préservez votre configuration REMI
existante lors d’un changement de source du code. L’action **Supprimer et
désinstaller** de Marketplace supprime aussi la configuration, les appareils et
les entités associés ; elle ne sert pas à changer de dépôt source.

Ce dépôt est prêt à être ajouté depuis son URL. Le passage d’une installation
Marketplace existante à ce fork constitue une étape distincte. Préparer ou
publier ce fork ne modifie pas automatiquement le dépôt déjà installé.

### Installation manuelle

1. Copiez le dossier `custom_components/urbanhello_remi_unofficial/` dans le répertoire `config/custom_components/` de Home Assistant.
2. Redémarrez Home Assistant.

---

## Configuration

1. Ouvrez **Paramètres → Appareils et services → Ajouter une intégration**.
2. Recherchez **Remi**.
3. Saisissez l’**identifiant** et le **mot de passe** de votre compte UrbanHello.
4. L’intégration s’authentifie et découvre automatiquement votre Remi.

---

## Entités

| Entité | Type | Description |
|--------|------|-------------|
| Température | Capteur | Température de la pièce en °C |
| Signal Wi-Fi | Capteur | Puissance du signal RSSI en dBm |
| Version du firmware | Capteur | Version actuellement installée |
| Adresse IP | Capteur | Adresse IP locale |
| Visage actuel | Capteur | Nom du visage affiché |
| En ligne | Capteur binaire | État de connexion de l’appareil |
| Activité | Capteur binaire | État d’activité de l’appareil |
| Mise à jour du firmware disponible | Capteur binaire | Présence d’une mise à jour destinée à cet appareil |
| Vérifier le firmware | Bouton | Actualise les informations du firmware sans installer de mise à jour |
| Visage du réveil | Sélecteur | Modifie le visage affiché |
| Format de l’heure | Sélecteur | Format 12 h ou 24 h |
| Mode de lecture musicale | Sélecteur | Normal, piste unique, répétition d’une piste ou de la liste |
| Volume | Curseur numérique | Volume du haut-parleur, de 0 à 100 |
| Luminosité | Curseur numérique | Luminosité de l’éclairage supérieur, de 0 à 100 |
| Luminosité du visage la nuit | Curseur numérique | Luminosité du visage dans l’obscurité, de 1 à 10, comme dans l’application |
| Seuil d’alerte sonore | Curseur numérique | Seuil de déclenchement des notifications sonores, de 0 à 250 |
| Couleur de fond de l’application | Lumière | Couleur associée au REMI dans l’application officielle |
| Alarme, une par horaire | Interrupteur | Active ou désactive chaque alarme |
| Heure de l’alarme, une par horaire | Heure | Modifie l’horaire dans le fuseau horaire du REMI |

---

## Évolution des entités RGB

L’entité `App Background Color` règle la couleur associée à un REMI dans
l’application officielle UrbanHello. Elle reste une entité RGB de type `light`,
avec les mêmes identifiants et commandes. Les automatisations existantes
continuent de cibler la même entité. Home Assistant conserve les noms
personnalisés par l’utilisateur.

L’ancienne entité RGB `Night Light` a été supprimée. Les commandes envoyées à
`lightnight` n’avaient aucun effet physique observable sur les deux REMI testés,
équipés des firmwares 329 et 332. Ce champ était initialement absent sur l’un
des appareils et est apparu après des essais d’écriture RGB. Ces observations
ne permettent pas de conclure à sa prise en charge par d’autres modèles.
L’intégration n’écrit plus dans `lightnight` et ne supprime ni ne réinitialise
les valeurs déjà présentes sur les serveurs UrbanHello.

Au chargement, l’ancienne entité `Night Light` est retirée du registre des
entités de cette intégration. Supprimez ses références dans vos tableaux de
bord, scripts et automatisations. La couleur de fond de l’application ne
commande pas un éclairage physique.

## Réglages de luminosité et migration

### Luminosité du visage la nuit

Le curseur **Luminosité du visage la nuit** utilise la même échelle de **1 à 10**
que le réglage correspondant dans les paramètres de l’application REMI. Il
règle la luminosité du visage dans l’obscurité, conformément au
[guide UrbanHello](https://www.urbanhello.com/fr/faq/faqs/gerer-la-luminosite-de-remi).
Il est distinct du curseur **Luminosité** existant, gradué de **0 à 100**.

Le réglage est lu et écrit dans `light_min`. Une modification n’envoie que ce
champ, puis actualise l’état de l’appareil. Elle ne modifie ni le visage, ni
les horaires des alarmes, ni l’étalonnage de la lumière. Une valeur absente ou
invalide est affichée comme inconnue. L’entité est ajoutée automatiquement au
chargement du code mis à jour. Son effet sur un REMI physique n’a pas encore
été testé avec ce fork.

### Commande de luminosité existante

La luminosité est un curseur de type `number`, sur l’échelle REMI de 0 à 100,
comme le volume et le seuil d’alerte sonore. Il commande toujours le même
réglage `luminosity` de l’API.

Les versions précédentes exposaient ce réglage sous la forme d’une lumière
`light` à intensité variable. Auparavant, il apparaissait comme un `number`
nommé `Screen Brightness`, accompagné d’un capteur incorrectement étiqueté en
lux. Ces anciennes entités sont retirées du registre de l’intégration au
chargement. Les références présentes dans les automatisations ne sont pas
réécrites. Aucun capteur d’éclairement ambiant n’est fourni.

Modifiez les automatisations qui utilisaient `light.*_brightness` pour cibler
l’entité numérique affichée sur la page de votre REMI. Les identifiants varient
selon les installations ; ceux ci-dessous sont uniquement des exemples.

```yaml
# Avant
service: light.turn_on
target:
  entity_id: light.example_brightness
data:
  brightness_pct: 40
```

```yaml
# Maintenant
service: number.set_value
target:
  entity_id: number.example_brightness
data:
  value: 40
```

Le curseur utilise l’échelle REMI de 0 à 100 : une ancienne valeur
`brightness_pct` correspond donc au même nombre. La valeur `0` éteint
l’éclairage supérieur.

La mémorisation de la dernière intensité non nulle, propre à l’ancienne entité
`light`, a disparu. Le curseur n’a pas d’état marche/arrêt séparé : s’il est
réglé sur `0`, il reste à `0`. Dans les conditions d’état, utilisez sa valeur
de 0 à 100, au lieu de l’ancien attribut `brightness` de la lumière, qui allait
de 0 à 255. Supprimez les références à l’ancien capteur en lux ou remplacez-les
par celles d’un véritable capteur de lumière ambiante. Les valeurs historiques
ne sont ni converties ni réinterprétées.

Une valeur d’API absente, invalide ou hors plage laisse le curseur à l’état
inconnu ; aucune luminosité par défaut n’est inventée.

## Conversion de la température

La conversion en degrés Celsius est `(raw - 50) / 5`. Elle a été vérifiée dans
la version 3.4.23 de l’application Android fournie (`com.app.urbanhello`). Ainsi,
une valeur brute de `160` correspond à **22,0 °C**, et non à 20,0 °C.
L’intégration conserve les décimales et suggère un affichage avec une décimale.
L’application officielle tronque son affichage à l’entier. Conserver les
décimales ne garantit pas la précision physique du capteur. Les mesures
absentes ou invalides restent inconnues. La valeur brute et la formule de
conversion sont disponibles dans les attributs de diagnostic du capteur.

L’historique des températures n’est pas réécrit. Une variation du graphique au
moment de la mise à jour peut donc venir de la conversion corrigée, sans
changement réel de température dans la pièce. Les éléments vérifiés dans le
protocole figurent dans les [notes d’analyse](docs/protocol-3.4.23.json).

## Correction du mode de lecture musicale

L’application utilise `musicMode` pour le comportement de lecture : `0` = normal,
`1` = piste unique, `2` = répétition d’une piste, `3` = répétition de la liste.
Les anciens libellés `Off`, `Music` et `White Noise` étaient incorrects.
Le sélecteur conserve son identifiant unique, mais les automatisations qui
sélectionnent ou comparent les anciens noms d’options doivent être adaptées.
Ce réglage ne sélectionne pas de fichier audio et ne lance pas la lecture.

## État du firmware et reprise de connexion

L’alerte de firmware utilise l’indicateur `firmware_need_update` de l’appareil
ou la version cible `update_firmware_version` qui lui est attribuée. La version
par défaut du serveur est informative : elle ne prouve pas qu’une nouvelle
version a été attribuée à ce REMI. Si les informations propres à l’appareil
manquent, l’état est inconnu, sans annoncer de mise à jour.

L’alerte expose dans ses attributs la version installée, la version cible
attribuée et la version par défaut du serveur. Le bouton **Vérifier le firmware**
actualise les informations de l’appareil et du cloud, sans installer de firmware.
UrbanHello gère automatiquement les mises à jour habituelles lorsque REMI est
connecté au Wi-Fi. Consultez les
[instructions de mise à jour du fabricant](https://www.urbanhello.com/fr/faq/faqs/comment-mettre-a-jour-remi-manuellement-).

Les lectures du cloud utilisent un délai maximal de 15 secondes par requête et
jusqu’à trois tentatives en cas d’erreur de connexion ou de réponse HTTP
500/502/503/504. Les commandes envoyées à l’appareil, ainsi que la création ou
la suppression d’alarmes, ne sont pas rejouées automatiquement après ces
erreurs. Le renouvellement de session conserve le REMI sélectionné. Les services
d’alarme utilisent l’intégration actuellement chargée : un rechargement ne
laisse plus les actions rattachées à un ancien client.

La création d’une alarme sans sélection explicite d’appareil est possible
lorsqu’un seul REMI est chargé. Avec plusieurs appareils, elle échoue désormais
avec une erreur explicite au lieu de choisir silencieusement le premier. Les
actions de modification et de suppression retrouvent l’appareil chargé à partir
de l’identifiant de l’alarme.

## Validation

Avant l’ajout du réglage de luminosité du visage, les corrections de fiabilité
ont été testées avec Python 3.14.9 et Home Assistant 2026.10.4 : 248 tests
réussis, 2 ignorés et 1 réussite inattendue non bloquante (`XPASS`), avec une
couverture de 97,32 %. Le nouveau réglage ajoute des tests sur les valeurs
natives, les entrées invalides, l’envoi du seul champ concerné et l’appel du
service Home Assistant. Les procédures GitHub Actions **Tests** et **Release**
exécutent la suite complète pour les nouvelles versions.

Après installation et redémarrage complet sous Home Assistant 2026.11.0, un
REMI équipé du firmware 332 a indiqué 22,0 °C pour une température brute de 160,
aucune mise à jour de firmware en attente, les bons jours de la semaine et
quatre horaires d’alarme modifiables. Les identifiants d’entités, les horaires
et les états d’activation existants ont été conservés. Aucune erreur de
l’intégration n’a été observée dans les journaux de démarrage. Les écritures
d’alarmes ont été testées avec une API simulée ; les vérifications après
installation n’ont pas modifié les horaires de l’appareil physique.

## Services de gestion des alarmes

Les alarmes se gèrent avec les services Home Assistant, appelables depuis les
automatisations ou **Outils de développement → Actions**.

### `urbanhello_remi_unofficial.create_alarm`

| Champ | Obligatoire | Description |
|-------|-------------|-------------|
| `name` | ✅ | Nom de l’alarme |
| `time` | ✅ | Heure locale dans le fuseau horaire du REMI, par exemple `07:00` |
| `enabled` | — | Activation ou désactivation ; valeur par défaut : `true` |
| `repeat` | — | Jours de répétition : 0 = dimanche, 1 = lundi, …, 6 = samedi |
| `face_define` | — | Visage à afficher à l’heure de l’alarme, par exemple `FACE_DAY` |
| `volume` | — | Volume propre à cette alarme, de 0 à 100 |

Les entités d’heure et les services écrivent dans le tableau `event_time`
réellement utilisé par l’application. Les entrées combinant une date et une
heure au format ISO sont désormais refusées : ces alarmes utilisent une heure
locale, sans date UTC. Adaptez vos appels existants au format `HH:MM` ou
`HH:MM:00`. Les secondes non nulles sont refusées au lieu d’être ignorées.

Le tableau `recurrence` du cloud commence le lundi. Les attributs des alarmes
affichent maintenant les bons jours. La convention existante du service
(`repeat`, avec dimanche = 0) est conservée, puis convertie vers ce tableau.

### `urbanhello_remi_unofficial.update_alarm`

Mêmes champs que `create_alarm`, avec le champ obligatoire `event_id` en plus :
il correspond à l’`objectId` de l’alarme à modifier.

### `urbanhello_remi_unofficial.delete_alarm`

| Champ | Obligatoire | Description |
|-------|-------------|-------------|
| `event_id` | ✅ | L’`objectId` de l’alarme à supprimer |

---

## Crédits

Ce fork s’appuie sur [timoa/ha-remi](https://github.com/timoa/ha-remi), ainsi que
sur le travail de son auteur et de ses contributeurs.

L’intégration s’inspire également de
[Remi_UrbanHello_hass](https://github.com/pdruart/Remi_UrbanHello_hass), de
[@pdruart](https://github.com/pdruart), qui a apporté des éléments utiles sur
l’activation des alarmes et le réglage de luminosité.

## Développement et publication des versions

Créez vos branches de développement à partir de `main`, faites des commits
ciblés et ouvrez une pull request vers `Mins95/ha-remi`. Exécutez
`pytest --cov --cov-report=term-missing` avant de fusionner. La branche de
contribution au projet d’origine reste réservée à la pull request déjà ouverte.

Pour publier une version, préparez une modification relue du numéro de version
dans `manifest.json` et des notes dans `CHANGELOG.md`. Lorsque les vérifications
réussissent sur `main`, lancez la procédure GitHub Actions **Release** avec ce
numéro exact. Elle vérifie la version, exécute les tests et publie une version
GitHub correspondant au commit vérifié. Elle utilise le `GITHUB_TOKEN` standard
du dépôt et ne nécessite aucun identifiant du mainteneur d’origine.

---

## Avertissement

Cette intégration utilise l’API cloud officielle d’UrbanHello. Une modification
de cette API peut affecter son fonctionnement. Son utilisation se fait sous
votre responsabilité.

## Licence

MIT
