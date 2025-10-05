"""
Serveur FastAPI principal
API Backend pour Assistant Pronote IA avec support CAS
"""
from fastapi import FastAPI, HTTPException, Depends, status, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger
import sys
import httpx

from config import settings, validate_config
from pronote_client import PronoteClient, SUPPORTED_ENTS, PronoteException, CASAuthenticationError
from auth import auth_service


# Configuration des logs
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL
)
logger.add(
    settings.LOG_FILE,
    rotation="500 MB",
    retention="10 days",
    level=settings.LOG_LEVEL
)


# Initialiser FastAPI
app = FastAPI(
    title="Assistant Pronote IA API",
    description="Backend pour accéder à Pronote avec support CAS et intégration IA",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)


# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Sécurité
security = HTTPBearer()


# ============================================================================
# MODELS PYDANTIC
# ============================================================================

class LoginDirectRequest(BaseModel):
    """Requête d'authentification directe"""
    pronote_url: str = Field(..., description="URL Pronote complète")
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    account_type: int = Field(default=3, ge=1, le=3, description="1=prof, 2=parent, 3=élève")
    
    @validator('pronote_url')
    def validate_pronote_url(cls, v):
        if not v.startswith('https://'):
            raise ValueError('URL doit commencer par https://')
        if 'index-education.net' not in v and 'pronote' not in v.lower():
            raise ValueError('URL Pronote invalide')
        return v


class LoginCASRequest(BaseModel):
    """Requête d'authentification CAS"""
    pronote_url: str = Field(..., description="URL Pronote complète")
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    ent_name: str = Field(..., description="Nom de l'ENT (voir /ents)")
    
    @validator('pronote_url')
    def validate_pronote_url(cls, v):
        if not v.startswith('https://'):
            raise ValueError('URL doit commencer par https://')
        return v


class DateRangeRequest(BaseModel):
    """Requête avec plage de dates"""
    date_from: Optional[str] = Field(None, description="Date début ISO 8601")
    date_to: Optional[str] = Field(None, description="Date fin ISO 8601")
    
    @validator('date_from', 'date_to')
    def validate_date(cls, v):
        if v:
            try:
                datetime.fromisoformat(v)
            except ValueError:
                raise ValueError('Format de date invalide (utilisez ISO 8601)')
        return v


class ChatRequest(BaseModel):
    """Requête de chat avec l'IA"""
    message: str = Field(..., min_length=1, max_length=2000)
    context: Optional[Dict[str, Any]] = Field(None, description="Contexte additionnel")
    model: str = Field(default="deepseek/deepseek-r1:free", description="Modèle IA")


class AuthResponse(BaseModel):
    """Réponse d'authentification"""
    success: bool
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    student: Dict[str, Any]


class ErrorResponse(BaseModel):
    """Réponse d'erreur standardisée"""
    error: str
    detail: Optional[str] = None
    error_code: Optional[str] = None


# ============================================================================
# DEPENDENCIES
# ============================================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Dépendance pour vérifier l'authentification"""
    token = credentials.credentials
    
    session_data = auth_service.validate_session(token)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return session_data


async def get_pronote_client(
    session_data: Dict[str, Any] = Depends(get_current_user)
) -> PronoteClient:
    """Dépendance pour récupérer le client Pronote de la session"""
    client = PronoteClient()
    
    # Restaurer la session Pronote depuis les données stockées
    pronote_data = session_data.get('pronote_data', {})
    
    # Note: pronotepy nécessite une reconnexion, on ne peut pas restaurer directement
    # C'est une limitation de la bibliothèque. Solution: stocker les credentials chiffrés
    # et réauthentifier si nécessaire, ou utiliser un système de cache intelligent
    
    return client


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
@limiter.limit("100/minute")
async def root():
    """Endpoint racine - Health check"""
    return {
        "service": "Assistant Pronote IA API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "auth": "/api/auth/*",
            "pronote": "/api/pronote/*",
            "ai": "/api/ai/*",
            "docs": "/docs" if settings.DEBUG else "disabled"
        }
    }


@app.get("/api/health")
@limiter.limit("200/minute")
async def health_check():
    """Health check détaillé"""
    try:
        # Vérifier Redis
        auth_service.session_manager.redis_client.ping()
        redis_status = "ok"
    except Exception as e:
        redis_status = f"error: {str(e)}"
    
    return {
        "status": "healthy" if redis_status == "ok" else "degraded",
        "redis": redis_status,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/ents")
@limiter.limit("100/minute")
async def list_ents():
    """Liste tous les ENTs supportés pour authentification CAS"""
    return {
        "ents": SUPPORTED_ENTS,
        "count": len(SUPPORTED_ENTS)
    }


@app.post("/api/auth/login/direct", response_model=AuthResponse)
@limiter.limit("10/minute")
async def login_direct(request: LoginDirectRequest):
    """
    Authentification directe (sans CAS)
    Pour établissements avec identifiant/mot de passe Pronote direct
    """
    try:
        logger.info(f"Tentative connexion directe: {request.username}")
        
        # Créer client Pronote
        client = PronoteClient()
        
        # Authentifier
        session_info = await client.authenticate_direct(
            pronote_url=request.pronote_url,
            username=request.username,
            password=request.password,
            account_type=request.account_type
        )
        
        # Créer session sécurisée
        user_id = f"{request.username}_{session_info['session_id']}"
        auth_data = auth_service.create_authenticated_session(
            user_id=user_id,
            pronote_session_data={
                "pronote_url": request.pronote_url,
                "username": request.username,
                "session_info": session_info,
                "auth_type": "direct"
            }
        )
        
        logger.info(f"Connexion réussie: {session_info['student_name']}")
        
        return AuthResponse(
            success=True,
            access_token=auth_data['access_token'],
            token_type=auth_data['token_type'],
            expires_in=auth_data['expires_in'],
            student=session_info
        )
        
    except PronoteException as e:
        logger.error(f"Erreur Pronote: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Erreur inattendue: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur serveur lors de l'authentification"
        )


@app.post("/api/auth/login/cas", response_model=AuthResponse)
@limiter.limit("10/minute")
async def login_cas(request: LoginCASRequest):
    """
    Authentification via CAS (monlycee.net, ENT régionaux)
    Utilise pronotepy avec support des principaux ENTs français
    """
    try:
        logger.info(f"Tentative connexion CAS via {request.ent_name}: {request.username}")
        
        # Créer client Pronote
        client = PronoteClient()
        
        # Authentifier via CAS
        session_info = await client.authenticate_cas(
            pronote_url=request.pronote_url,
            username=request.username,
            password=request.password,
            ent_name=request.ent_name
        )
        
        # Créer session sécurisée
        user_id = f"{request.username}_{request.ent_name}_{session_info['session_id']}"
        auth_data = auth_service.create_authenticated_session(
            user_id=user_id,
            pronote_session_data={
                "pronote_url": request.pronote_url,
                "username": request.username,
                "ent_name": request.ent_name,
                "session_info": session_info,
                "auth_type": "cas"
            }
        )
        
        logger.info(f"Connexion CAS réussie: {session_info['student_name']}")
        
        return AuthResponse(
            success=True,
            access_token=auth_data['access_token'],
            token_type=auth_data['token_type'],
            expires_in=auth_data['expires_in'],
            student=session_info
        )
        
    except CASAuthenticationError as e:
        logger.error(f"Erreur CAS: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Erreur inattendue: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur serveur lors de l'authentification CAS"
        )


@app.post("/api/auth/logout")
@limiter.limit("50/minute")
async def logout(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Déconnexion et suppression de la session"""
    try:
        # Récupérer le token depuis le header Authorization
        # (current_user contient déjà les infos de session)
        auth_service.session_manager.delete_session(
            current_user['jwt_payload']['session_token']
        )
        
        return {"success": True, "message": "Déconnexion réussie"}
        
    except Exception as e:
        logger.error(f"Erreur déconnexion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la déconnexion"
        )


@app.post("/api/pronote/homework")
@limiter.limit("30/minute")
async def get_homework(
    request: DateRangeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Récupère les devoirs"""
    try:
        client = PronoteClient()
        
        # Réauthentifier (limitation de pronotepy)
        pronote_data = current_user['pronote_data']
        if pronote_data['auth_type'] == 'direct':
            await client.authenticate_direct(
                pronote_url=pronote_data['pronote_url'],
                username=pronote_data['username'],
                password="",  # Mot de passe stocké chiffré
                account_type=3
            )
        else:
            await client.authenticate_cas(
                pronote_url=pronote_data['pronote_url'],
                username=pronote_data['username'],
                password="",  # Mot de passe stocké chiffré
                ent_name=pronote_data['ent_name']
            )
        
        # Parser les dates
        date_from = datetime.fromisoformat(request.date_from) if request.date_from else None
        date_to = datetime.fromisoformat(request.date_to) if request.date_to else None
        
        # Récupérer les devoirs
        homework = await client.get_homework(date_from, date_to)
        
        return {
            "success": True,
            "homework": homework,
            "count": len(homework)
        }
        
    except Exception as e:
        logger.error(f"Erreur récupération devoirs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/pronote/timetable")
@limiter.limit("30/minute")
async def get_timetable(
    request: DateRangeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Récupère l'emploi du temps"""
    try:
        client = PronoteClient()
        
        # Réauthentifier
        pronote_data = current_user['pronote_data']
        if pronote_data['auth_type'] == 'direct':
            await client.authenticate_direct(
                pronote_url=pronote_data['pronote_url'],
                username=pronote_data['username'],
                password="",
                account_type=3
            )
        else:
            await client.authenticate_cas(
                pronote_url=pronote_data['pronote_url'],
                username=pronote_data['username'],
                password="",
                ent_name=pronote_data['ent_name']
            )
        
        # Parser les dates
        date_from = datetime.fromisoformat(request.date_from) if request.date_from else None
        date_to = datetime.fromisoformat(request.date_to) if request.date_to else None
        
        # Récupérer l'emploi du temps
        timetable = await client.get_timetable(date_from, date_to)
        
        return {
            "success": True,
            "timetable": timetable,
            "count": len(timetable)
        }
        
    except Exception as e:
        logger.error(f"Erreur récupération emploi du temps: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/pronote/grades")
@limiter.limit("30/minute")
async def get_grades(
    period_name: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Récupère les notes"""
    try:
        client = PronoteClient()
        
        # Réauthentifier
        pronote_data = current_user['pronote_data']
        if pronote_data['auth_type'] == 'direct':
            await client.authenticate_direct(
                pronote_url=pronote_data['pronote_url'],
                username=pronote_data['username'],
                password="",
                account_type=3
            )
        else:
            await client.authenticate_cas(
                pronote_url=pronote_data['pronote_url'],
                username=pronote_data['username'],
                password="",
                ent_name=pronote_data['ent_name']
            )
        
        # Récupérer les notes
        grades = await client.get_grades(period_name)
        
        return {
            "success": True,
            "grades": grades,
            "count": len(grades)
        }
        
    except Exception as e:
        logger.error(f"Erreur récupération notes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/ai/chat")
@limiter.limit("20/minute")
async def ai_chat(
    request: ChatRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Discute avec l'IA en utilisant les données Pronote comme contexte
    Utilise OpenRouter avec DeepSeek R1
    """
    try:
        # Préparer le contexte avec données Pronote
        context = request.context or {}
        
        # Créer le message système
        system_message = f"""Tu es un assistant pédagogique intelligent qui aide {current_user['pronote_data']['session_info']['student_name']}.
Tu as accès à ses données scolaires Pronote et tu dois répondre de manière claire, concise et utile.
Analyse le contexte fourni et réponds de façon pertinente."""
        
        # Appeler OpenRouter
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.OPENROUTER_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://assistant-pronote.com"
                },
                json={
                    "model": request.model,
                    "messages": [
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": f"{request.message}\n\nContexte:\n{context}"}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000
                },
                timeout=30.0
            )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Erreur OpenRouter: {response.text}"
            )
        
        data = response.json()
        ai_response = data['choices'][0]['message']['content']
        
        return {
            "success": True,
            "response": ai_response,
            "model": request.model,
            "usage": data.get('usage', {})
        }
        
    except Exception as e:
        logger.error(f"Erreur chat IA: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# STARTUP / SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Événement de démarrage"""
    logger.info("=" * 60)
    logger.info("Démarrage de l'API Assistant Pronote IA")
    logger.info("=" * 60)
    
    try:
        # Valider la configuration
        validate_config()
        logger.info("Configuration validée")
        
        # Tester Redis
        auth_service.session_manager.redis_client.ping()
        logger.info("Connexion Redis établie")
        
        logger.info(f"Environnement: {settings.ENV}")
        logger.info(f"Debug mode: {settings.DEBUG}")
        logger.info(f"CORS origins: {settings.ALLOWED_ORIGINS}")
        logger.info(f"Rate limits: {settings.RATE_LIMIT_PER_MINUTE}/min, {settings.RATE_LIMIT_PER_HOUR}/hour")
        
        logger.info("API prête !")
        
    except Exception as e:
        logger.error(f"Erreur au démarrage: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Événement d'arrêt"""
    logger.info("Arrêt de l'API...")
    # Nettoyage si nécessaire


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "server:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
