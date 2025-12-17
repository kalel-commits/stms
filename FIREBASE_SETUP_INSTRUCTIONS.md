# Firebase Setup Instructions

## Getting Your Firebase Credentials

This project requires Firebase Firestore for database storage. You need to set up your own Firebase project.

### Steps:

1. **Go to Firebase Console**
   - Visit: https://console.firebase.google.com/
   - Sign in with your Google account

2. **Create a New Project**
   - Click "Add project"
   - Enter project name (e.g., "smart-traffic-management")
   - Follow the setup wizard

3. **Enable Firestore Database**
   - In Firebase Console, go to "Firestore Database"
   - Click "Create database"
   - Choose "Start in production mode" (you can change rules later)
   - Select a location for your database

4. **Generate Service Account Credentials**
   - Go to Project Settings (gear icon)
   - Click "Service accounts" tab
   - Click "Generate new private key"
   - Download the JSON file

5. **Add Credentials to Project**
   - Place the downloaded JSON file in the project root
   - Rename it if needed, or set `FIREBASE_CREDENTIALS_PATH` in `.env` file

### Environment Variable (Optional)

Create a `.env` file in project root:
```env
FIREBASE_CREDENTIALS_PATH=your-firebase-credentials-file.json
FIREBASE_PROJECT_ID=your-project-id
```

### Security Note

⚠️ **NEVER commit Firebase credentials to GitHub!**
- The `.gitignore` file already excludes Firebase credential files
- Keep your credentials file secure and local
- Share only the project code, not credentials

