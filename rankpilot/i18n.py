"""Bilingual (English / French) translations for all user-facing text.

Every string shown in the terminal, in the CSV report, or in the
command-line help must be defined here for both languages.
"""

PASS = "PASS"
FAIL = "FAIL"
WARN = "WARN"

SUPPORTED_LANGUAGES = ("en", "fr")
DEFAULT_LANGUAGE = "en"

TRANSLATIONS = {
    "en": {
        # Application identity
        "app_title": "RANKPILOT — WEBSITE SEO AUDITOR",
        # Header labels
        "lbl_website": "Website",
        "lbl_date": "Analysis date",
        "lbl_http_status": "HTTP status",
        # Sections
        "sec_results": "SEO ANALYSIS RESULTS",
        "sec_summary": "SUMMARY",
        "lbl_passed": "Checks Passed",
        "lbl_failed": "Checks Failed",
        "lbl_warnings": "Warnings",
        "lbl_issues": "Issues Found",
        "lbl_csv": "CSV Report",
        # Check names
        "check_page": "Page Load",
        "check_title": "Page Title",
        "check_meta": "Meta Description",
        "check_h1": "H1 Heading",
        "check_images": "Image Alt Attributes",
        "check_links": "Internal Links",
        "check_sitemap": "Sitemap",
        "check_robots": "Robots.txt",
        # Status labels
        "status_PASS": "PASS",
        "status_FAIL": "FAIL",
        "status_WARN": "WARN",
        # Check details
        "page_ok": "Page downloaded successfully (HTTP {status}).",
        "title_ok": 'Title found: "{value}"',
        "title_missing": "No <title> tag found on the page.",
        "title_empty": "The <title> tag is present but empty.",
        "meta_ok": 'Meta description found: "{value}"',
        "meta_missing": "No meta description found.",
        "meta_empty": "The meta description is empty.",
        "h1_ok": 'H1 heading found: "{value}"',
        "h1_missing": "No H1 heading found on the page.",
        "h1_multiple": "{count} H1 headings found (first: \"{first}\"); a page should have a single H1.",
        "images_none": "No images found on the page.",
        "images_ok": "{total} image(s) found, all with a non-empty alt attribute.",
        "images_missing_only": "{missing} of {total} image(s) have no alt attribute.",
        "images_empty_only": "{empty} of {total} image(s) have an empty alt attribute; this can be intentional for decorative images.",
        "images_both": "{missing} of {total} image(s) have no alt attribute; {empty} have an empty alt attribute (possibly intentional for decorative images).",
        "links_none": "No internal links found on the page.",
        "links_ok": "{count} internal link(s) checked, none broken.",
        "links_broken": "{broken} broken internal link(s) out of {count} checked.",
        "links_truncated": " Only the first {limit} unique internal links were checked.",
        "link_broken_item": "{url} -> {status}",
        "sitemap_robots": "Sitemap declared in robots.txt: {url}",
        "sitemap_default": "Sitemap found at {url}",
        "sitemap_missing": "No sitemap found (checked robots.txt declarations and /sitemap.xml).",
        "robots_ok": "robots.txt found at {url}",
        "robots_missing": "No robots.txt file found at the website root.",
        # CSV headers and rows
        "csv_website": "Website",
        "csv_date": "Analysis date",
        "csv_check": "Check",
        "csv_status": "Status",
        "csv_details": "Details",
        "csv_related_url": "Related URL",
        "csv_http_status": "HTTP status",
        "csv_broken_link": "Broken Internal Link",
        # Errors
        "err_url_empty": "No URL provided.",
        "err_url_scheme": "Invalid URL: only http:// and https:// URLs are accepted.",
        "err_url_invalid": "Invalid URL: could not determine a valid hostname.",
        "err_timeout": "The website did not respond in time (timeout).",
        "err_connection": "Could not connect to the website.",
        "err_ssl": "SSL/TLS error while contacting the website.",
        "err_fetch": "Could not download the page.",
        "err_http_status": "The website returned HTTP status {status}. The analysis was aborted.",
        "err_analysis_failed": "Analysis failed: {detail}",
        # Command-line help
        "help_description": "RankPilot — Website SEO Auditor: analyze a web page for common SEO issues and generate a CSV report.",
        "help_url": "Website URL to analyze (e.g. https://example.com). If omitted, RankPilot starts in interactive mode.",
        "help_lang": "Interface language: en (English) or fr (French). Default: en.",
        "help_timeout": "Request timeout in seconds. Default: 10.",
        "help_reports_dir": "Directory where CSV reports are saved. Default: reports.",
        "help_version": "Show the RankPilot version and exit.",
        # Interactive mode
        "prompt_url": "Website URL to analyze",
        "prompt_hint": "(leave empty to cancel)",
        "cancelled": "Analysis cancelled.",
    },
    "fr": {
        # Application identity
        "app_title": "RANKPILOT — AUDITEUR SEO DE SITES WEB",
        # Header labels
        "lbl_website": "Site web",
        "lbl_date": "Date d'analyse",
        "lbl_http_status": "Statut HTTP",
        # Sections
        "sec_results": "RÉSULTATS DE L'ANALYSE SEO",
        "sec_summary": "RÉSUMÉ",
        "lbl_passed": "Contrôles réussis",
        "lbl_failed": "Contrôles échoués",
        "lbl_warnings": "Avertissements",
        "lbl_issues": "Problèmes détectés",
        "lbl_csv": "Rapport CSV",
        # Check names
        "check_page": "Chargement de la page",
        "check_title": "Titre de la page",
        "check_meta": "Méta-description",
        "check_h1": "En-tête H1",
        "check_images": "Attributs alt des images",
        "check_links": "Liens internes",
        "check_sitemap": "Sitemap",
        "check_robots": "Robots.txt",
        # Status labels
        "status_PASS": "RÉUSSI",
        "status_FAIL": "ÉCHEC",
        "status_WARN": "ALERTE",
        # Check details
        "page_ok": "Page téléchargée avec succès (HTTP {status}).",
        "title_ok": "Titre trouvé : « {value} »",
        "title_missing": "Aucune balise <title> trouvée sur la page.",
        "title_empty": "La balise <title> est présente mais vide.",
        "meta_ok": "Méta-description trouvée : « {value} »",
        "meta_missing": "Aucune méta-description trouvée.",
        "meta_empty": "La méta-description est vide.",
        "h1_ok": "En-tête H1 trouvé : « {value} »",
        "h1_missing": "Aucun en-tête H1 trouvé sur la page.",
        "h1_multiple": "{count} en-têtes H1 trouvés (premier : « {first} ») ; une page devrait avoir un seul H1.",
        "images_none": "Aucune image trouvée sur la page.",
        "images_ok": "{total} image(s) trouvée(s), toutes avec un attribut alt non vide.",
        "images_missing_only": "{missing} image(s) sur {total} n'ont pas d'attribut alt.",
        "images_empty_only": "{empty} image(s) sur {total} ont un attribut alt vide ; cela peut être intentionnel pour les images décoratives.",
        "images_both": "{missing} image(s) sur {total} n'ont pas d'attribut alt ; {empty} ont un attribut alt vide (potentiellement intentionnel pour les images décoratives).",
        "links_none": "Aucun lien interne trouvé sur la page.",
        "links_ok": "{count} lien(s) interne(s) vérifié(s), aucun lien cassé.",
        "links_broken": "{broken} lien(s) interne(s) cassé(s) sur {count} vérifié(s).",
        "links_truncated": " Seuls les {limit} premiers liens internes uniques ont été vérifiés.",
        "link_broken_item": "{url} -> {status}",
        "sitemap_robots": "Sitemap déclaré dans robots.txt : {url}",
        "sitemap_default": "Sitemap trouvé à l'adresse {url}",
        "sitemap_missing": "Aucun sitemap trouvé (déclarations robots.txt et /sitemap.xml vérifiées).",
        "robots_ok": "robots.txt trouvé à l'adresse {url}",
        "robots_missing": "Aucun fichier robots.txt trouvé à la racine du site.",
        # CSV headers and rows
        "csv_website": "Site web",
        "csv_date": "Date d'analyse",
        "csv_check": "Contrôle",
        "csv_status": "Statut",
        "csv_details": "Détails",
        "csv_related_url": "URL associée",
        "csv_http_status": "Statut HTTP",
        "csv_broken_link": "Lien interne cassé",
        # Errors
        "err_url_empty": "Aucune URL fournie.",
        "err_url_scheme": "URL invalide : seules les URL http:// et https:// sont acceptées.",
        "err_url_invalid": "URL invalide : impossible de déterminer un nom d'hôte valide.",
        "err_timeout": "Le site web n'a pas répondu dans le délai imparti.",
        "err_connection": "Impossible de se connecter au site web.",
        "err_ssl": "Erreur SSL/TLS lors du contact avec le site web.",
        "err_fetch": "Impossible de télécharger la page.",
        "err_http_status": "Le site web a renvoyé le statut HTTP {status}. L'analyse a été interrompue.",
        "err_analysis_failed": "Échec de l'analyse : {detail}",
        # Command-line help
        "help_description": "RankPilot — Auditeur SEO de sites web : analyse une page web pour détecter les problèmes SEO courants et génère un rapport CSV.",
        "help_url": "URL du site web à analyser (ex. https://example.com). Si omise, RankPilot démarre en mode interactif.",
        "help_lang": "Langue de l'interface : en (anglais) ou fr (français). Par défaut : en.",
        "help_timeout": "Délai d'expiration des requêtes en secondes. Par défaut : 10.",
        "help_reports_dir": "Répertoire où les rapports CSV sont enregistrés. Par défaut : reports.",
        "help_version": "Afficher la version de RankPilot et quitter.",
        # Interactive mode
        "prompt_url": "URL du site web à analyser",
        "prompt_hint": "(laissez vide pour annuler)",
        "cancelled": "Analyse annulée.",
    },
}


class Translator:
    """Provides localized strings for a given language."""

    def __init__(self, lang: str = DEFAULT_LANGUAGE):
        if lang not in SUPPORTED_LANGUAGES:
            lang = DEFAULT_LANGUAGE
        self.lang = lang
        self._strings = TRANSLATIONS[lang]

    def t(self, key: str, **params) -> str:
        """Return the translated string for ``key``, formatted with ``params``."""
        text = self._strings.get(key, key)
        return text.format(**params) if params else text

    def status_label(self, status: str) -> str:
        """Return the localized label for a PASS/FAIL/WARN status."""
        return self.t(f"status_{status}")
