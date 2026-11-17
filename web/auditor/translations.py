"""Centralized translations for the RankPilot web interface.

Engine strings (check names, statuses, check details, engine errors)
come from ``rankpilot.i18n``; this module adds the web-only strings and
falls back to the engine catalogue, so both interfaces stay consistent.
"""

from __future__ import annotations

from rankpilot.i18n import SUPPORTED_LANGUAGES, Translator

LANG_SESSION_KEY = "rankpilot_lang"

WEB_TRANSLATIONS = {
    "en": {
        "brand_tagline": "Website SEO Auditor",
        "nav_dashboard": "Dashboard",
        "nav_analyze": "Analyze Website",
        "nav_reports": "Reports",
        "nav_about": "About RankPilot",
        "lang_switch_label": "Language",
        "btn_analyze": "Analyze Website",
        "loading_message": "Analyzing website… this can take up to a minute.",
        "footer_text": "RankPilot — bilingual SEO auditing platform. The RankPilot score is an internal quality indicator, not an official Google score.",
        # Dashboard
        "dash_title": "Dashboard",
        "dash_subtitle": "Overview of your SEO analyses",
        "stat_sites": "Websites Analyzed",
        "stat_score": "Average SEO Score",
        "stat_issues": "Issues Detected",
        "stat_success": "Successful Analyses",
        "recent_title": "Recent Analyses",
        "empty_title": "No analyses yet",
        "empty_text": "Run your first SEO audit to see statistics, results and reports here.",
        "col_website": "Website",
        "col_date": "Date",
        "col_score": "Score",
        "col_status": "Status",
        "col_actions": "Actions",
        "action_view": "View",
        "action_csv": "CSV",
        # Analyzer
        "ana_title": "Analyze a Website",
        "ana_subtitle": "Enter the URL of a public website to run the seven RankPilot SEO checks.",
        "ana_label": "Website URL",
        "ana_placeholder": "https://example.com",
        "ana_help": "Only public http:// and https:// websites can be analyzed. Private, local and reserved network addresses are blocked for security reasons.",
        "ana_checks_note": "The audit checks the page title, meta description, H1 heading, image alt attributes, broken internal links, sitemap and robots.txt.",
        # Results
        "res_title": "SEO Analysis Results",
        "res_domain": "Domain",
        "res_date": "Analyzed on",
        "res_score": "RankPilot SEO Score",
        "score_explain": "The score reflects the seven checks run on this page: a passed check counts full points, a warning counts half points and a failed check counts zero. It is an internal quality indicator, not an official Google score.",
        "res_passed": "Passed",
        "res_failed": "Failed",
        "res_warnings": "Warnings",
        "res_issues": "Issues detected",
        "res_checks": "Individual Checks",
        "res_broken": "Broken Internal Links",
        "res_broken_none": "No broken internal links were detected.",
        "col_url": "URL",
        "col_http": "HTTP status",
        "res_detected": "Detected content",
        "lbl_title": "Page title",
        "lbl_meta": "Meta description",
        "lbl_h1": "H1 heading",
        "res_none": "none detected",
        "res_download": "Download CSV report",
        "res_back_reports": "All reports",
        "res_error_title": "This analysis could not be completed",
        "chart_title": "Check outcomes",
        "chart_passed": "Passed",
        "chart_failed": "Failed",
        "chart_warn": "Warnings",
        # Reports
        "rep_title": "Reports",
        "rep_subtitle": "History of your SEO analyses and their CSV reports",
        "rep_empty": "No reports yet. Analyze a website to create your first report.",
        "rep_page": "Page",
        "rep_of": "of",
        "rep_prev": "Previous",
        "rep_next": "Next",
        "rep_success": "Completed",
        "rep_error": "Failed",
        # About
        "about_title": "About RankPilot",
        "about_text": "RankPilot is a bilingual SEO auditing platform. The same Python engine powers both the command-line interface and this web application: it downloads a page, runs seven SEO checks and produces a detailed report.",
        "about_scoring_title": "Scoring methodology",
        "about_scoring": "Each of the seven counted checks contributes equally to the score out of 100: PASS awards full points, WARN awards half points and FAIL awards zero. The score summarizes the audit; it does not predict search engine rankings.",
        "about_security_title": "Security",
        "about_security": "Submitted URLs are strictly validated: only public http/https addresses are accepted, DNS-resolved addresses are checked against private and reserved ranges, every redirect hop is revalidated, responses are size-limited and requests always time out.",
        # Web-only errors
        "err_ssrf_blocked": "This address resolves to a private, local or reserved network range. RankPilot only analyzes public websites.",
        "err_response_too_large": "The website response is too large to be analyzed.",
        "msg_analysis_saved": "Analysis completed and saved to your report history.",
        "msg_analysis_failed": "The analysis failed, but the attempt was saved in your report history.",
    },
    "fr": {
        "brand_tagline": "Auditeur SEO de sites web",
        "nav_dashboard": "Tableau de bord",
        "nav_analyze": "Analyser un site",
        "nav_reports": "Rapports",
        "nav_about": "À propos de RankPilot",
        "lang_switch_label": "Langue",
        "btn_analyze": "Analyser le site",
        "loading_message": "Analyse du site en cours… cela peut prendre jusqu'à une minute.",
        "footer_text": "RankPilot — plateforme bilingue d'audit SEO. Le score RankPilot est un indicateur de qualité interne, pas un score officiel Google.",
        # Dashboard
        "dash_title": "Tableau de bord",
        "dash_subtitle": "Vue d'ensemble de vos analyses SEO",
        "stat_sites": "Sites web analysés",
        "stat_score": "Score SEO moyen",
        "stat_issues": "Problèmes détectés",
        "stat_success": "Analyses réussies",
        "recent_title": "Analyses récentes",
        "empty_title": "Aucune analyse pour le moment",
        "empty_text": "Lancez votre premier audit SEO pour voir apparaître ici statistiques, résultats et rapports.",
        "col_website": "Site web",
        "col_date": "Date",
        "col_score": "Score",
        "col_status": "Statut",
        "col_actions": "Actions",
        "action_view": "Voir",
        "action_csv": "CSV",
        # Analyzer
        "ana_title": "Analyser un site web",
        "ana_subtitle": "Saisissez l'URL d'un site web public pour lancer les sept contrôles SEO de RankPilot.",
        "ana_label": "URL du site web",
        "ana_placeholder": "https://example.com",
        "ana_help": "Seuls les sites publics http:// et https:// peuvent être analysés. Les adresses privées, locales et réservées sont bloquées pour des raisons de sécurité.",
        "ana_checks_note": "L'audit vérifie le titre de la page, la méta-description, l'en-tête H1, les attributs alt des images, les liens internes cassés, le sitemap et le robots.txt.",
        # Results
        "res_title": "Résultats de l'analyse SEO",
        "res_domain": "Domaine",
        "res_date": "Analysé le",
        "res_score": "Score SEO RankPilot",
        "score_explain": "Le score reflète les sept contrôles exécutés sur cette page : un contrôle réussi compte tous les points, une alerte la moitié et un échec zéro. C'est un indicateur de qualité interne, pas un score officiel Google.",
        "res_passed": "Réussis",
        "res_failed": "Échoués",
        "res_warnings": "Avertissements",
        "res_issues": "Problèmes détectés",
        "res_checks": "Contrôles détaillés",
        "res_broken": "Liens internes cassés",
        "res_broken_none": "Aucun lien interne cassé n'a été détecté.",
        "col_url": "URL",
        "col_http": "Statut HTTP",
        "res_detected": "Contenu détecté",
        "lbl_title": "Titre de la page",
        "lbl_meta": "Méta-description",
        "lbl_h1": "En-tête H1",
        "res_none": "aucun contenu détecté",
        "res_download": "Télécharger le rapport CSV",
        "res_back_reports": "Tous les rapports",
        "res_error_title": "Cette analyse n'a pas pu être terminée",
        "chart_title": "Répartition des contrôles",
        "chart_passed": "Réussis",
        "chart_failed": "Échoués",
        "chart_warn": "Alertes",
        # Reports
        "rep_title": "Rapports",
        "rep_subtitle": "Historique de vos analyses SEO et de leurs rapports CSV",
        "rep_empty": "Aucun rapport pour le moment. Analysez un site web pour créer votre premier rapport.",
        "rep_page": "Page",
        "rep_of": "sur",
        "rep_prev": "Précédent",
        "rep_next": "Suivant",
        "rep_success": "Terminée",
        "rep_error": "Échouée",
        # About
        "about_title": "À propos de RankPilot",
        "about_text": "RankPilot est une plateforme bilingue d'audit SEO. Le même moteur Python anime l'interface en ligne de commande et cette application web : il télécharge une page, exécute sept contrôles SEO et produit un rapport détaillé.",
        "about_scoring_title": "Méthode de calcul du score",
        "about_scoring": "Chacun des sept contrôles comptabilisés contribue également au score sur 100 : RÉUSSI donne tous les points, ALERTE la moitié et ÉCHEC zéro. Le score résume l'audit ; il ne prédit pas le classement dans les moteurs de recherche.",
        "about_security_title": "Sécurité",
        "about_security": "Les URL soumises sont strictement validées : seules les adresses http/https publiques sont acceptées, les adresses résolues par DNS sont vérifiées contre les plages privées et réservées, chaque saut de redirection est revalidé, les réponses sont limitées en taille et les requêtes expirent toujours.",
        # Web-only errors
        "err_ssrf_blocked": "Cette adresse correspond à une plage réseau privée, locale ou réservée. RankPilot analyse uniquement des sites web publics.",
        "err_response_too_large": "La réponse du site web est trop volumineuse pour être analysée.",
        "msg_analysis_saved": "Analyse terminée et enregistrée dans votre historique de rapports.",
        "msg_analysis_failed": "L'analyse a échoué, mais la tentative a été enregistrée dans votre historique de rapports.",
    },
}


class WebTranslator:
    """Translator for web UI strings, falling back to the engine catalogue."""

    def __init__(self, lang: str = "en"):
        if lang not in SUPPORTED_LANGUAGES:
            lang = "en"
        self.lang = lang
        self._engine = Translator(lang)
        self._web = WEB_TRANSLATIONS[lang]

    def t(self, key: str, **params) -> str:
        text = self._web.get(key)
        if text is None:
            return self._engine.t(key, **params)
        return text.format(**params) if params else text

    def status_label(self, status: str) -> str:
        return self._engine.status_label(status)

    def __getattr__(self, key: str) -> str:
        # Convenient attribute access in Django templates: {{ t.nav_reports }}
        if key.startswith("_"):
            raise AttributeError(key)
        return self.t(key)
