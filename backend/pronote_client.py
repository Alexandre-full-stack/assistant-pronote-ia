"""
Client Pronote avec support CAS (monlycee.net, ENT régionaux)
Utilise pronotepy avec gestion avancée des erreurs
"""
import pronotepy
from pronotepy.ent import ent_list
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from loguru import logger
import asyncio
from functools import wraps
import traceback


class PronoteException(Exception):
    """Exception personnalisée pour les erreurs Pronote"""
    pass


class CASAuthenticationError(PronoteException):
    """Erreur d'authentification CAS"""
    pass


class PronoteClient:
    """
    Client robuste pour interagir avec Pronote
    Support authentification directe + CAS (monlycee.net, ENT régionaux)
    """
    
    def __init__(self):
        self.client: Optional[pronotepy.Client] = None
        self.session_info: Dict[str, Any] = {}
    
    @staticmethod
    def retry_on_failure(max_attempts=3, delay=2):
        """Décorateur pour réessayer en cas d'échec"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                for attempt in range(max_attempts):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        if attempt == max_attempts - 1:
                            raise
                        logger.warning(
                            f"Tentative {attempt + 1}/{max_attempts} échouée: {str(e)}"
                        )
                        await asyncio.sleep(delay * (attempt + 1))
                return None
            return wrapper
        return decorator
    
    async def authenticate_direct(
        self,
        pronote_url: str,
        username: str,
        password: str,
        account_type: int = 3
    ) -> Dict[str, Any]:
        """
        Authentification directe (sans CAS)
        
        Args:
            pronote_url: URL Pronote (ex: https://0123456X.index-education.net/pronote/eleve.html)
            username: Identifiant
            password: Mot de passe
            account_type: Type de compte (3=élève, 2=parent, 1=professeur)
        
        Returns:
            Informations de session
        """
        try:
            logger.info(f"Authentification directe vers {pronote_url}")
            
            # Créer le client Pronote
            self.client = pronotepy.Client(
                pronote_url,
                username=username,
                password=password
            )
            
            if not self.client.logged_in:
                raise PronoteException("Échec d'authentification - identifiants incorrects")
            
            # Extraire les informations de session
            self.session_info = self._extract_session_info()
            
            logger.info(
                f"Authentification réussie pour {self.session_info['student_name']}"
            )
            
            return self.session_info
            
        except Exception as e:
            logger.error(f"Erreur authentification directe: {str(e)}")
            raise PronoteException(f"Échec authentification: {str(e)}")
    
    async def authenticate_cas(
        self,
        pronote_url: str,
        username: str,
        password: str,
        ent_name: str = "ac_reunion"
    ) -> Dict[str, Any]:
        """
        Authentification via CAS (monlycee.net, ENT régionaux)
        
        Args:
            pronote_url: URL Pronote
            username: Identifiant ENT
            password: Mot de passe ENT
            ent_name: Nom de l'ENT (voir ent_list dans pronotepy.ent)
        
        Returns:
            Informations de session
        
        ENTs supportés:
        - ac_reunion, ac_orleans_tours, ac_rennes, ac_reims, ac_montpellier
        - arsene76, atrium_sud, cas_kosmos, eclat_bfc, ent27, ent77
        - ent_94, ent_creuse, ent_elyco, ent_essonne, ent_hdf, ent_somme
        - ent_var, l_normandie, laclasse_lyon, lyceeconnecte_aquitaine
        - lyceeconnecte_edu, mon_bureau_numerique, monlycee_net, neotech_occitanie
        - paris_classe_numerique, toutatice, webcollege_cantal
        """
        try:
            logger.info(
                f"Authentification CAS via {ent_name} vers {pronote_url}"
            )
            
            # Vérifier que l'ENT existe
            if ent_name not in [ent.__name__.lower() for ent in ent_list]:
                available_ents = ", ".join([ent.__name__ for ent in ent_list])
                raise CASAuthenticationError(
                    f"ENT '{ent_name}' non supporté. "
                    f"ENTs disponibles: {available_ents}"
                )
            
            # Trouver la classe ENT correspondante
            ent_class = next(
                (ent for ent in ent_list if ent.__name__.lower() == ent_name.lower()),
                None
            )
            
            if not ent_class:
                raise CASAuthenticationError(f"ENT {ent_name} non trouvé")
            
            # Créer le client avec authentification CAS
            self.client = pronotepy.Client.token_login(
                pronote_url,
                username=username,
                password=password,
                ent=ent_class
            )
            
            if not self.client.logged_in:
                raise CASAuthenticationError(
                    "Échec authentification CAS - vérifiez vos identifiants ENT"
                )
            
            # Extraire les informations
            self.session_info = self._extract_session_info()
            
            logger.info(
                f"Authentification CAS réussie pour {self.session_info['student_name']}"
            )
            
            return self.session_info
            
        except Exception as e:
            logger.error(f"Erreur authentification CAS: {str(e)}\n{traceback.format_exc()}")
            raise CASAuthenticationError(f"Échec authentification CAS: {str(e)}")
    
    def _extract_session_info(self) -> Dict[str, Any]:
        """Extrait les informations importantes de la session"""
        if not self.client or not self.client.logged_in:
            raise PronoteException("Pas de session active")
        
        info = self.client.info
        
        return {
            "student_name": info.name if hasattr(info, 'name') else "Inconnu",
            "class_name": info.class_name if hasattr(info, 'class_name') else None,
            "establishment": info.establishment if hasattr(info, 'establishment') else None,
            "logged_in": self.client.logged_in,
            "session_id": id(self.client)
        }
    
    @retry_on_failure(max_attempts=3)
    async def get_homework(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Récupère les devoirs
        
        Args:
            date_from: Date de début (par défaut: aujourd'hui)
            date_to: Date de fin (par défaut: +14 jours)
        
        Returns:
            Liste des devoirs
        """
        if not self.client or not self.client.logged_in:
            raise PronoteException("Pas de session active")
        
        try:
            # Dates par défaut
            if not date_from:
                date_from = datetime.now()
            if not date_to:
                date_to = date_from + timedelta(days=14)
            
            logger.info(f"Récupération devoirs du {date_from} au {date_to}")
            
            # Récupérer les devoirs depuis pronotepy
            homework_list = self.client.homework(date_from, date_to)
            
            # Formater les devoirs
            formatted_homework = []
            for hw in homework_list:
                formatted_homework.append({
                    "id": hw.id if hasattr(hw, 'id') else None,
                    "subject": hw.subject.name if hw.subject else "Matière inconnue",
                    "description": hw.description if hw.description else "Pas de description",
                    "done": hw.done if hasattr(hw, 'done') else False,
                    "date": hw.date.isoformat() if hw.date else None,
                    "files": [
                        {
                            "name": f.name if hasattr(f, 'name') else "Fichier",
                            "url": f.url if hasattr(f, 'url') else None
                        }
                        for f in (hw.files if hasattr(hw, 'files') else [])
                    ]
                })
            
            logger.info(f"{len(formatted_homework)} devoirs récupérés")
            return formatted_homework
            
        except Exception as e:
            logger.error(f"Erreur récupération devoirs: {str(e)}")
            raise PronoteException(f"Impossible de récupérer les devoirs: {str(e)}")
    
    @retry_on_failure(max_attempts=3)
    async def get_timetable(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Récupère l'emploi du temps
        
        Args:
            date_from: Date de début (par défaut: lundi de cette semaine)
            date_to: Date de fin (par défaut: dimanche de cette semaine)
        
        Returns:
            Liste des cours
        """
        if not self.client or not self.client.logged_in:
            raise PronoteException("Pas de session active")
        
        try:
            # Dates par défaut (semaine courante)
            if not date_from:
                today = datetime.now()
                date_from = today - timedelta(days=today.weekday())
            if not date_to:
                date_to = date_from + timedelta(days=7)
            
            logger.info(f"Récupération emploi du temps du {date_from} au {date_to}")
            
            # Récupérer l'emploi du temps
            lessons = self.client.lessons(date_from, date_to)
            
            # Formater les cours
            formatted_lessons = []
            for lesson in lessons:
                formatted_lessons.append({
                    "id": lesson.id if hasattr(lesson, 'id') else None,
                    "subject": lesson.subject.name if lesson.subject else "Cours",
                    "teacher": lesson.teacher_name if hasattr(lesson, 'teacher_name') else None,
                    "classroom": lesson.classroom if hasattr(lesson, 'classroom') else None,
                    "start": lesson.start.isoformat() if lesson.start else None,
                    "end": lesson.end.isoformat() if lesson.end else None,
                    "status": lesson.status if hasattr(lesson, 'status') else None,
                    "canceled": lesson.canceled if hasattr(lesson, 'canceled') else False
                })
            
            logger.info(f"{len(formatted_lessons)} cours récupérés")
            return formatted_lessons
            
        except Exception as e:
            logger.error(f"Erreur récupération emploi du temps: {str(e)}")
            raise PronoteException(f"Impossible de récupérer l'emploi du temps: {str(e)}")
    
    @retry_on_failure(max_attempts=3)
    async def get_grades(self, period_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Récupère les notes
        
        Args:
            period_name: Nom de la période (ex: "Trimestre 1", None = toutes)
        
        Returns:
            Liste des notes
        """
        if not self.client or not self.client.logged_in:
            raise PronoteException("Pas de session active")
        
        try:
            logger.info("Récupération des notes")
            
            # Récupérer toutes les périodes
            periods = self.client.periods
            
            # Sélectionner la période
            if period_name:
                period = next(
                    (p for p in periods if p.name == period_name),
                    None
                )
                if not period:
                    raise PronoteException(f"Période '{period_name}' non trouvée")
                periods_to_fetch = [period]
            else:
                periods_to_fetch = periods
            
            # Récupérer les notes
            all_grades = []
            for period in periods_to_fetch:
                grades = period.grades if hasattr(period, 'grades') else []
                
                for grade in grades:
                    all_grades.append({
                        "subject": grade.subject.name if grade.subject else "Matière",
                        "grade": grade.grade if hasattr(grade, 'grade') else None,
                        "out_of": grade.out_of if hasattr(grade, 'out_of') else 20,
                        "date": grade.date.isoformat() if hasattr(grade, 'date') and grade.date else None,
                        "period": period.name,
                        "coefficient": grade.coefficient if hasattr(grade, 'coefficient') else 1,
                        "comment": grade.comment if hasattr(grade, 'comment') else None
                    })
            
            logger.info(f"{len(all_grades)} notes récupérées")
            return all_grades
            
        except Exception as e:
            logger.error(f"Erreur récupération notes: {str(e)}")
            raise PronoteException(f"Impossible de récupérer les notes: {str(e)}")
    
    def disconnect(self):
        """Ferme proprement la session Pronote"""
        if self.client:
            try:
                # pronotepy n'a pas de méthode close explicite
                self.client = None
                logger.info("Session Pronote fermée")
            except Exception as e:
                logger.warning(f"Erreur lors de la fermeture: {str(e)}")


# Liste des ENTs supportés pour l'interface
SUPPORTED_ENTS = [
    {"id": "ac_reunion", "name": "Académie de La Réunion"},
    {"id": "ac_orleans_tours", "name": "Académie Orléans-Tours"},
    {"id": "ac_rennes", "name": "Académie de Rennes"},
    {"id": "ac_reims", "name": "Académie de Reims"},
    {"id": "ac_montpellier", "name": "Académie de Montpellier"},
    {"id": "arsene76", "name": "Arsene76 (Seine-Maritime)"},
    {"id": "atrium_sud", "name": "Atrium Sud (PACA)"},
    {"id": "cas_kosmos", "name": "CAS Kosmos"},
    {"id": "eclat_bfc", "name": "Eclat-BFC (Bourgogne-Franche-Comté)"},
    {"id": "ent27", "name": "ENT27 (Eure)"},
    {"id": "ent77", "name": "ENT77 (Seine-et-Marne)"},
    {"id": "ent_94", "name": "ENT94 (Val-de-Marne)"},
    {"id": "ent_creuse", "name": "ENT Creuse"},
    {"id": "ent_elyco", "name": "e-lyco (Pays de la Loire)"},
    {"id": "ent_essonne", "name": "ENT Essonne"},
    {"id": "ent_hdf", "name": "ENT Hauts-de-France"},
    {"id": "ent_somme", "name": "ENT Somme"},
    {"id": "ent_var", "name": "ENT Var"},
    {"id": "l_normandie", "name": "L'Educ de Normandie"},
    {"id": "laclasse_lyon", "name": "Laclasse.com (Lyon)"},
    {"id": "lyceeconnecte_aquitaine", "name": "Lycée Connecté (Nouvelle-Aquitaine)"},
    {"id": "lyceeconnecte_edu", "name": "Lycée Connecté"},
    {"id": "mon_bureau_numerique", "name": "Mon Bureau Numérique (Grand Est)"},
    {"id": "monlycee_net", "name": "Mon lycée.net (Île-de-France)"},
    {"id": "neotech_occitanie", "name": "Néo (Occitanie)"},
    {"id": "paris_classe_numerique", "name": "Paris Classe Numérique"},
    {"id": "toutatice", "name": "Toutatice (Bretagne)"},
    {"id": "webcollege_cantal", "name": "Webcollège Cantal"}
]
