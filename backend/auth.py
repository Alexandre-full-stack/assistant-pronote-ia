"""
Système d'authentification et gestion des sessions
JWT + Redis pour stockage sécurisé des sessions Pronote
"""
import jwt
import secrets
import redis
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from passlib.context import CryptContext
from loguru import logger
from config import settings


# Contexte de chiffrement pour les mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SessionManager:
    """Gestion des sessions utilisateur avec Redis"""
    
    def __init__(self):
        self.redis_client = redis.Redis.from_url(
            settings.REDIS_URL,
            password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
            decode_responses=True
        )
        # Initialiser Fernet pour chiffrer les données sensibles
        self.cipher = Fernet(settings.ENCRYPTION_KEY.encode())
    
    def create_session(
        self,
        user_id: str,
        pronote_data: Dict[str, Any],
        expires_in: Optional[int] = None
    ) -> str:
        """
        Crée une nouvelle session
        
        Args:
            user_id: Identifiant unique de l'utilisateur
            pronote_data: Données Pronote à stocker (chiffrées)
            expires_in: Durée de vie en secondes (défaut: settings)
        
        Returns:
            Token de session
        """
        try:
            # Générer un token unique
            session_token = secrets.token_urlsafe(32)
            
            # Chiffrer les données sensibles
            encrypted_data = self._encrypt_data(pronote_data)
            
            # Préparer les données de session
            session_data = {
                "user_id": user_id,
                "pronote_data": encrypted_data,
                "created_at": datetime.utcnow().isoformat(),
                "last_activity": datetime.utcnow().isoformat()
            }
            
            # Stocker dans Redis
            expiration = expires_in or settings.SESSION_EXPIRATION_SECONDS
            self.redis_client.setex(
                f"session:{session_token}",
                expiration,
                json.dumps(session_data)
            )
            
            logger.info(f"Session créée pour {user_id}, expire dans {expiration}s")
            return session_token
            
        except Exception as e:
            logger.error(f"Erreur création session: {str(e)}")
            raise
    
    def get_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Récupère une session active
        
        Args:
            session_token: Token de session
        
        Returns:
            Données de session (avec données Pronote déchiffrées) ou None
        """
        try:
            session_key = f"session:{session_token}"
            session_data_str = self.redis_client.get(session_key)
            
            if not session_data_str:
                logger.warning(f"Session introuvable: {session_token[:10]}...")
                return None
            
            session_data = json.loads(session_data_str)
            
            # Déchiffrer les données Pronote
            session_data['pronote_data'] = self._decrypt_data(
                session_data['pronote_data']
            )
            
            # Mettre à jour l'activité
            session_data['last_activity'] = datetime.utcnow().isoformat()
            self.redis_client.setex(
                session_key,
                settings.SESSION_EXPIRATION_SECONDS,
                json.dumps({
                    **session_data,
                    'pronote_data': self._encrypt_data(session_data['pronote_data'])
                })
            )
            
            return session_data
            
        except Exception as e:
            logger.error(f"Erreur récupération session: {str(e)}")
            return None
    
    def update_session(self, session_token: str, new_data: Dict[str, Any]):
        """
        Met à jour les données d'une session
        
        Args:
            session_token: Token de session
            new_data: Nouvelles données à fusionner
        """
        try:
            session_data = self.get_session(session_token)
            if not session_data:
                raise ValueError("Session introuvable")
            
            # Fusionner les nouvelles données
            session_data['pronote_data'].update(new_data)
            
            # Re-chiffrer et stocker
            encrypted_data = self._encrypt_data(session_data['pronote_data'])
            session_data['pronote_data'] = encrypted_data
            session_data['last_activity'] = datetime.utcnow().isoformat()
            
            self.redis_client.setex(
                f"session:{session_token}",
                settings.SESSION_EXPIRATION_SECONDS,
                json.dumps(session_data)
            )
            
            logger.info(f"Session mise à jour: {session_token[:10]}...")
            
        except Exception as e:
            logger.error(f"Erreur mise à jour session: {str(e)}")
            raise
    
    def delete_session(self, session_token: str):
        """
        Supprime une session
        
        Args:
            session_token: Token de session
        """
        try:
            result = self.redis_client.delete(f"session:{session_token}")
            if result:
                logger.info(f"Session supprimée: {session_token[:10]}...")
            else:
                logger.warning(f"Session déjà supprimée: {session_token[:10]}...")
        except Exception as e:
            logger.error(f"Erreur suppression session: {str(e)}")
    
    def _encrypt_data(self, data: Dict[str, Any]) -> str:
        """Chiffre les données sensibles"""
        json_data = json.dumps(data)
        encrypted = self.cipher.encrypt(json_data.encode())
        return encrypted.decode()
    
    def _decrypt_data(self, encrypted_data: str) -> Dict[str, Any]:
        """Déchiffre les données sensibles"""
        decrypted = self.cipher.decrypt(encrypted_data.encode())
        return json.loads(decrypted.decode())


class JWTManager:
    """Gestion des tokens JWT"""
    
    @staticmethod
    def create_token(
        user_id: str,
        session_token: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Crée un JWT token
        
        Args:
            user_id: Identifiant utilisateur
            session_token: Token de session Redis
            additional_claims: Claims additionnels
        
        Returns:
            JWT token
        """
        try:
            now = datetime.utcnow()
            expiration = now + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
            
            payload = {
                "user_id": user_id,
                "session_token": session_token,
                "iat": now,
                "exp": expiration,
                "jti": secrets.token_urlsafe(16)  # JWT ID unique
            }
            
            if additional_claims:
                payload.update(additional_claims)
            
            token = jwt.encode(
                payload,
                settings.JWT_SECRET_KEY,
                algorithm=settings.JWT_ALGORITHM
            )
            
            logger.info(f"JWT créé pour {user_id}, expire à {expiration}")
            return token
            
        except Exception as e:
            logger.error(f"Erreur création JWT: {str(e)}")
            raise
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Vérifie et décode un JWT token
        
        Args:
            token: JWT token
        
        Returns:
            Payload décodé ou None si invalide
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT expiré")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"JWT invalide: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Erreur vérification JWT: {str(e)}")
            return None
    
    @staticmethod
    def refresh_token(old_token: str) -> Optional[str]:
        """
        Rafraîchit un JWT token
        
        Args:
            old_token: Ancien token
        
        Returns:
            Nouveau token ou None
        """
        try:
            payload = JWTManager.verify_token(old_token)
            if not payload:
                return None
            
            # Créer un nouveau token avec les mêmes données
            new_token = JWTManager.create_token(
                user_id=payload['user_id'],
                session_token=payload['session_token']
            )
            
            return new_token
            
        except Exception as e:
            logger.error(f"Erreur rafraîchissement JWT: {str(e)}")
            return None


class AuthenticationService:
    """Service d'authentification complet"""
    
    def __init__(self):
        self.session_manager = SessionManager()
        self.jwt_manager = JWTManager()
    
    def hash_password(self, password: str) -> str:
        """Hashe un mot de passe"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Vérifie un mot de passe"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_authenticated_session(
        self,
        user_id: str,
        pronote_session_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Crée une session complète avec JWT
        
        Args:
            user_id: Identifiant utilisateur
            pronote_session_data: Données de session Pronote
        
        Returns:
            Dict avec access_token et session_token
        """
        try:
            # Créer la session Redis
            session_token = self.session_manager.create_session(
                user_id=user_id,
                pronote_data=pronote_session_data
            )
            
            # Créer le JWT
            access_token = self.jwt_manager.create_token(
                user_id=user_id,
                session_token=session_token
            )
            
            return {
                "access_token": access_token,
                "session_token": session_token,
                "token_type": "bearer",
                "expires_in": settings.JWT_EXPIRATION_HOURS * 3600
            }
            
        except Exception as e:
            logger.error(f"Erreur création session authentifiée: {str(e)}")
            raise
    
    def validate_session(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Valide un access token et retourne les données de session
        
        Args:
            access_token: JWT access token
        
        Returns:
            Données de session ou None
        """
        try:
            # Vérifier le JWT
            payload = self.jwt_manager.verify_token(access_token)
            if not payload:
                return None
            
            # Récupérer la session Redis
            session_data = self.session_manager.get_session(
                payload['session_token']
            )
            
            if not session_data:
                logger.warning("Session Redis introuvable pour JWT valide")
                return None
            
            return {
                **session_data,
                "user_id": payload['user_id'],
                "jwt_payload": payload
            }
            
        except Exception as e:
            logger.error(f"Erreur validation session: {str(e)}")
            return None
    
    def logout(self, access_token: str):
        """
        Déconnecte un utilisateur
        
        Args:
            access_token: JWT access token
        """
        try:
            payload = self.jwt_manager.verify_token(access_token)
            if payload:
                self.session_manager.delete_session(payload['session_token'])
                logger.info(f"Déconnexion réussie pour {payload['user_id']}")
        except Exception as e:
            logger.error(f"Erreur déconnexion: {str(e)}")


# Instance globale
auth_service = AuthenticationService()
