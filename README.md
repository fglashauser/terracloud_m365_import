# terracloud_m365_import

**terracloud_m365_import** ist eine Frappe/ERPNext App zur automatisierten Importierung und Verwaltung von Microsoft 365 Abonnements über die Terracloud-Plattform. Diese App erleichtert die Integration von Terracloud-Daten in ERPNext, um Abonnements, Bestellungen und Rechnungen effizient zu verwalten.

## Inhaltsverzeichnis

- [Features](#features)
- [Voraussetzungen](#voraussetzungen)
- [Installation](#installation)
- [Konfiguration](#konfiguration)
- [Verwendung](#verwendung)
- [Beitrag leisten](#beitrag-leisten)
- [Lizenz](#lizenz)

## Features

- **Automatisierter Import:** Importiert Abonnementdaten und Bestellungen aus Terracloud-CSV-Dateien.
- **Subscription Management:** Erstellt und verwaltet Kundenabonnements basierend auf importierten Daten.
- **Rechnungsstellung:** Generiert automatisch Rechnungen für monatliche und jährliche Abonnements.
- **Preisberechnung:** Berechnet anteilige Preise basierend auf tatsächlichen Tagen im Abrechnungszeitraum.
- **Fehlerprotokollierung:** Umfangreiche Logging-Funktionen zur Nachverfolgung und Fehlerdiagnose.

## Voraussetzungen

- **ERPNext:** Version X.X oder höher
- **Frappe:** Version X.X oder höher
- **Python:** Version 3.8 oder höher
- **Weitere Abhängigkeiten:** Siehe `requirements.txt`

## Installation

1. **Repository klonen:**

    ```bash
    cd frappe-bench/apps
    git clone https://github.com/yourusername/terracloud_m365_import.git
    ```

2. **App installieren:**

    ```bash
    cd ../..
    bench install-app terracloud_m365_import
    ```

3. **Abhängigkeiten installieren:**

    ```bash
    pip install -r apps/terracloud_m365_import/requirements.txt
    ```

4. **Datenbank migrieren:**

    ```bash
    bench migrate
    ```

## Konfiguration

1. **Einstellungen festlegen:**
   
   Gehen Sie zu **Setup > Terracloud M365 Import** und konfigurieren Sie die erforderlichen Einstellungen wie API-Schlüssel, Preislisten und andere relevante Parameter.

2. **CSV-Dateipfad angeben:**
   
   Stellen Sie sicher, dass der Pfad zur Terracloud-CSV-Datei korrekt in den Einstellungen angegeben ist.

3. **Zeitpläne einrichten (optional):**
   
   Richten Sie Cron-Jobs ein, um den Importprozess regelmäßig automatisch auszuführen.

## Verwendung

1. **Import starten:**

    Gehen Sie zu **Terracloud M365 Import > Import starten** und klicken Sie auf **Start Import**, um den Importprozess manuell zu initiieren.

2. **Abonnements verwalten:**
   
   Nach dem Import werden die Abonnements unter **Abonnements** im ERPNext-System angezeigt. Sie können diese verwalten, bearbeiten und verfolgen.

3. **Rechnungen überprüfen:**
   
   Generierte Rechnungen finden Sie unter **Verkäufe > Rechnungen**. Hier können Sie den Status der Rechnungen einsehen und bearbeiten.

## Beitrag leisten

Beiträge zur **terracloud_m365_import** App sind willkommen! Bitte folgen Sie diesen Schritten:

1. Forken Sie das Repository.
2. Erstellen Sie einen neuen Branch für Ihre Änderungen.
3. Committen Sie Ihre Änderungen mit aussagekräftigen Nachrichten.
4. Senden Sie einen Pull Request.

Für größere Änderungen, öffnen Sie bitte ein Issue zur Diskussion vorab.

## Lizenz

Dieses Projekt ist unter der [MIT Lizenz](LICENSE) lizenziert.