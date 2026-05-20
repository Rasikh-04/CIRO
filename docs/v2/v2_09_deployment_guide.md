# CIRO v2 — Deployment Guide
## Google Cloud + Supabase, $5 Budget + Free Tiers

---

## 1. One-Time Setup

### Google Cloud Project
```bash
# Install gcloud CLI: https://cloud.google.com/sdk/docs/install
gcloud auth login
gcloud projects create ciro-production --name="CIRO Crisis System"
gcloud config set project ciro-production

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  pubsub.googleapis.com \
  cloudbuild.googleapis.com \
  cloudfunctions.googleapis.com \
  cloudscheduler.googleapis.com \
  texttospeech.googleapis.com \
  storage.googleapis.com \
  secretmanager.googleapis.com \
  aiplatform.googleapis.com \
  logging.googleapis.com

# Create service account
gcloud iam service-accounts create ciro-backend \
  --display-name="CIRO Backend Service"

# Grant permissions
gcloud projects add-iam-policy-binding ciro-production \
  --member="serviceAccount:ciro-backend@ciro-production.iam.gserviceaccount.com" \
  --role="roles/pubsub.publisher"
gcloud projects add-iam-policy-binding ciro-production \
  --member="serviceAccount:ciro-backend@ciro-production.iam.gserviceaccount.com" \
  --role="roles/pubsub.subscriber"
gcloud projects add-iam-policy-binding ciro-production \
  --member="serviceAccount:ciro-backend@ciro-production.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"
gcloud projects add-iam-policy-binding ciro-production \
  --member="serviceAccount:ciro-backend@ciro-production.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
gcloud projects add-iam-policy-binding ciro-production \
  --member="serviceAccount:ciro-backend@ciro-production.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Download key
gcloud iam service-accounts keys create service-account.json \
  --iam-account=ciro-backend@ciro-production.iam.gserviceaccount.com
```

### Supabase Setup
```bash
# Go to supabase.com → New Project → "ciro-production"
# Region: Southeast Asia (Singapore) — closest to Pakistan
# Copy: Project URL + anon key + service role key

# Install Supabase CLI
npm install -g supabase

# Run migrations
supabase db push --db-url "postgresql://postgres:[password]@[host]:5432/postgres"
# Paste the full schema from v2_06_backend_v2.md §3
```

### Cloud Storage Bucket
```bash
gsutil mb -p ciro-production -l asia-south1 gs://ciro-assets
gsutil iam ch allUsers:objectViewer gs://ciro-assets  # Public read for alert audio
```

### Pub/Sub Topics
```bash
for topic in signals-raw signals-processed crisis-detected crisis-major \
  ops-picture-ready dispatch-planned simulation-complete alert-broadcast \
  sitrep-generated track2-update crisis-resolved; do
  gcloud pubsub topics create $topic
done
```

### Store Secrets
```bash
# Store all secrets in Secret Manager (never in code or env files)
for secret in SUPABASE_URL SUPABASE_KEY SUPABASE_SERVICE_KEY \
  UNOSAT_API_KEY HEALTHSITES_API_KEY OPENROUTESERVICE_API_KEY \
  GOOGLE_MAPS_API_KEY GEMINI_API_KEY; do
  echo -n "Enter $secret: "
  read -s value
  echo "$value" | gcloud secrets create $secret --data-file=-
done
```

---

## 2. Backend Deployment

```bash
# Build and deploy
cd backend

gcloud builds submit \
  --tag gcr.io/ciro-production/ciro-backend \
  --timeout=10m

gcloud run deploy ciro-backend \
  --image gcr.io/ciro-production/ciro-backend \
  --platform managed \
  --region asia-south1 \
  --service-account ciro-backend@ciro-production.iam.gserviceaccount.com \
  --set-secrets="SUPABASE_URL=SUPABASE_URL:latest,SUPABASE_SERVICE_KEY=SUPABASE_SERVICE_KEY:latest,GOOGLE_MAPS_API_KEY=GOOGLE_MAPS_API_KEY:latest" \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=ciro-production,ENVIRONMENT=production" \
  --allow-unauthenticated \
  --min-instances=0 \
  --max-instances=5 \
  --memory=512Mi \
  --cpu=1

# Get the URL
BACKEND_URL=$(gcloud run services describe ciro-backend \
  --region asia-south1 --format="value(status.url)")
echo "Backend: $BACKEND_URL"

# Verify
curl $BACKEND_URL/health
```

---

## 3. Agent Deployment (Cloud Run Services)

Each agent deployed similarly. Template:

```bash
# Template for each agent
AGENT_NAME="agent-1-signal-ingest"
AGENT_DIR="agents/agent_1_signal_ingestion"

cd $AGENT_DIR

gcloud builds submit \
  --tag gcr.io/ciro-production/ciro-$AGENT_NAME \
  --timeout=15m

gcloud run deploy ciro-$AGENT_NAME \
  --image gcr.io/ciro-production/ciro-$AGENT_NAME \
  --platform managed \
  --region asia-south1 \
  --service-account ciro-backend@ciro-production.iam.gserviceaccount.com \
  --set-secrets="SUPABASE_SERVICE_KEY=SUPABASE_SERVICE_KEY:latest,..." \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=ciro-production,BACKEND_URL=$BACKEND_URL" \
  --no-allow-unauthenticated \  # Agents only reachable via Pub/Sub
  --min-instances=0 \           # Scale to zero when idle — saves cost
  --max-instances=3 \
  --memory=1Gi \                # More memory for NLP models
  --cpu=1
```

### Configure Pub/Sub Push Subscriptions

```bash
# For each agent, create a push subscription pointing to its Cloud Run service
AGENT_URL=$(gcloud run services describe ciro-agent-1-signal-ingest \
  --region asia-south1 --format="value(status.url)")

gcloud pubsub subscriptions create agent-1-sub \
  --topic=signals-processed \
  --push-endpoint="${AGENT_URL}/pubsub/push" \
  --push-auth-service-account=ciro-backend@ciro-production.iam.gserviceaccount.com \
  --ack-deadline=300 \
  --min-retry-delay=10s \
  --max-retry-delay=600s
```

Repeat for all agents with their respective topics.

---

## 4. Ingestion Services Deployment

### Weather Ingestor (Cloud Run Job + Scheduler)
```bash
cd ingestion/weather_ingestor

gcloud builds submit --tag gcr.io/ciro-production/ciro-weather-ingestor

gcloud run jobs create ciro-weather-ingestor \
  --image gcr.io/ciro-production/ciro-weather-ingestor \
  --region asia-south1 \
  --service-account ciro-backend@ciro-production.iam.gserviceaccount.com \
  --set-secrets="SUPABASE_SERVICE_KEY=SUPABASE_SERVICE_KEY:latest" \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=ciro-production" \
  --max-retries=3

gcloud scheduler jobs create http ciro-weather-schedule \
  --location asia-south1 \
  --schedule "*/15 * * * *" \
  --uri "https://asia-south1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/ciro-production/jobs/ciro-weather-ingestor:run" \
  --http-method POST \
  --oauth-service-account-email ciro-backend@ciro-production.iam.gserviceaccount.com
```

### Social Monitor (Continuous Service)
```bash
gcloud run deploy ciro-social-monitor \
  --image gcr.io/ciro-production/ciro-social-monitor \
  --region asia-south1 \
  --min-instances=1 \    # Always on for real-time monitoring
  --max-instances=1 \
  --memory=256Mi
```

---

## 5. Web Dashboard Deployment (Firebase)

```bash
cd web-dashboard

# Update .env.production
echo "VITE_BACKEND_URL=$BACKEND_URL" > .env.production

npm run build

# Install Firebase CLI
npm install -g firebase-tools
firebase login

# Initialize (first time only)
firebase init hosting
# → Select: Use existing project (ciro-production)
# → Public directory: dist
# → Single-page app: Yes
# → No GitHub Actions for now

firebase deploy --only hosting
# Dashboard URL: https://ciro-production.web.app
```

Update CORS in backend:
```python
# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ciro-production.web.app",
        "http://localhost:5173",  # dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 6. Mobile App (Expo EAS)

```bash
cd mobile-app

# Install EAS CLI
npm install -g eas-cli
eas login

# Configure
eas build:configure

# Update eas.json
cat > eas.json << 'EOF'
{
  "cli": { "version": ">= 5.9.1" },
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal"
    },
    "production": {
      "android": {
        "buildType": "apk"
      },
      "env": {
        "EXPO_PUBLIC_BACKEND_URL": "https://ciro-backend-xxx.a.run.app"
      }
    }
  }
}
EOF

# Update BACKEND_URL
echo "EXPO_PUBLIC_BACKEND_URL=$BACKEND_URL" >> .env.production

# Build APK (free tier: limited builds per month)
eas build --profile production --platform android --non-interactive

# Download APK from EAS dashboard or CLI output URL
# Distribute via link for testing
```

---

## 7. Budget Monitoring

Check monthly to stay within free tiers:

```bash
# Cloud Run: should be near $0
gcloud billing accounts describe BILLING_ACCOUNT_ID

# Check free tier usage
gcloud run services list --region=asia-south1

# Pub/Sub: check data usage
gcloud pubsub subscriptions list

# Cloud Storage: check bucket size
gsutil du -sh gs://ciro-assets

# Supabase: check in dashboard
# Free tier: 500MB database, 2GB bandwidth, 1GB storage
# Monitor at: app.supabase.com/project/[id]/settings/billing
```

**If approaching Supabase 500MB limit:**
```sql
-- Check table sizes
SELECT relname, pg_size_pretty(pg_total_relation_size(relid))
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;

-- Archive old resolved crises (older than 30 days) to Cloud Storage
-- Delete from Supabase after archiving
```

---

## 8. Quick Deployment Commands (After Initial Setup)

```bash
# Deploy everything after code changes
./scripts/deploy_all.sh

# Individual deploys
./scripts/deploy_backend.sh
./scripts/deploy_agents.sh
./scripts/deploy_dashboard.sh
```

```bash
# scripts/deploy_backend.sh
#!/bin/bash
set -e
echo "Deploying backend..."
cd backend
gcloud builds submit --tag gcr.io/ciro-production/ciro-backend --quiet
gcloud run deploy ciro-backend \
  --image gcr.io/ciro-production/ciro-backend \
  --region asia-south1 --quiet
echo "Backend deployed: $(gcloud run services describe ciro-backend --region asia-south1 --format='value(status.url)')"
```
