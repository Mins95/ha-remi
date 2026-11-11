## 0.5.4 — Temporiser les erreurs de lecture du firmware (2026-11-11)

- Après un échec de lecture des informations firmware, attendre cinq minutes avant la prochaine tentative automatique, y compris après un échec au démarrage ou via le bouton de vérification.
- Pendant cette attente, continuer à actualiser l’appareil et ses alarmes toutes les 60 secondes, en conservant les dernières informations firmware reçues.
- Le bouton de vérification permet toujours une tentative immédiate. Une lecture réussie rétablit l’intervalle normal d’une heure ; les erreurs d’authentification restent signalées.
- Correctif adapté du travail publié dans [timoa/ha-remi #40](https://github.com/timoa/ha-remi/pull/40), avec tests de non-régression et documentation actualisée.

Après installation, redémarrer Home Assistant. Les entités, automatisations et
la carte existantes sont conservées.

## 0.5.3 — Libellés de luminosité de la veilleuse (2026-11-08)

- Le curseur 0–100 est nommé « Luminosité de la veilleuse » dans la carte, son éditeur, l’entité numérique et les actions d’alarmes/minuteurs ; les libellés anglais sont également corrigés.
- La lumière facultative avec mémoire de luminosité est nommée « Veilleuse ».
- Le curseur inférieur est nommé simplement « Luminosité du visage » ; son fonctionnement et son échelle 1–10 sont conservés. Les identifiants, valeurs, commandes et noms personnalisés sont conservés.
- Documentation harmonisée ; crédits et compteur de téléchargements conservés.

Après installation, redémarrer Home Assistant puis recharger la page ou
l’application Companion pour charger les nouveaux libellés.

## 0.5.2 — Alarmes stables, éclairage mémorisé et carte configurable (2026-11-07)

- Conservation des identifiants Home Assistant lorsqu’une alarme est recréée dans le cloud, grâce à une correspondance persistante par appareil. Les noms ambigus ne sont jamais associés automatiquement.
- Les commandes et l’éditeur de la carte suivent l’identifiant cloud actuel de l’alarme, même après une reconnexion ou un redémarrage.
- Nouvelle entité Éclairage facultative : marche/arrêt, variateur et restauration de la dernière luminosité confirmée, sans modifier le visage ni remplacer les entités existantes.
- Éditeur visuel de la carte enrichi pour afficher ou masquer les commandes, la température, la connexion, la musique et les onglets secondaires. L’affichage existant reste le choix par défaut.
- Diagnostics de connexion téléchargeables sans identifiants de compte, appareil, réseau ou horaires. Deux capteurs diagnostiques facultatifs exploitent les valeurs signalées par le Rémi lorsqu’elles existent ; les données absentes restent inconnues.

Home Assistant 2026.11.0 minimum. Installer la mise à jour, redémarrer Home
Assistant puis recharger la page ou l’application Companion. Conserver
l’intégration et la carte existantes. La protection des alarmes commence avec
le premier instantané mémorisé ; une rotation et un renommage simultanés ne
peuvent pas être rapprochés avec certitude.

## 0.5.1 — Bilans de sommeil et historique corrigés (2026-11-07)

- Sélection parmi 60 journaux cloud disponibles, avec une période du jour précédent au jour indiqué. Les valeurs et les courbes de la carte restent rattachées au même journal.
- Date du dernier export cloud distincte de la période enregistrée. Les capteurs natifs privilégient le dernier bilan terminé disposant d’une estimation de sommeil valide.
- Score et durée de sommeil à zéro affichés comme indisponibles, conformément à l’application ; minuit reste une heure valide.
- Les octets zéro ambigus des courbes de température restent des trous, sans fausse mesure à −10 °C ni ligne reliant les données manquantes. Les zéros de bruit et de lumière restent valides.
- Bouton Actualiser : demande explicite d’export au Rémi, attente de 12 secondes puis relecture du cloud, avec un délai minimal de 60 secondes entre deux commandes. Aucun export automatique.
- Action `get_history` enrichie : catalogue sans courbes, sélection par `report_id`, relecture cloud avec `refresh` et demande d’export facultative avec `sync`.

La demande d’export a été vérifiée sur un Rémi physique et a actualisé son
journal courant. Elle ne garantit pas la récupération des jours manquants.
Après installation, redémarrer Home Assistant puis recharger la page ou
l’application Companion. La carte existante et les identifiants d’entités
sont conservés.

## 0.5.0 — Carte Rémi et fonctions cloud, version stable (2026-11-07)

**Home Assistant 2026.11.0 minimum.** Installer la mise à jour, redémarrer
Home Assistant puis recharger la page ou l’application Companion. Depuis
0.4.0 ou les bêtas 0.5.0, conserver l’intégration et la carte existantes :
les identifiants d’entités et la configuration du tableau de bord sont préservés.

- Passage de la série 0.5.0 en version stable, disponible sans activer les préversions dans Marketplace ou HACS.
- Carte intégrée avec quatre onglets : Rémi, Horaires, Sommeil et Minuteurs. Commande Allumé/Éteint du visage, choix directs Réveillé/Endormi, musique repliée par défaut et mises à jour automatiques des ressources.
- Alarmes avec horaires lisibles, édition de la luminosité et des paramètres musicaux ; lecteur musical, bibliothèque et cinq profils de minuteur enregistrés.
- Bilans de sommeil datés et courbes de température, bruit et lumière à la demande ; température en direct avec décimales.
- Fiabilité du compte, des lectures cloud et de la détection des entités conservée depuis les bêtas ; interface française et anglaise selon Home Assistant.
- README raccourci avec une capture réelle de la carte, badge de téléchargements et guides détaillés pour l’installation, les actions, les migrations et le développement.
- Archive ZIP de l’intégration générée et contrôlée avant publication, utilisée par Marketplace et HACS. Le compteur GitHub suit les téléchargements de ces archives, sans reprendre les anciens téléchargements de sources.

Les limites du protocole restent documentées : le cloud ne confirme pas la
lecture audio et peut publier des bilans anciens ; les minuteurs se démarrent
avec le bouton du Rémi. La mise à jour du firmware et l’audio du babyphone
ne sont pas fournis. La validation des commandes sur un appareil physique
reste distincte des tests automatisés sous Home Assistant 2026.11.0.

## 0.5.0-beta.2 — Commandes du visage simplifiées (2026-11-07)

- Onglet « Rémi » plus compact, avec une commande pour allumer ou éteindre l’affichage du visage et deux choix directs : « Réveillé » et « Endormi ».
- Le rallumage retrouve le dernier visage non éteint connu par la carte pour cet appareil, ou choisit « Réveillé » si aucun n’est connu. Cette commande agit sur l’affichage du visage, pas sur l’alimentation du Rémi.
- Section « Musique » repliée par défaut ; ses commandes restent accessibles en la dépliant.
- Les cinq expressions restent disponibles dans « Autres réglages ». Le dessin distingue le visage à moitié éveillé du visage endormi ; un état inconnu n’affiche plus de visage inventé.

Après installation, redémarrer Home Assistant puis recharger la page ou
l’application Companion pour charger la nouvelle carte. Les identifiants
d’entités et la configuration des tableaux de bord sont conservés.
Cette préversion reste facultative ; la version 0.4.0 demeure la dernière version stable.

## 0.5.0-beta.1 — Carte Rémi, musique et sommeil (2026-11-07)

- Nouvelle carte de tableau de bord inspirée de Rémi : visage, température avec décimales, commandes et quatre onglets « Rémi », « Horaires », « Sommeil » et « Minuteurs ». Interface française ou anglaise selon Home Assistant, adaptée aux thèmes clair et sombre.
- Carte livrée avec l’intégration : enregistrement automatique de sa ressource, version et empreinte des sources pour renouveler le cache. Après une mise à jour et le redémarrage de Home Assistant, recharger la page ou l’application Companion. Les tableaux de bord existants ne sont pas modifiés automatiquement.
- Détection des entités à partir des registres Home Assistant, y compris après leur renommage. Choix explicite de l’appareil lorsqu’il y a plusieurs Rémi.
- Horaires classés par heure dans la carte ; les interrupteurs natifs affichent également « 07:30 · Nom de l’alarme ». Les identifiants existants et les noms personnalisés sont conservés.
- Édition des alarmes enrichie : luminosité, fichier musical, durée et bouton de lecture. Les modifications partielles préservent les autres réglages ; les formats de commande inconnus sont refusés pour éviter de les remplacer arbitrairement.
- Lecteur musical avec bibliothèque du Rémi, lecture, pause, arrêt, piste précédente/suivante, volume et répétition. L’état de lecture reste inconnu lorsque le cloud ne le confirme pas ; « Lire » relance le fichier sélectionné.
- Cinq capteurs de sommeil et consultation des courbes de température, bruit et lumière, chargées à la demande. La date et l’ancienneté du bilan restent visibles. Le bruit et la lumière n’ont pas d’unité physique étalonnée.
- Gestion des cinq profils de minuteur : consultation, création, modification et suppression. Leur lancement se fait avec le bouton physique du Rémi ; aucun faux compte à rebours n’est affiché.
- Reconnexion du compte sans recréer l’appareil, récupération complète des alarmes et isolation des erreurs : un échec de lecture des horaires ou de l’historique ne supprime pas les entités et ne bloque pas les autres commandes disponibles.
- Environnement de validation ciblé sur Home Assistant 2026.11.0 et Python 3.14.10.

**Version bêta :** activer l’affichage des préversions dans le Marketplace/HACS
pour la sélectionner. La version 0.4.0 reste la dernière version stable.
Les nouvelles écritures musicales, d’alarme et de minuteur sont vérifiées avec
des réponses API simulées ; leur effet physique n’a pas encore été validé sur
un Rémi. Un bilan cloud peut avoir plusieurs jours : il n’est jamais présenté
comme une mesure en direct.

## 0.4.0 — Langue de Home Assistant et nouvelle présentation (2026-11-07)

- Traduction complète en français et en anglais des noms d'entités, des états, des choix, des formulaires, des actions et des erreurs affichées par l'intégration.
- Utilisation des traductions natives de Home Assistant ; les noms personnalisés et les noms d'alarmes définis dans l'application Rémi sont conservés.
- Conservation des identifiants uniques et des identifiants des entités existantes lors de la mise à jour.
- Refonte du README en anglais, avec une bannière, une photo officielle du Rémi, des badges et une documentation détaillée.

**Adaptation des automatisations :** les valeurs internes des visages et des modes
musicaux deviennent des codes indépendants de la langue. Les menus affichent
toujours leur traduction. Dans les appels `select.select_option`, les modèles et
les conditions portant sur ces états, remplacer les anciens libellés comme
`Awake`, `Sleepy` ou `Repeat playlist` par `awake`, `sleepy` ou `repeat_playlist`.
La liste complète figure dans [le guide de migration](docs/usage.md#040-translated-interface-and-stable-state-codes).
Les constantes `FACE_*` des actions d'alarme restent acceptées.

## 0.3.0 — Fork Mins95 (2026-11-07)

- Correction de la température, en conservant les décimales.
- Détection des mises à jour du firmware à partir des informations propres au Rémi, avec un bouton de vérification.
- Reprises limitées des lectures cloud et récupération de session, sans répéter les écritures après une erreur temporaire.
- Correction des jours et des commandes d'alarme ; ajout d'un réglage de l'heure pour chaque alarme.
- Correction des libellés des modes de lecture musicale.
- Ajout du curseur « Luminosité du visage la nuit », de 1 à 10, comme dans l'application Rémi.
- Préparation du fork pour le Marketplace, avec ses propres liens de support et son processus de publication.

Les identifiants des entités existantes et les alarmes configurées sont conservés.
Les services d'alarme attendent désormais `HH:MM` ou `HH:MM:00` : les automatisations
utilisant des dates ISO ou les anciens libellés musicaux doivent être adaptées.

Validation : 284 tests réussis, 2 ignorés et 1 réussite inattendue d'un test marqué
non bloquant ; couverture de 97,36 %. Les correctifs précédents ont aussi été
vérifiés sur Home Assistant 2026.11.0 avec un Rémi en firmware 332. Les écritures
d'alarme, la lecture musicale et l'effet physique du nouveau réglage de luminosité
n'ont pas été testés sur cet appareil.

## [0.2.7](https://github.com/timoa/ha-remi/compare/0.2.6...0.2.7) (2026-11-05)


### Bug Fixes

* **hacs:** declare the integration category ([2181824](https://github.com/timoa/ha-remi/commit/2181824caba61bd31f977e9b45afbd8662c5e5d2))

## [0.2.6](https://github.com/timoa/ha-remi/compare/0.2.5...0.2.6) (2026-11-05)


### Bug Fixes

* expose REMI brightness as a slider ([7349f8e](https://github.com/timoa/ha-remi/commit/7349f8edcc4871905464a08b904d1aa84e261fc7))

## [0.2.5](https://github.com/timoa/ha-remi/compare/0.2.4...0.2.5) (2026-11-05)


### Bug Fixes

* **renovate:** drop invalid "*" from matchPackageNames matcher ([3a2044a](https://github.com/timoa/ha-remi/commit/3a2044a8f0062f1691bc6c12bffc5e80d8791cc1)), closes [#19](https://github.com/timoa/ha-remi/issues/19)

## [0.2.4](https://github.com/timoa/ha-remi/compare/0.2.3...0.2.4) (2026-11-05)


### Bug Fixes

* expose REMI brightness as a dimmable light ([52979e5](https://github.com/timoa/ha-remi/commit/52979e5b1c5eaeec161cb8fd7b63b82c858e1052))

## [0.2.3](https://github.com/timoa/ha-remi/compare/0.2.2...0.2.3) (2026-11-05)


### Bug Fixes

* remove ineffective RGB night light and clarify app color ([2729ffd](https://github.com/timoa/ha-remi/commit/2729ffdf579c7a09d037938d0413ffb65418ad09))

## [0.2.2](https://github.com/timoa/ha-remi/compare/0.2.1...0.2.2) (2026-11-05)


### Bug Fixes

* allow REMI noise alert thresholds up to 250 ([4ec29cd](https://github.com/timoa/ha-remi/commit/4ec29cd67519879d7cafe187f163a565dbea63f2))

## [0.2.1](https://github.com/timoa/ha-remi/compare/0.2.0...0.2.1) (2026-11-05)


### Bug Fixes

* correct REMI temperature conversion ([deb02dc](https://github.com/timoa/ha-remi/commit/deb02dcd28c8edb65073e97a09129d6f255d6768))

# [0.2.0](https://github.com/timoa/ha-remi/compare/0.1.9...0.2.0) (2026-03-05)


### Bug Fixes

* **cicd:** add extra_plugins to semantic-release action ([f939d3a](https://github.com/timoa/ha-remi/commit/f939d3a1546b2ae806d609cbca160ddf9b0a5ef5))
* **cicd:** fix the Semantic Release command + remove unused package.json ([a9bc823](https://github.com/timoa/ha-remi/commit/a9bc823a8bcb5e20e9c7f0d89f42f512d3eddc01))
* **hacs:** fix the manifest.json for HACS Store ([26ddf91](https://github.com/timoa/ha-remi/commit/26ddf9179b29e58fb21ccfb08d51096d08803972))
* **project:** fix the Semantic release issue ([b2aaf2c](https://github.com/timoa/ha-remi/commit/b2aaf2cf6c6180044325efd239986707fcb74f35))


### Features

* **hacs:** add checks for the HACS store ([055ae22](https://github.com/timoa/ha-remi/commit/055ae2254ae8b69def9a2b02a4dd21574caa6956))

## [0.1.9](https://github.com/timoa/ha-remi/compare/0.1.8...0.1.9) (2026-03-03)


### Bug Fixes

* **brand:** add the new logo and icons for HA 2026.3 version ([f5ae6d3](https://github.com/timoa/ha-remi/commit/f5ae6d3a69c162b956f7c5ae7b5dff95105c2dd9))

## [0.1.8](https://github.com/timoa/ha-remi/compare/0.1.7...0.1.8) (2026-02-21)


### Bug Fixes

* **docs:** update the README ([f749427](https://github.com/timoa/ha-remi/commit/f749427bbf4a3052c10b5b063aed8b713d118d77))

## [0.1.7](https://github.com/timoa/ha-remi/compare/0.1.6...0.1.7) (2026-02-21)


### Bug Fixes

* **i18n:** rename Screen Brightness to Brightness ([2f8cb0f](https://github.com/timoa/ha-remi/commit/2f8cb0f7c379a0fbf422b79c48b0f626ae2cc3f1))
* **tests:** add missing tests ([a7c00f9](https://github.com/timoa/ha-remi/commit/a7c00f9d8839c1d3956480809b2e350175b44c27))

## [0.1.6](https://github.com/timoa/ha-remi/compare/0.1.5...0.1.6) (2026-02-20)


### Bug Fixes

* **integration:** rename the integration "urbanhello_remi_unofficial" ([a28bbfc](https://github.com/timoa/ha-remi/commit/a28bbfc2313c859c0a9226625b6a44128e278dcc))

## [0.1.5](https://github.com/timoa/ha-remi/compare/0.1.4...0.1.5) (2026-02-20)


### Bug Fixes

* **docs:** update the README + move the icons in the /assets folder ([3c69b0b](https://github.com/timoa/ha-remi/commit/3c69b0b4a7d6344815c22b7f0e3d5954547dff3b))

## [0.1.4](https://github.com/timoa/ha-remi/compare/0.1.3...0.1.4) (2026-02-20)


### Bug Fixes

* **project:** change the domain name to be more explicit ([59641a7](https://github.com/timoa/ha-remi/commit/59641a755ec714ac421257427b5244e3008f5c4d))

## [0.1.3](https://github.com/timoa/ha-remi/compare/0.1.2...0.1.3) (2026-02-20)


### Bug Fixes

* **project:** add the icon files (light and dark variant) ([98b8df9](https://github.com/timoa/ha-remi/commit/98b8df986476f6a155815f50a041b562b8000db2))

## [0.1.2](https://github.com/timoa/ha-remi/compare/0.1.1...0.1.2) (2026-02-20)


### Bug Fixes

* **project:** simplify name of the integration ([2665b4c](https://github.com/timoa/ha-remi/commit/2665b4c744d210e2701fef381216fec3f88f62c8))

## [0.1.1](https://github.com/timoa/ha-remi/compare/0.1.0...0.1.1) (2026-02-20)


### Bug Fixes

* **cicd:** update the workflow values ([27029da](https://github.com/timoa/ha-remi/commit/27029da5a4ca2bf74448f181e3e303d73f16e42b))
* **entity:** fix the read only luminosity entity and add the alarm dynamic switch ([251b1a4](https://github.com/timoa/ha-remi/commit/251b1a423d7350fadbaa923042473c84d4822214))
