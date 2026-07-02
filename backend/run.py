"""서버 실행 진입점"""
import uvicorn
from app.config import get_settings

settings = get_settings()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=(settings.app_env == "development"),
        log_level="info",
    )
