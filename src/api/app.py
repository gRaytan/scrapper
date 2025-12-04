"""FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings

# Create FastAPI app
app = FastAPI(
    title="Career Scraper API",
    description="API for accessing scraped job positions",
    version="0.1.0",
    debug=settings.debug,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Career Scraper API",
        "version": "0.1.0",
        "status": "operational"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# Import and include routers
from src.api.routes import auth, scraper, users, jobs, companies, alerts

app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(scraper.router, prefix="/api/v1/scraper", tags=["scraper"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(companies.router, prefix="/api/v1/companies", tags=["companies"])
app.include_router(alerts.router, prefix="/api/v1", tags=["alerts"])

