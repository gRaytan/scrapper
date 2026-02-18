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
# In production, set CORS_ORIGINS env var to your frontend URLs
# e.g., CORS_ORIGINS=https://hiddenjobs.me,https://www.hiddenjobs.me
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
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
from src.api.routes import auth, scraper, users, jobs, companies, alerts, applications, saved_filters, interview_questions

app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(scraper.router, prefix="/api/v1/scraper", tags=["scraper"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(companies.router, prefix="/api/v1/companies", tags=["companies"])
app.include_router(alerts.router, prefix="/api/v1", tags=["alerts"])
app.include_router(applications.router, prefix="/api/v1/applications", tags=["applications"])
app.include_router(saved_filters.router, prefix="/api/v1/saved-filters", tags=["saved-filters"])
app.include_router(interview_questions.router, prefix="/api/v1", tags=["interview-questions"])
