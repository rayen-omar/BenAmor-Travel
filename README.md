# BenAmor Travel — Module Odoo 19 Community

Module unique de gestion pour petites et moyennes agences de voyage.
Toutes les fonctions, natives et personnalisées, sont regroupées sous un seul menu.

---

## SOMMAIRE

1. Principe du module
2. Installation
3. Structure du menu
4. Ce qui est natif Odoo / ce qui est développé
5. Description des écrans
6. Guide d'utilisation
7. Configuration initiale
8. Modèles de données
9. Droits d'accès
10. Ce qui n'est pas couvert
11. Points techniques
12. Feuille de route

---

## 1. PRINCIPE DU MODULE

### La règle de base

Ce module suit un principe simple : **ne jamais redévelopper ce qu'Odoo sait déjà faire.**

Odoo Community contient déjà la facturation, les commandes, les paiements, la
comptabilité, les contacts, le multi-devise. Tout cela fonctionne, est testé, et
sera maintenu par Odoo. Le redévelopper serait du travail perdu et une dette de
migration à chaque nouvelle version.

Le module ajoute donc uniquement ce qui manque au métier de l'agence de voyage,
et amène le reste dans le même menu.

### Le problème résolu

Odoo sait faire un devis avec des lignes. Mais une agence a besoin de savoir :

- Qui voyage (des passagers, différents du client qui paie)
- Chez qui on achète chaque prestation (vol chez A, hôtel chez B)
- Combien coûte réellement le dossier (pour connaître la marge)
- Quand le client doit payer (acompte, solde)

Odoo n'a aucun endroit pour ces informations. Le module crée cet endroit :
**le dossier de voyage**.

### L'architecture

```
   MODULE (développé)                 ODOO NATIF (non modifié)

   Dossier de voyage
   ├── Prestations       ──────►      Commande de vente
   ├── Passagers                      ├── Facture client
   └── Échéancier                     ├── Paiement
                                      └── Compte analytique

                                      Commande d'achat
                                      └── Facture fournisseur
```

Le dossier rassemble l'information métier, puis génère une commande de vente
Odoo standard. Toute la comptabilité reste native.

---

## 2. INSTALLATION

### Prérequis

- Odoo 19.0 Community (ou Enterprise, le module fonctionne sur les deux)
- PostgreSQL
- Applications installées automatiquement par les dépendances :
  Contacts, Ventes, Achats, Facturation

### Étapes

1. Copier le dossier `benamor_travel/` dans un répertoire d'addons déclaré dans
   `odoo.conf` :

   ```
   addons_path = /opt/odoo/addons,/opt/odoo/custom_addons
   ```

2. Redémarrer le service Odoo :

   ```
   sudo systemctl restart odoo
   ```

3. Activer le mode développeur :
   Paramètres → Général → Outils développeur → Activer le mode développeur

4. Mettre à jour la liste des applications :
   Apps → Mettre à jour la liste des applications

5. Rechercher « BenAmor Travel » et cliquer sur Installer

### Mise à jour après modification du code

```
sudo systemctl stop odoo
sudo -u odoo odoo -d nom_base -u benamor_travel --stop-after-init
sudo systemctl start odoo
```

---

## 3. STRUCTURE DU MENU

Une seule application : **BenAmor Travel**

```
BenAmor Travel
│
├── Tableau de bord                 [développé]
│
├── Opérations
│   ├── Dossiers de voyage          [développé]
│   ├── Départs à venir             [développé]
│   ├── Passagers                   [développé]
│   ├── Alertes passeports          [développé]
│   ├── Documents manquants         [développé]
│   ├── Prestations                 [développé]
│   └── Modèles de dossier          [développé]
│
├── Ventes
│   ├── Devis et commandes          [natif Odoo]
│   ├── Factures clients            [natif Odoo]
│   └── Encaissements               [natif Odoo]
│
├── Achats
│   ├── Commandes fournisseurs      [natif Odoo]
│   ├── Factures fournisseurs       [natif Odoo]
│   └── Règlements                  [natif Odoo]
│
├── Contacts
│   ├── Clients                     [natif Odoo]
│   ├── Fournisseurs                [natif Odoo]
│   ├── Voyageurs                   [développé]
│   └── Tous les contacts           [natif Odoo]
│
├── Analyse                         (responsables uniquement)
│   ├── Analyse des marges          [développé]
│   ├── Analyse par prestation      [développé]
│   ├── Comptes analytiques         [natif Odoo]
│   └── Écritures analytiques       [natif Odoo]
│
├── Aide
│   └── Guide complet               [développé]
│
└── Configuration                   (responsables uniquement)
    ├── Référentiel voyage
    │   ├── Destinations            [développé]
    │   ├── Compagnies aériennes    [développé]
    │   ├── Hôtels                  [développé]
    │   └── Types de documents      [développé]
    ├── Articles et tarifs
    │   ├── Articles / prestations  [natif Odoo]
    │   └── Listes de prix          [natif Odoo]
    └── Comptabilité
        ├── Conditions de paiement  [natif Odoo]
        ├── Taxes                   [natif Odoo]
        └── Devises et taux         [natif Odoo]
```

L'utilisateur n'a jamais besoin de sortir de cette application.

---

## 4. NATIF ODOO / DÉVELOPPÉ

### Utilisé tel quel, sans une ligne de code

| Besoin métier | Application Odoo Community |
|---|---|
| Fiches clients, fournisseurs, hôtels | Contacts |
| Devis, commandes, acomptes | Ventes |
| Commandes fournisseurs | Achats |
| Factures clients et fournisseurs | Facturation |
| Encaissements et règlements | Facturation |
| Plan comptable, écritures, lettrage | Facturation |
| Multi-devise avec taux de change | Facturation |
| Conditions de paiement | Facturation |
| Taxes | Facturation |
| Articles et listes de prix | Ventes |
| Comptabilité analytique | Facturation |
| Historique, notes, discussions | Chatter (intégré) |
| Rappels et tâches | Activités (intégré) |
| Pièces jointes (scans passeports) | Intégré |
| Envoi d'emails | Discuss |
| Import / export Excel | Intégré |
| Gestion des utilisateurs | Paramètres |

### Développé dans le module

| Objet | Rôle |
|---|---|
| `travel.file` | Le dossier de voyage, objet central |
| `travel.service` | Les prestations vendues, avec coût et marge |
| `travel.passenger` | Les passagers et leurs documents |
| `travel.payment.plan` | L'échéancier de paiement |
| `travel.dashboard` | Tableau de bord (modèle transitoire, aucune donnée stockée) |
| `travel.document.type` | Types de documents configurables |
| `travel.document` | Checklist des documents d'un dossier |
| `travel.destination` | Référentiel des destinations |
| `travel.airline` | Référentiel des compagnies aériennes |
| `travel.hotel` | Référentiel des hôtels |

### Modifications apportées à Odoo

**1. Champs de liaison**

| Modèle | Champ ajouté |
|---|---|
| `sale.order` | `travel_file_id` |
| `account.move` | `travel_file_id` + destination, dates, passagers (champs liés) |
| `res.partner` | profil voyageur : passeport, nationalité, date de naissance, préférences, historique |

Le dossier se propage automatiquement de la commande vers la facture via
`_prepare_invoice()`.

**2. Bloc voyage sur les documents PDF**

Un encadré est ajouté en haut de la facture client et du devis, contenant :
référence du dossier, destination, dates de départ et de retour, liste des
passagers. Le bloc n'apparaît que si le document est rattaché à un dossier.

**3. Vocabulaire métier (fichier `models/travel_labels.py`)**

Les libellés natifs sont renommés en vocabulaire agence de voyage :

| Modèle | Champ technique | Libellé Odoo | Libellé module |
|---|---|---|---|
| `sale.order` | `order_line` | Lignes de commande | Prestations |
| `sale.order` | `client_order_ref` | Référence client | Référence client |
| `sale.order` | `validity_date` | Date d'expiration | Option valable jusqu'au |
| `sale.order` | `commitment_date` | Date de livraison | Date de départ prévue |
| `sale.order.line` | `product_id` | Article | Prestation |
| `sale.order.line` | `product_uom_qty` | Quantité | Qté (pax / nuits) |
| `account.move` | `invoice_line_ids` | Lignes de facture | Prestations |
| `account.move` | `invoice_origin` | Document d'origine | Dossier d'origine |
| `account.move.line` | `product_id` | Article | Prestation |
| `purchase.order` | `order_line` | Lignes de commande | Prestations achetées |
| `purchase.order.line` | `product_id` | Article | Prestation |

Menus renommés : « Devis et commandes » devient « Réservations », « Factures
clients » devient « Factures voyage ».

**Important** : seuls les libellés changent. Les noms techniques des champs
restent identiques, donc aucun autre module ni aucune migration n'est affecté.

**Pour revenir au vocabulaire Odoo standard** : retirer la ligne
`from . import travel_labels` de `models/__init__.py` et mettre le module à
jour. Tout redevient standard immédiatement.

**Ce qui n'est pas renommé** : les titres des rapports PDF (« Facture »,
« Devis ») et les libellés d'état (« Brouillon », « Confirmé ») restent en
vocabulaire Odoo. Les modifier demanderait de surcharger des sélections ou des
traductions, ce qui est plus fragile en migration.

---

## 4 bis. FONCTIONS D'AIDE À LA SAISIE

Huit fonctions ajoutées en version 2.0 pour réduire le temps de saisie et les
oublis. Chacune indique ce qui est natif Odoo et ce qui a été développé.

### 1. Dupliquer un dossier

**Natif Odoo.** Menu roue dentée → Dupliquer, sur n'importe quel dossier.

Développé : la méthode `copy_data` réinitialise ce qui ne doit pas être copié —
nouvelle référence, état brouillon, date d'ouverture du jour, PNR, numéros de
billets, références fournisseur, états d'échéances et de documents, visas.
Les prestations, passagers et échéances sont conservés.

### 2. Modèles de dossier

Développé. Un modèle est un `travel.file` avec `is_template = True`.

Menu Opérations → Modèles de dossier. Créez « Omra 10 jours » ou « Istanbul
7 nuits » avec ses prestations types, puis bouton **Créer un dossier depuis ce
modèle**.

Un modèle ne reçoit pas de numéro de séquence, ne peut pas être confirmé, et
n'apparaît pas dans la liste des dossiers.

Odoo possède des modèles de devis natifs (Ventes → Configuration → Modèles de
devis), mais ils s'appliquent aux commandes de vente, pas aux dossiers. Les deux
peuvent coexister.

### 3. Marge cible automatique

Développé. Deux niveaux :

- **Par ligne** : colonne « Marge cible (%) ». Saisir 25 calcule le prix de vente
  à partir du coût.
- **Par dossier** : champ « Marge cible du dossier » + bouton Appliquer, qui
  répercute le taux sur toutes les prestations ayant un coût.

Formule utilisée : `prix de vente = coût / (1 - taux)`. Le taux est donc une
marge sur prix de vente, pas un coefficient appliqué au coût. Un coût de 100 avec
un taux de 25 % donne un prix de 133,33 et une marge de 33,33, soit bien 25 % du
prix de vente.

Laisser la colonne vide permet de fixer le prix à la main comme avant.

### 4. Date limite d'annulation

Développé, avec des briques natives pour les alertes.

Chaque prestation porte une date limite d'annulation et un texte de conditions.
Un état se calcule automatiquement :

| État | Signification |
|---|---|
| Délai confortable | Plus de 7 jours avant la limite |
| Échéance proche | Moins de 7 jours — ligne orange |
| Délai dépassé | Limite franchie — ligne rouge |

Le dossier affiche la prochaine limite d'annulation toutes prestations
confondues, et un filtre de recherche liste les dossiers concernés.

Une tâche planifiée (`ir.cron`, natif Odoo) s'exécute chaque jour et crée une
**activité** (natif Odoo) sur les dossiers dont la limite tombe dans les 5 jours.
L'agent la voit dans sa liste d'activités, comme n'importe quel rappel Odoo.

Pour changer le délai d'alerte : Paramètres → Technique → Actions planifiées,
modifier `model._cron_travel_alerts()` en `model._cron_travel_alerts(10)`.

### 5. Prix par passager

Développé. Deux mécanismes :

- À la saisie du type de prestation, si le type est facturé par personne (vol,
  visa, assurance, omra, forfait), la quantité se remplit avec le nombre de
  passagers du dossier.
- Bouton **Qté = nombre de passagers** dans l'onglet Prestations, qui recalcule
  toutes les lignes concernées d'un coup — utile quand un passager est ajouté
  après la saisie des prestations.

Les hébergements et transferts sont exclus : leur quantité correspond à des
chambres ou des véhicules, pas à des personnes.

### 6. Checklist documents

Développé.

`travel.document.type` définit les documents demandés (configurable). Sept types
sont fournis par défaut : copie du passeport, photo d'identité, visa obtenu,
contrat signé, attestation d'assurance, billet émis, voucher hôtel.

Chaque type peut être limité à certains types de dossier, et marqué « par
passager » pour être demandé à chaque voyageur.

Sur le dossier, l'onglet Documents liste les pièces avec leur état (à obtenir,
reçu, sans objet). La liste se génère automatiquement à la confirmation, ou
manuellement par bouton.

Un menu Opérations → Documents manquants regroupe toutes les pièces en attente,
tous dossiers confondus.

### 7. Passager réutilisable

Développé, sur la base des Contacts natifs.

Le champ « Contact lié » sur un passager reprend automatiquement les documents
déjà connus : date de naissance, nationalité, numéro et expiration du passeport.

Inversement, quand un passager est enregistré avec un contact lié, ses documents
remontent vers la fiche contact. Le contact est marqué comme voyageur.

Résultat : un client fidèle n'a son passeport saisi qu'une seule fois.

### 8. Profil voyageur

Développé, sur la fiche contact native.

Un onglet **Voyageur** est ajouté à la fiche contact avec :

- ses documents de voyage (passeport, nationalité, date de naissance)
- son historique : nombre de voyages effectués, date du dernier voyage
- ses préférences (siège, repas, remarques)

Un bouton statistique **Dossiers** ouvre tous les dossiers où le contact
apparaît, soit comme client payeur, soit comme passager.

Le menu Contacts → Voyageurs liste les contacts marqués comme voyageurs.

---

## 5. DESCRIPTION DES ÉCRANS

### Dossier de voyage

L'écran principal. Un dossier = un voyage vendu.

**En-tête** : boutons d'action et barre d'état
(Brouillon → Option → Confirmé → Clôturé)

**Informations générales**
- Client payeur, type de dossier, destination, agent responsable
- Date d'ouverture, date de départ, date de retour
- Compte analytique (rempli automatiquement à la confirmation)

**Onglet Prestations**
Liste éditable des services vendus. Chaque ligne porte le fournisseur, le coût
d'achat, le prix de vente et la marge. Le total s'affiche en bas.

**Onglet Passagers**
Les personnes qui voyagent. Les lignes se colorent selon l'état du passeport.

**Onglet Échéancier**
Les paiements attendus avec leurs dates.

**Onglet Notes**
Notes internes libres.

**Boutons statistiques** : nombre de commandes générées, nombre de passagers.

**Chatter** : historique complet, messages, pièces jointes, activités planifiées.

### Tableau de bord

Écran d'accueil de l'application, en 4 blocs :

**Activité** — dossiers en cours, dossiers en option, départs sous 7 jours,
départs ce mois.

**Résultat du mois** — ventes, coûts, marge, taux de marge. Calculé sur les
dossiers confirmés ou clôturés ouverts dans le mois en cours.

**Cumul annuel** — ventes et marge depuis le 1er janvier.

**Points de vigilance** — passeports à contrôler, échéances en retard, montant
en retard, reste à encaisser.

Les tuiles avec chiffre cliquable ouvrent la liste filtrée correspondante.

Le tableau de bord ne stocke rien : les chiffres sont recalculés à chaque
ouverture de l'écran.

### Guide complet

Menu Aide. Ouvre une page dans un nouvel onglet du navigateur.

Le guide suit un dossier de voyage du début à la fin, en 15 étapes, et passe par
tous les menus de l'application dans l'ordre où on les utilise réellement :

1. Préparer l'agence (Configuration)
2. Enregistrer le client (Contacts)
3. Créer le dossier (Opérations)
4. Saisir les passagers
5. Saisir les prestations
6. Prévoir les paiements
7. Confirmer le dossier
8. Générer la commande (Ventes)
9. Facturer le client
10. Encaisser le paiement
11. Commander chez les fournisseurs (Achats)
12. Suivre au quotidien (Tableau de bord)
13. Imprimer les documents
14. Clôturer le dossier
15. Analyser l'activité (Analyse)

Se termine par un récapitulatif « où faire quoi » et les 6 erreurs fréquentes.

Fichier : `static/src/guide.html`. Autonome et imprimable.

### Départs à venir

Les dossiers confirmés dont la date de départ n'est pas passée. Écran de
contrôle quotidien pour l'agent.

### Alertes passeports

Tous les passagers dont le passeport est expiré, expire bientôt, ou n'est pas
renseigné. Écran à consulter avant chaque départ.

### Analyse des marges

Tableau croisé : marge par type de dossier, par mois, par agent, par
destination. Vue graphique disponible.

---

## 6. GUIDE D'UTILISATION

### Créer un dossier complet

**1. Ouvrir le dossier**

Opérations → Dossiers de voyage → Nouveau

Saisir le client, le type de dossier, la destination et les dates.
La référence `DV/2026/00001` est attribuée automatiquement.

**2. Saisir les passagers**

Onglet Passagers. Pour chaque personne : nom, type (adulte / enfant / bébé),
date de naissance, numéro de passeport et date d'expiration.

L'état du passeport se calcule seul :

| Couleur | Signification |
|---|---|
| Normal | Passeport valide plus de 6 mois après le départ |
| Orange | Expire moins de 6 mois après le départ |
| Rouge | Déjà expiré à la date de départ |

**3. Saisir les prestations**

Onglet Prestations. Une ligne par service acheté.

Exemple :

| Type | Désignation | Fournisseur | Coût | Vente |
|---|---|---|---|---|
| Vol | Tunis–Istanbul | Tunisair | 400 EUR | 1 800 TND |
| Hébergement | Hôtel 4* 6 nuits | TO partenaire | 550 EUR | 2 400 TND |
| Assurance | Assistance voyage | Assureur | 80 TND | 150 TND |

La marge se calcule en temps réel en bas de l'onglet. Les montants en devise
étrangère sont convertis automatiquement.

**4. Définir l'échéancier**

Onglet Échéancier. Exemple : acompte 1 500 TND au 10 janvier, solde
2 850 TND au 1er mars.

**5. Confirmer**

Bouton Confirmer. Le compte analytique est créé.
Le module refuse de confirmer un dossier sans prestation.

**6. Générer la commande de vente**

Bouton Générer la commande. Une commande de vente Odoo standard est créée avec
toutes les prestations en lignes.

**7. Facturer**

Depuis la commande : Créer une facture. Processus Odoo standard.

**8. Imprimer le voucher**

Bouton Imprimer → Voucher / Fiche dossier.

### Exclure une prestation de la facture

Cocher « Hors facture » sur la ligne. La prestation reste suivie pour le calcul
de la marge mais n'apparaît pas sur la commande de vente. Utile pour une
prestation offerte ou déjà facturée séparément.

---

## 7. CONFIGURATION INITIALE

À faire une seule fois avant d'utiliser le module.

### Étape 1 — Société

Paramètres → Sociétés. Renseigner nom, adresse, matricule fiscal, logo.

### Étape 2 — Devises

Configuration → Comptabilité → Devises et taux.
Activer EUR, USD et les autres devises selon les besoins, puis renseigner les
taux de change.

Sans taux de change, les prestations achetées en devise étrangère seront
converties à un taux incorrect et la marge sera fausse.

### Étape 3 — Articles

Configuration → Articles et tarifs → Articles / prestations.

Créer les prestations en type Service :

| Article | Usage |
|---|---|
| Billet avion | Toute billetterie |
| Nuitée hôtel | Hébergement |
| Forfait séjour | Packages |
| Frais de visa | Visa |
| Assurance voyage | Assurance |
| Transfert aéroport | Transferts |

### Étape 4 — Référentiel voyage

Configuration → Référentiel voyage.

- Destinations : Paris, Istanbul, Djerba, Dubaï…
- Compagnies aériennes : avec code IATA
- Hôtels : avec destination et catégorie

### Étape 5 — Fournisseurs

Contacts → Fournisseurs. Compagnies aériennes, tour-opérateurs, hôtels,
assureurs, consolidateurs.

### Étape 6 — Utilisateurs

Paramètres → Utilisateurs. Attribuer le groupe Agent ou Responsable dans la
section BenAmor Travel.

---

## 8. MODÈLES DE DONNÉES

### travel.file

| Champ | Type | Description |
|---|---|---|
| `name` | Char | Référence auto DV/AAAA/NNNNN |
| `partner_id` | Many2one | Client payeur |
| `file_type` | Selection | ticket / package / omra / visa / b2b / other |
| `user_id` | Many2one | Agent responsable |
| `date_open` | Date | Date d'ouverture |
| `date_departure` | Date | Date de départ |
| `date_return` | Date | Date de retour |
| `destination_id` | Many2one | Destination |
| `service_ids` | One2many | Prestations |
| `passenger_ids` | One2many | Passagers |
| `payment_plan_ids` | One2many | Échéances |
| `analytic_account_id` | Many2one | Compte analytique |
| `amount_sale` | Monetary | Total vente (calculé) |
| `amount_cost` | Monetary | Total coût (calculé) |
| `margin` | Monetary | Marge (calculée) |
| `margin_rate` | Float | Taux de marge en % (calculé) |
| `state` | Selection | draft / option / confirmed / done / cancel |

### travel.service

Champs communs : `service_type`, `product_id`, `description`, `supplier_id`,
`date_start`, `date_end`, `quantity`, `cost_currency_id`, `cost_amount`,
`cost_company`, `sale_price_unit`, `sale_subtotal`, `margin`,
`excluded_from_invoice`.

Champs vol : `airline_id`, `pnr`, `ticket_number`, `route`.

Champs hébergement : `hotel_id`, `room_type`, `board`, `nights`.

### travel.passenger

`name`, `pax_type`, `gender`, `birthdate`, `nationality_id`, `phone`, `email`,
`passport_number`, `passport_expiry`, `passport_state`, `visa_state`, `note`.

### travel.payment.plan

`name`, `date_due`, `amount`, `state`, `note`.

---

## 9. DROITS D'ACCÈS

| Groupe | Lecture | Écriture | Création | Suppression |
|---|---|---|---|---|
| Agent | oui | oui | oui | non |
| Responsable | oui | oui | oui | oui |

Les menus Analyse et Configuration sont réservés aux responsables.

Une règle multi-société filtre les dossiers par société.

---

## 10. CE QUI N'EST PAS COUVERT

Ce module est un socle. Il ne couvre pas :

- Génération automatique des commandes d'achat fournisseur
- Enregistrement des encaissements lié à l'échéancier
- Relances automatiques sur échéances et documents
- Module Omra / Hajj (groupes, rooming list, pèlerins)
- Fiscalité tunisienne (timbre fiscal, TVA sur marge, formats de facture)
- Commissions et relevés pour agences partenaires
- Portail client et réservation en ligne
- Connexion GDS (Amadeus, Galileo, Sabre)
- Rapprochement BSP / IATA
- Moteur de disponibilité hôtelière avec allotements

**Avertissement important** : tant que la partie fiscale tunisienne n'est pas
traitée et validée par un expert-comptable, les factures produites ne sont
probablement pas conformes aux exigences locales. Le module est utilisable pour
le développement et les tests, mais ce point doit être réglé avant toute
utilisation en production réelle.

---

## 11. POINTS TECHNIQUES

### Conversion de devise

La conversion utilise le taux à la date `date_start` de la prestation, qui
correspond au moment de l'engagement fournisseur.

Si la règle comptable retenue est le taux du jour de facturation, modifier la
méthode `_compute_amounts` dans `models/travel_service.py`.

Ce choix doit être fixé avant la mise en production. Le changer après plusieurs
mois de données impose un recalcul complet.

### Champs stockés

`sale_subtotal`, `cost_company` et `margin` sont stockés en base pour permettre
les recherches et les tableaux croisés. Ils sont recalculés à chaque
modification. Sur un dossier dépassant 200 prestations, vérifier les
performances.

### Contrôles non bloquants

Le module n'empêche pas de confirmer un dossier contenant un passeport expiré.
Il se contente d'un signal visuel. Pour rendre le contrôle bloquant, ajouter une
vérification dans `action_confirm` de `models/travel_file.py`.

### Arborescence des fichiers

```
benamor_travel/
├── __init__.py
├── __manifest__.py
├── README.md
├── data/
│   └── travel_data.xml              séquence, plan analytique
├── models/
│   ├── travel_file.py               dossier
│   ├── travel_service.py            prestations
│   ├── travel_passenger.py          passagers
│   ├── travel_payment_plan.py       échéancier
│   ├── travel_referential.py        destinations, compagnies, hôtels
│   ├── travel_document.py           types et checklist de documents
│   ├── res_partner.py               profil voyageur sur le contact
│   ├── travel_dashboard.py          indicateurs du tableau de bord
│   ├── sale_order.py                lien vers le dossier
│   ├── account_move.py              lien facture + infos voyage
│   └── travel_labels.py             renommage des libellés natifs
├── report/
│   ├── travel_file_report.xml       voucher PDF
│   └── travel_invoice_report.xml    bloc voyage sur facture et devis
├── security/
│   ├── travel_security.xml          groupes et règles
│   └── ir.model.access.csv          droits par modèle
├── static/
│   ├── description/
│   │   ├── icon.png                 logo du module (140x140)
│   │   └── index.html               page de présentation
│   └── src/
│       └── guide.html               guide complet intégré
└── views/
    ├── travel_file_views.xml
    ├── travel_service_views.xml
    ├── travel_passenger_views.xml
    ├── travel_referential_views.xml
    ├── res_partner_views.xml
    ├── travel_dashboard_views.xml
    ├── travel_help_views.xml
    ├── travel_analysis_views.xml
    ├── native_actions.xml           actions vers écrans natifs
    ├── sale_order_views.xml
    ├── account_move_views.xml
    └── travel_menus.xml             menu unique
```

### Choix des actions natives

Le fichier `native_actions.xml` définit ses propres actions `ir.actions.act_window`
plutôt que de référencer les identifiants XML d'Odoo (`sale.action_orders`,
`account.action_move_out_invoice_type`, etc.).

Raison : ces identifiants changent parfois entre versions majeures. En
définissant nos propres actions sur les modèles natifs, le module ne dépend que
des noms de modèles, qui sont stables.

---

## 12. FEUILLE DE ROUTE

### Phase suivante

| Ordre | Chantier | Effort |
|---|---|---|
| 1 | Encaissements liés à l'échéancier | Faible |
| 2 | Achats fournisseurs automatiques | Moyen |
| 3 | Relances automatiques | Faible |

Ces trois chantiers ferment la boucle vendre → acheter → encaisser → piloter.

### Reporté

Module Omra, fiscalité tunisienne, B2B agences partenaires, portail client.

### Non recommandé

Connexion GDS et moteur de disponibilité hôtelière : effort disproportionné pour
une petite structure, et dépendant d'accords commerciaux externes.

---

## LICENCE

LGPL-3
